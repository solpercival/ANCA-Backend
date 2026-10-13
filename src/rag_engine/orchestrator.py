"""Coordinates a single resolve/chat turn across the retrieval components.

resolve (alarm code -> guidance):
  1. look the code up in the alarm catalogue (404 if unknown)
  2. build a retrieval query from the alarm's title + message (or the caller's query)
  3. retrieve candidates, keep the first rerank_k, rerank to rerank_top_n. Retrieval is
     limited to the documentation sets the caller's tier may see (operator: Part
     Programmer's Reference only; auth/tiers.py allowed_doc_audiences). Each chunk
     that survives is widened to its whole section for the prompt (_section_context)
  4. prompt the LLM for a COVERAGE line, action steps (as many as the docs support)
     and (technician+) CAUSE quotes
  5. post-process the answer so only grounded content survives: drop catalogue
     echoes, generalise or drop steps stating a doc example's values (0x04,
     Drive_3), drop non-action filler and repeated steps (incl. checks that only
     restate an earlier step), settle coverage, keep causes only when they match a
     real sentence of the retrieved docs that isn't a worked example (the doc's
     wording is returned)
  6. record the turn (store_context) and return steps, causes, citations (top 3)
chat follows the same retrieve -> rerank -> generate path with a simpler prompt,
after the query preprocessor rewrites the message using the conversation history,
and with the same tier restriction on retrieval.

Every component sits behind an interface from retrieval/interfaces.py, so tests
inject fakes; get_orchestrator wires the real backends. Stage timings go to the
resolve_timing log line, Prometheus (api/metrics.py) and Langfuse when configured.
"""

import logging
import re
import time
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from langfuse import Langfuse

from rag_engine.api.errors import ModelUnavailable, RetrievalUnavailable, UnknownAlarmCode
from rag_engine.api.metrics import rag_resolve_total, rag_stage_seconds
from rag_engine.api.safety import is_safety_alarm
from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    DocCoverage,
    EffortSettings,
    ResolveRequest,
    ResolveResponse,
    get_effort_settings,
)
from rag_engine.auth.tiers import Tier, allowed_doc_audiences, can_view_likely_causes
from rag_engine.config import get_settings
from rag_engine.retrieval.doc_refs import doc_name, doc_path, section_title
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.interfaces import (
    Alarm,
    AlarmStore,
    Chunk,
    Generator,
    Reranker,
    SectionStore,
    Where,
)
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker
from rag_engine.retrieval.rewriter import QueryPreprocessor
from rag_engine.stores.alarms import PostgresAlarmStore
from rag_engine.stores.search import PostgresDBConnection

log = logging.getLogger("rag_engine.orchestrator")

_NOT_COVERED = "The documentation does not cover this alarm."
# Shown with the answer for safety-related alarms (api/safety.py), whatever the tier
# and whatever the docs say: the steps come from documentation, not from the machine.
_SAFETY_NOTE = "Verify the machine's actual state before acting on these steps."

# models sometimes number or bullet lines despite the prompt; strip that prefix
_STEP_PREFIX = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s*")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# "CAUSE: <verbatim sentence>" lines the model emits for technician+ tiers
_CAUSE_LINE = re.compile(r"^\W*cause\s*[:=-]\s*(.+?)\s*$", re.I)
# inline citation markers ([1], [1, 2], [2-3], or a literal [n]) never reach the
# response: sources are reported only through the structured citations list
_CITE_MARKER = re.compile(r"\s*\[(?:n|\d+(?:\s*[,–-]\s*\d+)*)\]", re.I)
_MAX_CAUSES = 3
_MAX_CITATIONS = 3  # top-ranked chunks reported as citations
# how close a quoted cause must be to a real context sentence (difflib ratio);
# tolerates a small model's punctuation/markup slips, not paraphrase
_CAUSE_MATCH_RATIO = 0.85
_MIN_PARTIAL_QUOTE = 30  # a shorter fragment is too weak to anchor a sentence
# a step this close to the catalogue's alarm text is an echo, not doc guidance
_ECHO_RATIO = 0.8
# Verbs an action step starts with. Deliberately broad: a real step missing from
# this list is dropped only when the answer also has other action steps.
_ACTION_VERBS = frozenset(
    """
    acknowledge activate add adjust align allow apply assign attach avoid back
    calibrate call change check choose clean clear close compare configure confirm
    connect consult contact coordinate copy correct create cycle deactivate decide
    decrease define
    delete detach determine disable disconnect document downgrade edit enable ensure
    enter examine execute find fix go identify increase insert inspect install
    interpret investigate jog keep limit load locate look lower make map mark measure
    modify monitor move note obtain open order perform place power power-cycle press
    program provide purchase raise read re-initialise re-initialize re-run reboot
    reconfigure reconnect record recover reduce refer reinitialise reinitialize
    reinstall release reload remove rename repair replace report request rerun reseat
    reset restart restore retry review run save select set specify split start stop
    switch synchronise synchronize test tighten transfer try turn type uninstall
    unmap update upgrade upload use validate verify wait write
""".split()
)

# Example-specific literals the docs use for illustration (one machine's values),
# which must never be presented as facts about the caller's machine. Deliberately
# narrow: plain numbers ("at least 3 control points"), config properties
# ("opcua.enable = false", "mcode.101.mode = 5") and bracketed UI names are untouched.
#
# Device names are the one kind that is left alone when the alarm's own message
# contains it (_has_example_literal): there it is the caller's device as the machine
# reported it. Hex values get no such pass: a step that repeats the alarm's 0x04 goes
# on to say what it means ("If the error register shows 0x04, check for frame
# response errors"), which the docs do not state.
_DEVICE_NAME_LITERALS = (
    re.compile(r"\b[a-z]+_\d+\b", re.I),  # numbered device names: Drive_3
    # quoted device names: "Drive 3" (no ASCII apostrophe, so possessives can't match)
    re.compile(r"[\"“‘][a-z][\w -]*\d[\"”’]", re.I),
)
_EXAMPLE_LITERALS = (
    # register / station hex: 0x04. Not CoE object addresses (index:subindex, e.g.
    # "error code (0x1001:00)"): those are fixed by the standard, the same on every drive
    re.compile(r"\b0x[0-9a-f]+\b(?!:[0-9a-f]{1,2}\b)", re.I),
    *_DEVICE_NAME_LITERALS,
    # numbered lists of devices: "devices 2, 4 and 5", "stations 1 and 3"
    re.compile(
        r"\b(?:devices|drives|stations|slaves|nodes|axes|joints)\s+\d+"
        r"(?:\s*,\s*\d+)*\s*,?\s+(?:and|or)\s+\d+\b",
        re.I,
    ),
)
# parts of a step that can be cut to generalise it when they hold an example literal:
# a parenthetical, or a trailing "e.g. / for example / such as ..." clause
_EXAMPLE_ASIDE = re.compile(r"\s*\([^()]*\)")
_EXAMPLE_CLAUSE = re.compile(
    r",?\s*\b(?:e\.g\.|for example|for instance|such as)\s+[^.;,()]*", re.I
)
# Two steps are repeats when their content words are the same set, or mostly
# coincide: shared / smaller set >= _DUPLICATE_OVERLAP, for sets of at least
# _DUPLICATE_MIN_WORDS words. Word sets, not a character ratio: "Check the drive's
# error register" and "... status register" are ~0.9 alike by difflib yet distinct.
_DUPLICATE_OVERLAP = 0.8
_DUPLICATE_MIN_WORDS = 3
_STOPWORDS = frozenset(
    "a an and are as at be by for from if in into is it its of on or so that the "
    "then this to was when with you your".split()
)
# A check that restates an earlier step ("Set opcua.enable to false" -> "Verify
# opcua.enable is set to false in configuration") is also a repeat: the check's
# words, minus its verb and these generic ones, are mostly (_DUPLICATE_OVERLAP)
# found in the earlier step. Only checks are judged this way: two actions with the
# same object ("Enable the drive watchdog" / "Disable ...") are not repeats.
_CHECK_VERBS = frozenset("check confirm ensure validate verify".split())
_RESTATEMENT_FILLER = frozenset(
    "applied configuration configured correct correctly done file now properly "
    "property set setting still value".split()
)

# "If/When/Once/Unless <condition>, <main clause>" (or ":" after the condition);
# group 1 is the main clause, with a leading "then"/"just" skipped
_CONDITIONAL_STEP = re.compile(
    r"^\s*(?:if|when|once|unless)\b[^,:;]*[,:;]\s*(?:(?:then|just)\s+)?(.*)$", re.I
)

# first line of a resolve answer, e.g. "COVERAGE: partial"; tolerate markdown bold
_COVERAGE_LINE = re.compile(r"^\W*coverage\W*[:=-]\W*(full|partial|none)\b\W*$", re.I)
# confidence is kept for the interface contract; it mirrors doc_coverage as the
# starter-kit mock API does, rather than exposing an uncalibrated retrieval score
_COVERAGE_CONFIDENCE = {"full": 0.9, "partial": 0.5, "none": 0.0}


def _get_langfuse_client() -> Langfuse | None:
    """Instantiate Langfuse client if configured, else None."""
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def get_vector_store_backend() -> Any:
    """VectorStore for dense search; also serves as the KeywordStore for query rewriting."""
    return PostgresDBConnection()


def get_reranker_backend() -> Reranker:
    """Build the configured reranker backend; an unknown provider fails loudly."""
    provider = get_settings().rerank_provider.strip().lower()
    if provider == "none":
        return IdentityReranker()
    if provider == "qwen3":
        return Qwen3Reranker(max_length=get_settings().rerank_max_length)
    raise ValueError(f"Unknown RERANK_PROVIDER={provider!r}; expected 'none' or 'qwen3'")


def get_identity_reranker_backend() -> IdentityReranker:
    """The pass-through reranker, used when the effort level's reranker is "identity"
    whatever RERANK_PROVIDER says."""
    return IdentityReranker()


# Markdown structure stripped by _context_sentences, so causes are matched against
# (and returned as) plain prose sentences, never tables, code or headings.
_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^\s*#{1,6}(\s|$)")
_TABLE_ROW = re.compile(r"^\s*\|.*\||^\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
_LIST_MARKER = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+|^\s*(?:[-*+•]|\d+[.)])\s*$")
_ADMONITION = re.compile(r"^\s*(?:>\s*)+(?:\[![A-Z]+\]\s*)?")
_CODE_LIKE = re.compile(r"^\s*[{}\[\]<]|[{};]\s*$|\"\s*:\s*[\"{\[\d]")
_MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_MD_EMPHASIS = re.compile(r"(\*\*|__|\*|`)")
_HTML_TAG = re.compile(r"<[^>]+>")
_MIN_SENTENCE_WORDS = 4
# last line of defence before a cause is returned: never markdown/JSON structure
_STRUCTURAL = re.compile(r"```|~~~|^\s*#|^\s*[{}\[]|(?:\s\|\s.*){2}|^\s*\d+[.)]?\s*$")


def _clean_inline(text: str) -> str:
    """Strip inline markdown/HTML (links keep their text) and collapse whitespace."""
    text = _MD_LINK.sub(r"\1", text)
    text = _HTML_TAG.sub(" ", text)
    text = _MD_EMPHASIS.sub("", text).replace("\\_", "_")
    return " ".join(text.split())


@lru_cache(maxsize=512)
def _context_sentences(text: str) -> tuple[str, ...]:
    """Prose sentences of a markdown chunk, with its structure removed.

    Headings, table rows, fenced code/JSON and code-like lines are skipped and
    inline markup is stripped, so only readable doc text can be quoted back as
    a cause. Each list item and paragraph is split into sentences separately,
    so a heading or bullet never fuses with the prose after it.
    """
    paragraphs: list[list[str]] = []
    current: list[str] = []
    in_fence = False

    def flush():
        if current:
            paragraphs.append(current.copy())
            current.clear()

    for raw in (text or "").splitlines():
        if _FENCE.match(raw):
            in_fence = not in_fence
            flush()
            continue
        if in_fence or not raw.strip() or _HEADING.match(raw) or _TABLE_ROW.match(raw):
            flush()
            continue
        line = _ADMONITION.sub("", raw)
        if _LIST_MARKER.match(line):
            flush()
            line = _LIST_MARKER.sub("", line)
        if not line.strip() or _CODE_LIKE.search(line):
            flush()
            continue
        current.append(line)
    flush()

    sentences = []
    for para in paragraphs:
        for sentence in _SENTENCE_SPLIT.split(_clean_inline(" ".join(para))):
            words = [w for w in sentence.split() if any(ch.isalpha() for ch in w)]
            if len(words) >= _MIN_SENTENCE_WORDS:
                sentences.append(sentence.strip())
    return tuple(sentences)


def _log_candidates(candidates: list[Chunk]) -> None:
    """Log how many chunks retrieval returned, how many have no text, and the start
    of the first: a sanity check that retrieval returns usable text, not just ids."""
    empty = sum(1 for c in candidates if not (c.text or "").strip())
    preview = candidates[0].text[:120].replace("\n", " ") if candidates else ""
    log.info("retrieved count=%d empty_text=%d first=%r", len(candidates), empty, preview)


class Orchestrator:
    """One resolve or chat turn: retrieve, rerank, generate, then ground the answer."""

    def __init__(
        self,
        preprocessor: QueryPreprocessor,
        retriever: HybridRetriever,
        reranker: Reranker,
        generator: Generator,
        alarm_store: AlarmStore,
        langfuse_client: Langfuse | None = None,
        section_store: SectionStore | None = None,
    ):
        self._preprocessor = preprocessor
        self._retriever = retriever
        self._reranker = reranker
        self._id_reranker = get_identity_reranker_backend()
        self._generator = generator
        self._alarms = alarm_store
        self._langfuse = langfuse_client
        # None: the generator gets the selected chunks as they are
        self._sections = section_store

    async def _section_context(self, chunks: list[Chunk], code: str) -> list[Chunk]:
        """The chunks to show the generator: each selected chunk widened to its whole
        section, in rank order.

        Ingestion cuts a section into text, list, table and code pieces, so the steps
        of one procedure sit in several chunks ("run this:", the command, the warning
        after it) and the reranker keeps some and cuts others. A section replaces its
        chunk when it is at most CONTEXT_SECTION_MAX_CHARS and the context stays
        within CONTEXT_MAX_CHARS; otherwise the chunk is passed as it is. Later chunks
        of a section already included are dropped, their text being in it. Ranking,
        the relevance floor and citations keep using the original chunks.
        """
        settings = get_settings()
        if self._sections is None or settings.context_section_max_chars <= 0 or not chunks:
            return chunks
        try:
            sections = await self._sections.section_texts([c.chunk_id for c in chunks])
        except Exception:
            log.warning("section_lookup_failed code=%s (non-fatal)", code, exc_info=True)
            return chunks

        used = sum(len(c.text or "") for c in chunks)
        included: set[str] = set()
        context: list[Chunk] = []
        for i, chunk in enumerate(chunks):
            section_id, text = sections.get(chunk.chunk_id, (None, ""))
            if section_id in included:
                continue
            # the section stands in for every remaining chunk that came from it
            members = [
                c for c in chunks[i:] if sections.get(c.chunk_id, (None, ""))[0] == section_id
            ]
            grown = used + len(text) - sum(len(c.text or "") for c in members)
            if (
                section_id is None
                or len(text) > settings.context_section_max_chars
                or grown > settings.context_max_chars
            ):
                context.append(chunk)
                continue
            used = grown
            included.add(section_id)
            context.append(
                Chunk(
                    chunk_id=chunk.chunk_id,
                    text=text,
                    source=chunk.source,
                    metadata=chunk.metadata,
                    score=chunk.score,
                    section=chunk.section,
                )
            )
        log.info(
            "section_context code=%s chunks=%d sections=%d blocks=%d chars=%d",
            code,
            len(chunks),
            len(included),
            len(context),
            used,
        )
        return context

    @staticmethod
    def _tier_where(tier: Tier) -> Where:
        """The retrieval filter every request starts from: the documentation sets the
        tier may draw on (auth/tiers.py allowed_doc_audiences). Empty when unrestricted."""
        audiences = allowed_doc_audiences(tier)
        if audiences is None:
            return {}
        return {"doc_audiences": sorted(audiences)}

    @staticmethod
    def _format_context(chunks: list[Chunk]) -> str:
        """The prompt's context block: each chunk under its source path, separated by
        rules. No [n] labels: unlabelled context gives the model nothing to cite inline."""
        return "\n\n---\n\n".join(f"({c.source})\n{c.text}" for c in chunks)

    @staticmethod
    def _has_relevant_context(top: list[Chunk], reranker: Reranker, code: str) -> bool:
        """Whether the reranked chunks include anything about the alarm.

        False when the reranker scores relevance (Qwen3: chunk.score is P(yes)) and
        even its best chunk is below RESOLVE_MIN_RELEVANCE, or there are no chunks.
        That happens when the docs the caller may see don't cover the alarm, e.g. an
        operator asking about one documented only in the User Guide. With a reranker
        that doesn't score relevance (identity: low effort, RERANK_PROVIDER=none) the
        scores mean nothing here, so the context is always passed on.
        """
        floor = get_settings().resolve_min_relevance
        if floor <= 0 or not getattr(reranker, "scores_relevance", False):
            return True
        best = max((c.score for c in top), default=0.0)
        if best >= floor:
            return True
        log.info(
            "resolve_no_relevant_docs code=%s best_score=%.2f floor=%.2f chunks=%d",
            code,
            best,
            floor,
            len(top),
        )
        return False

    @staticmethod
    def _citations(chunks: list[Chunk]) -> list[Citation]:
        """The top chunks as contract citations {doc, path, section} (see
        retrieval/doc_refs.py): the first _MAX_CITATIONS chunks, with chunks of the
        same section merged, since they would be the same reference to a client."""
        citations: list[Citation] = []
        for chunk in chunks[:_MAX_CITATIONS]:
            path = doc_path(chunk.source)
            citation = Citation(
                doc=doc_name(path), path=path, section=section_title(chunk.section)
            )
            if citation not in citations:
                citations.append(citation)
        return citations

    @staticmethod
    def _strip_citations(text: str) -> str:
        """Remove any citation markers the model added despite being told not to."""
        return _CITE_MARKER.sub("", text).strip()

    @staticmethod
    def _retrieval_query(req: ResolveRequest, alarm: Alarm) -> str:
        """What to search the docs for: the caller's query if given, else the alarm's
        title and message. The code itself is opaque to the embedder, so retrieval
        runs on what the alarm means."""
        return req.query or f"{alarm.title}. {alarm.alarm_text}"

    def _build_prompt(
        self, req: ResolveRequest, alarm: Alarm, chunks: list[Chunk], tier: Tier
    ) -> str:
        """The generation prompt for a resolve call: instructions, the alarm header
        and the retrieved context.

        It asks for a COVERAGE line, then short action lines, then (for tiers that
        may see causes) CAUSE lines; resolve() parses the answer in that order.
        """
        # The docs describe machine behaviour, not per-alarm fixes, so the model is
        # asked for grounded guidance rather than a fix it would have to invent.
        # Output tokens dominate latency here (~16-33 tok/s on the demo GPU), so answers
        # are kept short. CAUSE lines only need to *locate* a sentence: the server
        # matches the opening words and returns the full doc sentence itself.
        causes = (
            "After those lines, add up to 3 lines of the form\n"
            "CAUSE: <the first 8 to 10 words of one context sentence, copied exactly>\n"
            "only where the context explicitly states a cause of this alarm. "
            "If it states none, add no CAUSE lines. Never write a cause in your own words.\n"
            if can_view_likely_causes(tier)
            else ""
        )
        return (
            "You are a CNC troubleshooting assistant.\n"
            "Using ONLY the context, tell the technician how to resolve this alarm. "
            "The documentation is descriptive and often will NOT contain explicit "
            "fix steps — never invent steps that aren't supported by the context; turn "
            "what it describes into an action instead.\n"
            "First line, exactly one of:\n"
            "COVERAGE: full    (the context gives explicit steps that resolve this alarm)\n"
            "COVERAGE: partial (the context explains the alarm or behaviour, but no complete fix)\n"
            "COVERAGE: none    (the context is unrelated to this alarm)\n"
            "Then output the steps, one line per point, no numbering. Give as many or as "
            "few steps as the context supports: there is no fixed number and no minimum, "
            "and one step is right when that is all the context gives. Each line is one "
            "short imperative sentence of at most 20 words, stated concisely in your own "
            "words. Start each line with a verb (for example Restart, Reinitialise, Set, "
            "Change, Add, Check or Verify). When the context makes a step depend on a "
            "condition, start with that condition instead, then the verb, in the form "
            '"If <condition from the context>, <verb> ...". Give each alternative the '
            "context offers as its own conditional step. Put first the step that "
            "resolves the alarm, written as the action itself (Set, Add, Disable, "
            "Restart, Reinitialise), not as a check that it was done; then the other "
            "steps in the order a technician would carry them out. Add a Check or Verify step only when "
            "the context says what to look for and what to do about it; never add one "
            "that checks whether another step was done, or that restates a step or a "
            "rule as a check. Never repeat a step in different words. Make sure no step "
            "would cause this alarm (for example by enabling a feature it reports as "
            "unlicensed). If the context says the alarm requires a restart or reinitialisation, "
            "that must be one of the lines. Never write a line that only describes the "
            "alarm or restates its message or error code. Fewer lines are better than "
            "filler: stop when the context has nothing more that applies.\n"
            "Ignore context about a different task or feature than this alarm, and never "
            "give advice that would cause this alarm again.\n"
            "Values in the context are examples from one machine and will not match this "
            "one. Never reproduce example-specific identifiers or values: device names "
            "(such as Drive_3), station or register hex values (such as 0x03 or 0x04), "
            "lists of device numbers (such as devices 2, 4 and 5), coordinates or example "
            "counts. Describe them generally instead: write \"Check the drive's reported "
            'error register", not "The error register is 0x04". Configuration property '
            "names, the values the documentation says to set, and limits it states as "
            "rules are not examples; keep those.\n"
            "Never copy code, program examples, coordinates, tables or long passages from "
            "the context. No citation markers or brackets, no introduction, no summary.\n"
            "For COVERAGE: none, the only following line must be exactly: "
            f'"{_NOT_COVERED}"\n'
            f"{causes}"
            "The alarm header below is what the machine reported, not documentation: "
            "use it to understand the alarm, and never repeat its description of the "
            "fault as guidance. If the alarm message itself states a remedy (it names a "
            "setting to change, or something to obtain or do), give that remedy as a "
            "step, in the direction the message says, and never give a step that "
            "contradicts it.\n"
            f"Tier: {tier.value}\nAlarm: {req.code} - {alarm.title}\n"
            f"Alarm message: {alarm.alarm_text}\n\n"
            f"Context:\n{self._format_context(chunks)}\n\n"
            # repeated after the context: a small model follows what it read last, and
            # the context may describe the opposite of the fix (how to enable a feature
            # the alarm says to disable)
            f"Reminder: the alarm to resolve is {req.code} - {alarm.title}. "
            f"Its message: {alarm.alarm_text}\n"
            "The steps must make this alarm go away. If the message states a remedy, "
            "your first step is that remedy, and no step may do the opposite."
        )

    @classmethod
    def _split_steps(cls, answer: str) -> list[str]:
        """The answer as a list of steps: one per non-empty line, with list numbering,
        bullets and citation markers removed."""
        steps = [cls._strip_citations(_STEP_PREFIX.sub("", ln)) for ln in answer.splitlines()]
        return [s for s in steps if s]

    @classmethod
    def _drop_catalogue_echoes(
        cls, steps: list[str], alarm: Alarm, chunks: list[Chunk]
    ) -> list[str]:
        """Remove steps that just restate the catalogue's alarm title/message.

        The catalogue identifies the alarm; it is not documentation, so repeating
        its text back must not pass as guidance. An echo is kept when the retrieved
        context says the same thing, i.e. the docs back it, or when it is an action:
        some alarm messages state their own remedy ("... disable the server with the
        opcua.enable configuration property"), and that part is guidance from the
        machine, unlike a restatement of the fault. Steps that merely mention the
        alarm while explaining it are not echoes.
        """
        header = [cls._norm(t) for t in (alarm.alarm_text, alarm.title) if t]
        kept = []
        for step in steps:
            s = cls._norm(step)
            is_echo = bool(s) and any(
                SequenceMatcher(None, s, h).ratio() >= _ECHO_RATIO
                or (len(s) >= _MIN_PARTIAL_QUOTE and s in h)
                for h in header
            )
            if (
                is_echo
                and not cls._starts_with_action(step)
                and cls._match_context_sentence(step, chunks) is None
            ):
                log.info("step_dropped_catalogue_echo code=%s step=%r", alarm.code, step[:120])
                continue
            kept.append(step)
        return kept

    @staticmethod
    def _starts_with_action(step: str) -> bool:
        """True if the step's first word is a known action verb (see _ACTION_VERBS), or
        it is a conditional action whose main clause starts with one: "If it's an
        error (non-zero code), recover by reinitialising the bus", "If PLC: configure
        ...". The reference answers branch like this, so such steps are not filler."""
        conditional = _CONDITIONAL_STEP.match(step)
        words = (conditional.group(1) if conditional else step).split()
        return bool(words) and words[0].strip(".,:;!\"'").lower() in _ACTION_VERBS

    @classmethod
    def _drop_filler_beside_actions(cls, steps: list[str], code: str) -> list[str]:
        """Drop non-action lines when the answer also gives action steps.

        The prompt asks for verb-led steps; lines like "Data-block mapping maps
        device 1 to devices 2, 4, and 5." that slip through next to real actions
        are filler copied from the context. An answer with no action line at all
        is a legitimate explanation-only answer (the docs give no fix) and is kept
        whole. The not-covered disclaimer is left for `_settle_coverage`.
        """
        disclaimer = cls._norm(_NOT_COVERED)
        if not any(cls._starts_with_action(s) for s in steps):
            return steps
        kept = []
        for step in steps:
            if cls._starts_with_action(step) or disclaimer in cls._norm(step):
                kept.append(step)
            else:
                log.info("step_dropped_non_action code=%s step=%r", code, step[:120])
        return kept

    @staticmethod
    def _has_example_literal(text: str, own: str = "") -> bool:
        """True if the text contains an example-specific literal (_EXAMPLE_LITERALS).

        A device name that also appears in `own` (the alarm's message) does not count:
        it is the caller's own device as the machine reported it, not a doc example.
        """
        own = own.casefold()
        for pattern in _EXAMPLE_LITERALS:
            for match in pattern.finditer(text):
                name = match.group(0).strip('"“”‘’').casefold()
                if pattern in _DEVICE_NAME_LITERALS and name in own:
                    continue
                return True
        return False

    @classmethod
    def _scrub_example_literals(
        cls, steps: list[str], code: str, alarm_text: str = ""
    ) -> list[str]:
        """Generalise or drop steps that state a doc example's value as fact.

        The docs illustrate with one machine's values (register 0x04, Drive_3,
        devices 2, 4 and 5); repeated as guidance they won't match the caller's
        machine. A step is generalised only by cutting the aside that holds the
        literal -- a parenthetical or a trailing "e.g. ..." clause -- so the rest of
        the sentence is untouched. If a literal is still there, the step is dropped:
        losing an example-bound step is safer than rewriting it into something wrong.

        A device name the alarm message itself reports (`alarm_text`) is left alone:
        "Run the upload for Drive_3" is what the alarm "device 'Drive_3' is running
        firmware 1.2.0" asks for, and treating Drive_3 as an example deleted every
        step of that answer. Other values from the message are still scrubbed.
        """

        def cut_aside(m: re.Match[str]) -> str:
            return "" if cls._has_example_literal(m.group(0), alarm_text) else m.group(0)

        kept = []
        for step in steps:
            if not cls._has_example_literal(step, alarm_text):
                kept.append(step)
                continue
            cut = step
            for aside in (_EXAMPLE_ASIDE, _EXAMPLE_CLAUSE):
                cut = aside.sub(cut_aside, cut)
            cut = re.sub(r"\s+([.,;:!?])", r"\1", " ".join(cut.split())).strip(" ,;:")
            if cut and not cls._has_example_literal(cut, alarm_text) and cls._norm(cut):
                log.info("step_generalised code=%s step=%r", code, step[:120])
                kept.append(cut)
            else:
                log.info("step_dropped_example_literal code=%s step=%r", code, step[:120])
        return kept

    @classmethod
    def _content_words(cls, text: str) -> set[str]:
        """The step's distinctive words for duplicate detection: normalised, no
        stopwords, a plural "s" removed so "point" and "points" coincide."""
        words = set()
        for w in cls._norm(text).split():
            if len(w) < 2 or w in _STOPWORDS:  # len: the "s" of a split "drive's"
                continue
            words.add(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w)
        return words

    @classmethod
    def _is_near_duplicate(cls, a: str, b: str) -> bool:
        """True if two steps say the same thing: the same content words, or (for
        steps with enough content) the smaller's words are almost all in the other."""
        wa, wb = cls._content_words(a), cls._content_words(b)
        if wa and wa == wb:
            return True
        smaller = min(len(wa), len(wb))
        return smaller >= _DUPLICATE_MIN_WORDS and len(wa & wb) / smaller >= _DUPLICATE_OVERLAP

    @classmethod
    def _restates_as_check(cls, check: str, earlier: str) -> bool:
        """True if `check` is a Check/Verify/... line that only re-states `earlier`
        (see _CHECK_VERBS): its object words are mostly in the earlier step."""
        words = check.split()
        if not words or words[0].strip(".,:;!\"'").lower() not in _CHECK_VERBS:
            return False
        claim = cls._content_words(" ".join(words[1:])) - _RESTATEMENT_FILLER
        if len(claim) < _DUPLICATE_MIN_WORDS:
            return False
        source = cls._content_words(earlier) - _RESTATEMENT_FILLER
        return len(claim & source) / len(claim) >= _DUPLICATE_OVERLAP

    @classmethod
    def _drop_duplicate_steps(cls, steps: list[str], code: str) -> list[str]:
        """Collapse repeated steps to their first occurrence.

        Small models pad a short answer by restating one instruction several ways
        (am.lic.0001: "Disable opcua.server with opcua.enable set to false", then
        "Verify opcua.enable is set to false in configuration", then "Check
        opcua.enable property is false in configuration file"). A later step is a
        repeat when it rewords an earlier one or only checks it. The first wording
        is kept, in place, so the step order is unchanged.
        """
        kept: list[str] = []
        for step in steps:
            if any(
                cls._is_near_duplicate(step, k) or cls._restates_as_check(step, k) for k in kept
            ):
                log.info("step_dropped_duplicate code=%s step=%r", code, step[:120])
                continue
            kept.append(step)
        return kept

    @classmethod
    def _support_stems(cls, text: str) -> set[str]:
        """Content words cut to 5 letters, so a step in the model's own words still
        meets the docs' wording ("restart" / "restarting")."""
        return {w[:5] for w in cls._content_words(text)}

    @classmethod
    def _drop_unsupported_steps(
        cls, steps: list[str], alarm: Alarm, chunks: list[Chunk], code: str
    ) -> list[str]:
        """Drop steps the context does not back up (STEP_SUPPORT_MIN; 0 disables).

        A step is unsupported when less than that share of its key words is found
        in what the model was shown: the context chunks and the alarm's title and
        message. Such steps are invented rather than reworded. The not-covered
        disclaimer is left for `_settle_coverage`.
        """
        floor = get_settings().step_support_min
        if floor <= 0:
            return steps
        shown = [alarm.title or "", alarm.alarm_text or "", *(c.context_text for c in chunks)]
        source = cls._support_stems(" ".join(shown))
        disclaimer = cls._norm(_NOT_COVERED)
        kept = []
        for step in steps:
            stems = cls._support_stems(step)
            support = len(stems & source) / len(stems) if stems else 1.0
            if support >= floor or disclaimer in cls._norm(step):
                kept.append(step)
            else:
                log.info(
                    "step_dropped_unsupported code=%s support=%.2f step=%r",
                    code,
                    support,
                    step[:120],
                )
        return kept

    @staticmethod
    def _split_coverage(answer: str, code: str) -> tuple[DocCoverage, str]:
        """Strip the leading COVERAGE line; return (claimed coverage, remaining answer).

        A missing or malformed header is treated as "partial" -- the answer may
        explain the alarm, but nothing confirmed a complete fix. The claim is only
        provisional; `_settle_coverage` reconciles it with what the steps say.
        """
        lines = answer.splitlines()
        first = next((i for i, ln in enumerate(lines) if ln.strip()), None)
        match = _COVERAGE_LINE.match(lines[first]) if first is not None else None
        if match:
            return match.group(1).lower(), "\n".join(lines[first + 1 :])
        log.warning("coverage_header_missing code=%s", code)
        return "partial", answer

    @classmethod
    def _settle_coverage(
        cls, claimed: DocCoverage, steps: list[str], code: str
    ) -> tuple[DocCoverage, list[str]]:
        """Make the grounding guard all-or-nothing.

        The "not covered" disclaimer is never mixed with guidance: it is either the
        whole answer (coverage "none") or it is dropped because the model did give
        real steps. In that second case the model contradicted itself, so coverage
        is capped at "partial" -- it can't claim a full fix it also disclaimed, and
        a "none" header is overruled by the steps it wrote anyway.
        """
        disclaimer = cls._norm(_NOT_COVERED)
        real = [s for s in steps if disclaimer not in cls._norm(s)]
        if not real:
            return "none", [_NOT_COVERED]
        if len(real) < len(steps) or claimed == "none":
            log.info(
                "coverage_contradiction code=%s claimed=%s steps=%d disclaimers=%d",
                code,
                claimed,
                len(real),
                len(steps) - len(real),
            )
            return "partial", real
        return claimed, real

    @classmethod
    def _split_causes(cls, body: str) -> tuple[list[str], str]:
        """Pull CAUSE lines out of the answer; return (claimed quotes, remaining body)."""
        claims: list[str] = []
        kept: list[str] = []
        for ln in body.splitlines():
            m = _CAUSE_LINE.match(ln)
            if not m:
                kept.append(ln)
                continue
            quote = cls._strip_citations(m.group(1)).strip("\"'").strip()
            if quote:
                claims.append(quote)
        return claims, "\n".join(kept)

    @staticmethod
    def _norm(text: str) -> str:
        """Lowercase, punctuation to spaces, single-spaced: for fuzzy text comparison."""
        return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())

    @classmethod
    def _ground_causes(cls, claims: list[str], chunks: list[Chunk], code: str) -> list[str]:
        """Keep only causes that are real sentences of the retrieved context.

        Each claimed quote is matched against every context sentence. The returned
        text is the documentation's own sentence, never the model's wording, so
        nothing synthesised survives.
        """
        causes: list[str] = []
        for quote in claims:
            if len(causes) == _MAX_CAUSES:
                break
            match = cls._match_context_sentence(quote, chunks)
            # a doc example ("maps index 0x6040 of device 1 to devices 2, 4, and 5")
            # is one machine's setup, not this alarm's cause
            if match is None or _STRUCTURAL.search(match) or cls._has_example_literal(match):
                log.info("cause_rejected code=%s quote=%r", code, quote[:120])
                continue
            if match not in causes:
                causes.append(match)
        return causes

    @classmethod
    def _match_context_sentence(cls, quote: str, chunks: list[Chunk]) -> str | None:
        """Return the (markup-free) context sentence `quote` reproduces, if any."""
        q = cls._norm(quote)
        best: tuple[float, str] | None = None
        for chunk in chunks:
            for sentence in _context_sentences(chunk.text or ""):
                s = cls._norm(sentence)
                if not s:
                    continue
                if len(q) >= _MIN_PARTIAL_QUOTE and q in s:
                    score = 1.0
                else:
                    score = SequenceMatcher(None, q, s).ratio()
                if best is None or score > best[0]:
                    best = (score, sentence.strip())
        if best is None or best[0] < _CAUSE_MATCH_RATIO:
            return None
        return best[1]

    def _build_chat_prompt(self, message: str, chunks: list[Chunk]) -> str:
        """Prompt for a short free-text answer from the context, or an exact refusal."""
        return (
            "You are a CNC troubleshooting assistant. Answer the user's question using only "
            "the context, in at most 3 short sentences. No citation markers or brackets, "
            "no preamble.\n"
            "If the answer is not in the context, reply exactly: "
            '"The documentation does not cover this."\n\n'
            f"Context:\n{self._format_context(chunks)}\n\nUser: {message}"
        )

    async def resolve(self, req: ResolveRequest, tier: Tier) -> ResolveResponse:
        """Guidance for one alarm code (pipeline in the module docstring).

        Raises UnknownAlarmCode for a code missing from the catalogue and
        RetrievalUnavailable when the catalogue or retrieval backend fails. The
        caller (api/routes.py) applies tier visibility rules to the result.
        """
        # retrieve request effort settings
        effort_settings: EffortSettings = get_effort_settings(req.effort)

        where = self._tier_where(tier)
        if req.env.versions:
            where["versions"] = req.env.versions
        if req.env.machine_variant:
            where["machine_variant"] = req.env.machine_variant
        try:
            alarm = await self._alarms.get_alarm(req.code)
        except Exception as exc:
            log.exception("alarm_lookup_error code=%s", req.code)
            rag_resolve_total.labels(outcome="error").inc()
            raise RetrievalUnavailable() from exc
        if alarm is None:
            rag_resolve_total.labels(outcome="unknown_code").inc()
            raise UnknownAlarmCode()
        query = self._retrieval_query(req, alarm)
        log.info("resolve_query code=%s query=%r", req.code, query[:200])

        trace = None
        if self._langfuse:
            trace = self._langfuse.trace(name="resolve", input={"code": req.code, "query": query})

        if effort_settings.rewrite:
            t0 = time.perf_counter()
            query = await self._preprocessor.process_prompt(query, "", effort_settings)
            t_rewrite = time.perf_counter() - t0
            rag_stage_seconds.labels(stage="rewrite").observe(t_rewrite)

        t0 = time.perf_counter()
        try:
            candidates = await self._retriever.retrieve(
                query, top_k=effort_settings.retrieval_k, where=where or None
            )
        except Exception as exc:
            log.exception("retrieval_error code=%s", req.code)
            rag_resolve_total.labels(outcome="error").inc()
            raise RetrievalUnavailable() from exc
        t_retrieve = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="retrieve").observe(t_retrieve)
        _log_candidates(candidates)

        if self._langfuse and trace:
            trace.span(
                name="retrieve",
                input={
                    "query": query,
                    "top_k": effort_settings.retrieval_k,
                    "where": where or None,
                },
                output={"candidates_count": len(candidates)},
                duration_ms=int(t_retrieve * 1000),
            )

        rerank_k = effort_settings.rerank_k
        trimmed = candidates[: effort_settings.context_k if rerank_k is None else rerank_k]

        t0 = time.perf_counter()
        reranker = self._id_reranker if effort_settings.reranker == "identity" else self._reranker
        top = await reranker.rerank(query, trimmed, effort=effort_settings)
        t_rerank = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="rerank").observe(t_rerank)

        if self._langfuse and trace:
            trace.span(
                name="rerank",
                input={"candidates_count": len(candidates), "top_n": effort_settings.reranker_n},
                output={"top_count": len(top)},
                duration_ms=int(t_rerank * 1000),
            )

        t_generate = 0.0
        # what the generator reads and what its answer is checked against; `top`
        # stays the ranking, used for the relevance floor and the citations
        context = top
        if self._has_relevant_context(top, reranker, req.code):
            context = await self._section_context(top, req.code)
            t0 = time.perf_counter()
            try:
                answer = await self._generator.generate(
                    prompt=self._build_prompt(req, alarm, context, tier),
                    tokens=effort_settings.num_predict,
                    thinking=effort_settings.thinking,
                )
            except Exception as exc:
                log.exception("generation_error code=%s", req.code)
                rag_resolve_total.labels(outcome="error").inc()
                raise ModelUnavailable() from exc
            t_generate = time.perf_counter() - t0
            rag_stage_seconds.labels(stage="generate").observe(t_generate)
        else:
            # nothing retrieved is about this alarm: say so rather than let the model
            # build steps out of unrelated text. Parsed like a generated answer below.
            answer = f"COVERAGE: none\n{_NOT_COVERED}"

        if self._langfuse and trace:
            trace.span(
                name="generate",
                input={"top_chunks": len(top), "tier": tier.value},
                output={"answer_length": len(answer)},
                duration_ms=int(t_generate * 1000),
            )

        try:
            self._preprocessor.store_context("", query, answer, req.code)
        except Exception:
            log.warning("store_context_failed code=%s (non-fatal)", req.code, exc_info=True)

        log.info(
            "resolve_timing code=%s retrieve=%.4fs rerank=%.4fs generate=%.4fs total=%.4fs",
            req.code,
            t_retrieve,
            t_rerank,
            t_generate,
            t_retrieve + t_rerank + t_generate,
        )

        if self._langfuse and trace:
            trace.update(
                output={
                    "code": req.code,
                    "citations_count": min(3, len(top)),
                    "total_latency_ms": int((t_retrieve + t_rerank + t_generate) * 1000),
                }
            )

        doc_coverage, body = self._split_coverage(answer, req.code)
        # always strip CAUSE lines so they never leak into steps, whatever the tier
        cause_claims, body = self._split_causes(body)
        steps = self._drop_catalogue_echoes(self._split_steps(body), alarm, context)
        steps = self._scrub_example_literals(steps, req.code, alarm.alarm_text)
        steps = self._drop_filler_beside_actions(steps, req.code)
        # after the scrub, which can leave two steps saying the same thing
        steps = self._drop_duplicate_steps(steps, req.code)
        steps = self._drop_unsupported_steps(steps, alarm, context, req.code)
        # empty (header only / only catalogue echoes) or only the disclaimer -> "none"
        doc_coverage, steps = self._settle_coverage(doc_coverage, steps, req.code)
        # the route also strips causes per tier; skipping here just avoids the work
        likely_causes = (
            self._ground_causes(cause_claims, context, req.code)
            if doc_coverage != "none" and can_view_likely_causes(tier)
            else []
        )
        log.info(
            "resolve_coverage code=%s doc_coverage=%s causes=%d/%d",
            req.code,
            doc_coverage,
            len(likely_causes),
            len(cause_claims),
        )

        rag_resolve_total.labels(outcome="ok").inc()
        return ResolveResponse(
            code=req.code,
            title=alarm.title,
            domain=alarm.domain,
            severity=alarm.severity_score,
            severity_category=alarm.severity_category.capitalize(),  # "error" -> "Error"
            steps=steps,
            likely_causes=likely_causes,
            # a "not covered" answer drew on nothing, so it cites nothing
            citations=self._citations(top) if doc_coverage != "none" else [],
            tier=tier,
            doc_coverage=doc_coverage,
            confidence=_COVERAGE_CONFIDENCE[doc_coverage],
            safety_note=_SAFETY_NOTE if is_safety_alarm(alarm.severity_category) else None,
        )

    async def chat(self, req: ChatRequest, tier: Tier) -> ChatResponse:
        """Answer a free-text message in the context of its conversation.

        The message is first rewritten into a standalone query (QueryPreprocessor).
        Note that req.message is replaced by that rewrite, so the rewritten text is
        what gets retrieved on and stored as the turn's query. An empty message
        returns an empty reply.
        """
        # retrieve request effort settings
        effort_settings: EffortSettings = get_effort_settings(req.effort)

        if effort_settings.rewrite:
            rewritten_prompt = await self._preprocessor.process_prompt(
                req.message, req.conversation_id, effort_settings
            )
            if not rewritten_prompt:
                return ChatResponse(conversation_id=req.conversation_id, reply="", citations=[])
            req.message = rewritten_prompt

        trace = None
        if self._langfuse:
            trace = self._langfuse.trace(
                name="chat", input={"conversation_id": req.conversation_id, "message": req.message}
            )

        where = self._tier_where(tier)

        t0 = time.perf_counter()
        try:
            candidates = await self._retriever.retrieve(
                req.message, top_k=effort_settings.retrieval_k, where=where or None
            )
        except Exception as exc:
            log.exception("retrieval_error conversation_id=%s", req.conversation_id)
            rag_resolve_total.labels(outcome="error").inc()
            raise RetrievalUnavailable() from exc
        t_retrieve = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="retrieve").observe(t_retrieve)
        _log_candidates(candidates)

        if self._langfuse and trace:
            trace.span(
                name="retrieve",
                input={
                    "query": req.message,
                    "top_k": effort_settings.retrieval_k,
                    "where": where or None,
                },
                output={"candidates_count": len(candidates)},
                duration_ms=int(t_retrieve * 1000),
            )

        trimmed = candidates[: effort_settings.context_k]

        t0 = time.perf_counter()
        if effort_settings.reranker == "identity":
            top = await self._id_reranker.rerank(req.message, trimmed, effort=effort_settings)
        else:
            top = await self._reranker.rerank(req.message, trimmed, effort=effort_settings)
        t_rerank = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="rerank").observe(t_rerank)

        if self._langfuse and trace:
            trace.span(
                name="rerank",
                input={"candidates_count": len(candidates), "top_n": effort_settings.reranker_n},
                output={"top_count": len(top)},
                duration_ms=int(t_rerank * 1000),
            )

        t0 = time.perf_counter()
        try:
            reply = await self._generator.generate(
                prompt=self._build_chat_prompt(req.message, top),
                tokens=effort_settings.num_predict,
                thinking=effort_settings.thinking,
            )
        except Exception as exc:
            log.exception("generation_error conversation_id=%s", req.conversation_id)
            rag_resolve_total.labels(outcome="error").inc()
            raise ModelUnavailable() from exc
        t_generate = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="generate").observe(t_generate)

        if self._langfuse and trace:
            trace.span(
                name="generate",
                input={"top_chunks": len(top)},
                output={"reply_length": len(reply)},
                duration_ms=int(t_generate * 1000),
            )

        self._preprocessor.store_context(req.conversation_id, req.message, reply, None)

        if self._langfuse and trace:
            trace.update(
                output={
                    "conversation_id": req.conversation_id,
                    "citations_count": min(3, len(top)),
                    "total_latency_ms": int((t_retrieve + t_rerank + t_generate) * 1000),
                }
            )

        rag_resolve_total.labels(outcome="ok").inc()
        return ChatResponse(
            conversation_id=req.conversation_id,
            reply=self._strip_citations(reply),
            citations=self._citations(top),
        )


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:  # pragma: no cover - wired at runtime
    """Build the production Orchestrator from settings (providers.py factories).

    Cached (lru_cache), so the routes' Depends(get_orchestrator) share one instance
    and the reranker model loads once per process. Imports are local to avoid an
    import cycle with main and to keep model-provider imports out of test runs.
    Note: HybridRetriever gets its default rrf_k (60), not settings.rrf_k, and the
    Orchestrator its default top_k/top_n (50/8), not RETRIEVAL_TOP_K/RERANK_TOP_N.
    """
    from rag_engine.main import app

    client = app.state.httpx_client

    from rag_engine.providers import (
        get_chat_store_backend,
        get_dense_embedding_backend,
        get_generation_backend,
        get_lexical_backend,
        get_rewrite_backend,
        get_sparse_embedding_backend,
    )

    dense_embedder = get_dense_embedding_backend(client=client)
    vector_store = get_vector_store_backend()
    if get_settings().embedding_setup == "dual":
        sparse_embedder = get_sparse_embedding_backend(client=client)
        lexical = get_lexical_backend()
    else:
        sparse_embedder = None
        lexical = None

    retriever = HybridRetriever(dense_embedder, sparse_embedder, vector_store, lexical)

    rewrite_model = get_rewrite_backend(client)
    chat_store = get_chat_store_backend()
    query_rewriter = QueryPreprocessor(
        chat_store, vector_store, rewrite_model, get_settings().KEYWORD_K
    )

    return Orchestrator(
        preprocessor=query_rewriter,
        retriever=retriever,
        reranker=get_reranker_backend(),
        generator=get_generation_backend(client=client),
        alarm_store=PostgresAlarmStore(),
        langfuse_client=_get_langfuse_client(),
        section_store=vector_store,
    )
