"""Coordinates a single resolve/chat turn across the retrieval components.

resolve (alarm code -> guidance):
  1. look the code up in the alarm catalogue (404 if unknown)
  2. build a retrieval query from the alarm's title + message (or the caller's query)
  3. retrieve candidates, keep the first 20, rerank to rerank_top_n
  4. prompt the LLM for a COVERAGE line, action steps and (technician+) CAUSE quotes
  5. post-process the answer so only grounded content survives: drop catalogue
     echoes and non-action filler, settle coverage, keep causes only when they
     match a real sentence of the retrieved docs (the doc's wording is returned)
  6. record the turn (store_context) and return steps, causes, citations (top 3)
chat follows the same retrieve -> rerank -> generate path with a simpler prompt,
after the query preprocessor rewrites the message using the conversation history.

Every component sits behind an interface from retrieval/interfaces.py, so tests
inject fakes; get_orchestrator wires the real backends. Stage timings go to the
resolve_timing log line, Prometheus (api/metrics.py) and Langfuse when configured.
"""
from functools import lru_cache
from difflib import SequenceMatcher
import logging
import re
import time
from typing import Any

from langfuse import Langfuse

from rag_engine.api.metrics import rag_stage_seconds, rag_resolve_total
from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    DocCoverage,
    ResolveRequest,
    ResolveResponse,
    EffortSettings,
    EffortLevel
)
from rag_engine.api.errors import ModelUnavailable, RetrievalUnavailable, UnknownAlarmCode
from rag_engine.auth.tiers import Tier, can_view_likely_causes
from rag_engine.config import get_settings
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.interfaces import Alarm, AlarmStore, Chunk, Generator, Reranker
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker
from rag_engine.stores.alarms import PostgresAlarmStore
from rag_engine.stores.search import PostgresDBConnection
from rag_engine.retrieval.rewriter import QueryPreprocessor

log = logging.getLogger("rag_engine.orchestrator")

_NOT_COVERED = "The documentation does not cover this alarm."

# models sometimes number or bullet lines despite the prompt; strip that prefix
_STEP_PREFIX = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s*")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# "CAUSE: <verbatim sentence>" lines the model emits for technician+ tiers
_CAUSE_LINE = re.compile(r"^\W*cause\s*[:=-]\s*(.+?)\s*$", re.I)
# inline citation markers ([1], [1, 2], [2-3], or a literal [n]) never reach the
# response: sources are reported only through the structured citations list
_CITE_MARKER = re.compile(r"\s*\[(?:n|\d+(?:\s*[,–-]\s*\d+)*)\]", re.I)
_MAX_CAUSES = 3
# how close a quoted cause must be to a real context sentence (difflib ratio);
# tolerates a small model's punctuation/markup slips, not paraphrase
_CAUSE_MATCH_RATIO = 0.85
_MIN_PARTIAL_QUOTE = 30  # a shorter fragment is too weak to anchor a sentence
# a step this close to the catalogue's alarm text is an echo, not doc guidance
_ECHO_RATIO = 0.8
# Verbs an action step starts with. Deliberately broad: a real step missing from
# this list is dropped only when the answer also has other action steps.
_ACTION_VERBS = frozenset("""
    acknowledge activate add adjust align allow apply assign attach avoid back
    calibrate call change check clean clear close compare configure confirm connect
    consult contact coordinate copy correct create cycle deactivate decrease define
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
""".split())

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
        return Qwen3Reranker(max_length=512)
    raise ValueError(f"Unknown RERANK_PROVIDER={provider!r}; expected 'none' or 'qwen3'")


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
    # sanity check that retrieval returns usable text, not just ids/sources
    empty = sum(1 for c in candidates if not (c.text or "").strip())
    preview = candidates[0].text[:120].replace("\n", " ") if candidates else ""
    log.info("retrieved count=%d empty_text=%d first=%r", len(candidates), empty, preview)


class Orchestrator:
    """One resolve or chat turn: retrieve, rerank, generate, then ground the answer.

    retrieval_top_k is candidates per search; rerank_top_n is how many reranked
    chunks go into the prompt (the first 3 are returned as citations).
    """

    def __init__(
        self,
        preprocessor: QueryPreprocessor,
        retriever: HybridRetriever,
        reranker: Reranker,
        generator: Generator,
        alarm_store: AlarmStore,
        rerank_top_n: int = 8,
        retrieval_top_k: int = 50,
        langfuse_client: Langfuse | None = None,
    ):
        self._preprocessor = preprocessor
        self._retriever = retriever
        self._reranker = reranker
        self._generator = generator
        self._alarms = alarm_store
        self._top_n = rerank_top_n
        self._top_k = retrieval_top_k
        self._langfuse = langfuse_client

    @staticmethod
    def _format_context(chunks: list[Chunk]) -> str:
        # no [n] labels: unlabelled context gives the model nothing to cite inline
        return "\n\n---\n\n".join(f"({c.source})\n{c.text}" for c in chunks)

    @staticmethod
    def _strip_citations(text: str) -> str:
        return _CITE_MARKER.sub("", text).strip()

    @staticmethod
    def _retrieval_query(req: ResolveRequest, alarm: Alarm) -> str:
        # the code itself is opaque to the embedder; retrieve on what the alarm means
        return req.query or f"{alarm.title}. {alarm.alarm_text}"

    def _build_prompt(
        self, req: ResolveRequest, alarm: Alarm, chunks: list[Chunk], tier: Tier
    ) -> str:
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
            "Then output one line per point, no numbering: at most 4 lines, each one short "
            "sentence of at most 20 words, stated concisely in your own words. "
            "Start each line with a verb. Put the action that resolves the alarm first "
            "(for example Restart, Reinitialise, Set, Change, Reconfigure, Add or Move), "
            "then at most two diagnostic lines (Check, Verify). If the context says the "
            "alarm requires a restart or reinitialisation, that must be one of the lines. "
            "Never write a line that only describes the alarm or restates its "
            "message or error code. Fewer lines are better than filler: stop when the "
            "context has nothing more that applies.\n"
            "Ignore context about a different task or feature than this alarm, and never "
            "give advice that would cause this alarm again.\n"
            "Never copy code, program examples, coordinates, tables or long passages from "
            "the context. No citation markers or brackets, no introduction, no summary.\n"
            "For COVERAGE: none, the only following line must be exactly: "
            f"\"{_NOT_COVERED}\"\n"
            f"{causes}"
            "The alarm header below is what the machine reported, not documentation: "
            "use it to understand the alarm, but never repeat it as guidance.\n"
            f"Tier: {tier.value}\nAlarm: {req.code} - {alarm.title}\n"
            f"Alarm message: {alarm.alarm_text}\n\n"
            f"Context:\n{self._format_context(chunks)}"
        )

    @classmethod
    def _split_steps(cls, answer: str) -> list[str]:
        steps = [cls._strip_citations(_STEP_PREFIX.sub("", ln)) for ln in answer.splitlines()]
        return [s for s in steps if s]

    @classmethod
    def _drop_catalogue_echoes(
        cls, steps: list[str], alarm: Alarm, chunks: list[Chunk]
    ) -> list[str]:
        """Remove steps that just restate the catalogue's alarm title/message.

        The catalogue identifies the alarm; it is not documentation, so repeating
        its text back must not pass as guidance. An echo is kept only when the
        retrieved context says the same thing, i.e. the docs back it. Steps that
        merely mention the alarm while explaining it are not echoes.
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
            if is_echo and cls._match_context_sentence(step, chunks) is None:
                log.info("step_dropped_catalogue_echo code=%s step=%r", alarm.code, step[:120])
                continue
            kept.append(step)
        return kept

    @staticmethod
    def _starts_with_action(step: str) -> bool:
        """True if the step's first word is a known action verb (see _ACTION_VERBS)."""
        words = step.split()
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
            return match.group(1).lower(), "\n".join(lines[first + 1:])
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
                code, claimed, len(real), len(steps) - len(real),
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
            if match is None or _STRUCTURAL.search(match):
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
            "\"The documentation does not cover this.\"\n\n"
            f"Context:\n{self._format_context(chunks)}\n\nUser: {message}"
        )

    async def resolve(self, req: ResolveRequest, tier: Tier) -> ResolveResponse:
        """Guidance for one alarm code (pipeline in the module docstring).

        Raises UnknownAlarmCode for a code missing from the catalogue and
        RetrievalUnavailable when the catalogue or retrieval backend fails. The
        caller (api/routes.py) applies tier visibility rules to the result.
        """
        # retrieve request effort settings
        effort_settings = EffortSettings()
        effort_settings = effort_settings.get_effort_settings(req.effort)
        
        where = {}
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

        t0 = time.perf_counter()
        query = await self._preprocessor.process_prompt(query, "", effort_settings)
        t_rewrite = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="rewrite").observe(t_rewrite)

        t0 = time.perf_counter()
        try:
            candidates = await self._retriever.retrieve(query, top_k=self._top_k, where=where or None)
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
                input={"query": query, "top_k": self._top_k, "where": where or None},
                output={"candidates_count": len(candidates)},
                duration_ms=int(t_retrieve * 1000),
            )

        trimmed = candidates[:20]

        t0 = time.perf_counter()
        top = await self._reranker.rerank(query, trimmed, effort=effort_settings)
        t_rerank = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="rerank").observe(t_rerank)

        if self._langfuse and trace:
            trace.span(
                name="rerank",
                input={"candidates_count": len(candidates), "top_n": self._top_n},
                output={"top_count": len(top)},
                duration_ms=int(t_rerank * 1000),
            )

        t0 = time.perf_counter()
        try:
            answer = await self._generator.generate(prompt=self._build_prompt(req, alarm, top, tier), 
                                                   tokens=effort_settings.num_predict, 
                                                   thinking=effort_settings.thinking)
        except Exception as exc:
            log.exception("generation_error code=%s", req.code)
            rag_resolve_total.labels(outcome="error").inc()
            raise ModelUnavailable() from exc
        t_generate = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="generate").observe(t_generate)

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
            req.code, t_retrieve, t_rerank, t_generate, t_retrieve + t_rerank + t_generate,
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
        steps = self._drop_catalogue_echoes(self._split_steps(body), alarm, top)
        steps = self._drop_filler_beside_actions(steps, req.code)
        # empty (header only / only catalogue echoes) or only the disclaimer -> "none"
        doc_coverage, steps = self._settle_coverage(doc_coverage, steps, req.code)
        # the route also strips causes per tier; skipping here just avoids the work
        likely_causes = (
            self._ground_causes(cause_claims, top, req.code)
            if doc_coverage != "none" and can_view_likely_causes(tier)
            else []
        )
        log.info(
            "resolve_coverage code=%s doc_coverage=%s causes=%d/%d",
            req.code, doc_coverage, len(likely_causes), len(cause_claims),
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
            citations=[Citation(source=c.source, chunk_id=c.chunk_id) for c in top[:3]],
            tier=tier,
            doc_coverage=doc_coverage,
            confidence=_COVERAGE_CONFIDENCE[doc_coverage],
        )

    async def chat(self, req: ChatRequest, tier: Tier) -> ChatResponse:
        """Answer a free-text message in the context of its conversation.

        The message is first rewritten into a standalone query (QueryPreprocessor).
        Note that req.message is replaced by that rewrite, so the rewritten text is
        what gets retrieved on and stored as the turn's query. An empty message
        returns an empty reply.
        """
        # retrieve request effort settings
        effort_settings: EffortSettings = EffortSettings()
        effort_settings = effort_settings.get_effort_settings(req.effort)

        rewritten_prompt = await self._preprocessor.process_prompt(req.message, req.conversation_id, effort_settings)
        if not rewritten_prompt:
            return ChatResponse(conversation_id=req.conversation_id, reply="", citations=[])
        req.message = rewritten_prompt

        trace = None
        if self._langfuse:
            trace = self._langfuse.trace(name="chat", input={"conversation_id": req.conversation_id, "message": req.message})

        t0 = time.perf_counter()
        try:
            candidates = await self._retriever.retrieve(req.message, top_k=self._top_k)
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
                input={"query": req.message, "top_k": self._top_k},
                output={"candidates_count": len(candidates)},
                duration_ms=int(t_retrieve * 1000),
            )

        trimmed = candidates[:20]

        t0 = time.perf_counter()
        top = await self._reranker.rerank(req.message, trimmed, effort=effort_settings)
        t_rerank = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="rerank").observe(t_rerank)

        if self._langfuse and trace:
            trace.span(
                name="rerank",
                input={"candidates_count": len(candidates), "top_n": self._top_n},
                output={"top_count": len(top)},
                duration_ms=int(t_rerank * 1000),
            )

        t0 = time.perf_counter()
        try:
            reply = await self._generator.generate(prompt=self._build_chat_prompt(req.message, top), 
                                                   tokens=effort_settings.num_predict, 
                                                   thinking=effort_settings.thinking)
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
            citations=[Citation(source=c.source, chunk_id=c.chunk_id) for c in top[:3]],
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
        get_dense_embedding_backend,
        get_generation_backend,
        get_lexical_backend,
        get_sparse_embedding_backend,
        get_rewrite_backend,
        get_chat_store_backend,
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
    query_rewriter = QueryPreprocessor(chat_store,
                                       vector_store, 
                                       rewrite_model, 
                                       get_settings().KEYWORD_K, 
                                       get_settings().CONTEXT_K)
    
    return Orchestrator(
        preprocessor=query_rewriter,
        retriever=retriever,
        reranker=get_reranker_backend(),
        generator=get_generation_backend(client=client),
        alarm_store=PostgresAlarmStore(),
        langfuse_client=_get_langfuse_client(),
    )