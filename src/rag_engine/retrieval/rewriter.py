"""Query preprocessing: turn a user's message into a standalone retrieval query.

Every query is normalised (lowercased, conversational filler and trailing
punctuation removed). For chat, if the conversation has history and the message
needs it (it contains a pronoun, or is five words or fewer), a small LLM rewrites
it into a standalone query. That rewrite prompt includes recent turns and domain
keywords from the ingested docs, so product terms are kept verbatim. Resolve-by-code
calls pass no conversation id and skip the rewrite entirely.
"""

import re

from rag_engine.api.schemas import EffortSettings
from rag_engine.retrieval.interfaces import ChatStore, Generator, KeywordStore

# a pronoun means the message probably refers back to earlier turns
PRONOUN_RE = re.compile(
    r"\b(my|i|it|its|that|this|those|these|they|them|their|he|she|same)\b", re.IGNORECASE
)
# leading filler ("can you tell me about ...", "i want to know ...") that adds nothing to retrieval
CONVERSATIONAL_RE = re.compile(
    r"^(?:please\s+)?(?:can|could|would)\s+you\s+(?:tell|show|explain|help)\s+(?:me\s+)?(?:about\s+|what\s+|how\s+)?|"
    r"^(?:i\s+want\s+to\s+know|i'm\s+looking\s+for|search\s+for)\s+",
    re.IGNORECASE,
)
PUNCTUATION_RE = r"[?!.]+$"

# System part of the rewrite prompt; process_prompt appends the glossary, context
# and query sections it refers to.
QUERY_REWRITE_PROMPT = """
    <instruction>
    You are a deterministic Conversational Query Reformulator for a hybrid search engine.
    Your ONLY job is resolve pronouns and omitted context from conversation history(stored in <context>) into a standalone search query.
    The query that needs to be formulated is in <user-query>. Previous chat context is contained in <context>. Relevant keywords are
    contained in <domain-glossary>.
    </instruction>

    <rules>
    * DO NOT answer questions or generate hypothetical explanations.
    * DO NOT expand acronyms or replace proprietary terms using general internet knowledge.
    * Every term listed in the <domain-glossary> below is a proprietary system identifier. You MUST preserve exact spelling and casing if referenced.
    * If the user's latest query pivots to a new topic unrelated to the <context>, DO NOT INTEGRATE any past context into the rewrittten query.
    * <context> is structured as {"user": ... } for a user's query followed by {"assist": ... } for the assistant's response. Each entry is separated by a \n delimiter.
    * If a response was tried and worked, it will be indicated with [status: success]. If a response was tried and failed, it will be indicated with [status: failed].
    </rules>
"""  # noqa: E501 -- prompt text is sent to the model verbatim; re-wrapping would change it


class Query:
    """A query being preprocessed: its current text and the conversation it belongs to.

    context is the chat history as (message, feedback) pairs, oldest first; see
    ChatStore.context_search.
    """

    resolved_query: str = ""
    context: list[tuple[str, bool | None]]

    def __init__(self, query: str, context: list[tuple[str, bool | None]]):
        self.resolved_query = query
        self.context = context


class QueryPreprocessor:
    """Normalises queries, rewrites context-dependent chat messages, and records
    each finished turn in the chat store (store_context)."""

    def __init__(
        self,
        chat_db: ChatStore,
        keyword_db: KeywordStore,
        rewrite_model: Generator,
        keywd_k: int = 1,
    ):
        self._keywd_k = keywd_k  # top k keywords selected
        self._chat_db = chat_db
        self._keyword_db = keyword_db
        self._rewrite_model = rewrite_model

    async def _retrieve_context(self, conversation_id: str) -> list[tuple[str, bool | None]]:
        """The conversation's history from the chat store, oldest message first."""
        return await self._chat_db.context_search(conversation_id)

    def _normalize_query(self, text: str) -> str:
        """Lowercase, put on one line, and drop leading conversational filler and
        trailing punctuation. May return ""."""
        query = text.strip().lower().replace("\n", " ")
        query = CONVERSATIONAL_RE.sub("", query).strip()
        query = re.sub(PUNCTUATION_RE, "", query).strip()
        return query

    def _create_query(self, text: str, context: list[tuple[str, bool | None]]) -> Query:
        """Bundle the normalised text with its conversation history."""
        return Query(text, context)

    def _req_coref_rewrite(self, query: Query) -> bool:
        """Whether the query needs the LLM rewrite: there is history, and the query
        has a pronoun or is five words or fewer."""
        if not query.context:
            return False

        if PRONOUN_RE.search(query.resolved_query) or len(query.resolved_query.split()) <= 5:
            return True

        return False  # prefer not to process

    async def _collect_keywords(
        self, query: Query, context: list[tuple[str, bool | None]], effort_settings: EffortSettings
    ) -> str:
        """The <domain-glossary> section of the rewrite prompt: keywords matching the
        query and the conversation, so the model keeps domain terms, acronyms and
        labels verbatim. effort_settings is not used yet."""
        # Known issue: keyword_search returns None when nothing matches, and the
        # join below then raises TypeError; guard with `or []` when fixing.
        terms = [entry[0] for entry in context]
        terms.append(query.resolved_query)
        context_query = " ".join(terms)

        matched_kws = await self._keyword_db.keyword_search(
            query.resolved_query, top_k=self._keywd_k
        )
        context_kws = await self._keyword_db.keyword_search(context_query, top_k=self._keywd_k)

        glossary_str = f"{'|'.join(matched_kws)}|{'|'.join(context_kws)}"
        return f"<domain-glossary>{glossary_str}</domain-glossary>"

    def _process_context(self, context: list[tuple[str, bool | None]], prev_k: int) -> str:
        """The <context> section of the rewrite prompt: the last prev_k messages, one
        per line, labelled [user]/[assist] and tagged with the user's feedback.

        context holds (message, status) pairs; status is True (the reply worked),
        False (it didn't) or None (no feedback recorded). "" when there is no history.
        """
        if not context:
            return ""

        # assume the first message is from the user
        # context is assumed to be populated from oldest to latest in order
        # (0 is the first message, -1 is the latest)
        preserved_context = context[-prev_k:]
        lines = []
        start_with_user = len(context) % 2 == 0

        for i, (msg, status) in enumerate(preserved_context):
            role = "user" if (i % 2 == 0) == start_with_user else "assist"

            status_indicator = ""
            if status is True:
                status_indicator = " [status: success]"
            elif status is False:
                status_indicator = " [status: failed]"

            lines.append(f"[{role}]: {msg}{status_indicator}")
        formatted = "\n".join(lines)

        return f"<context>{formatted}</context>"

    def _format_query(self, query: Query) -> str:
        """The <user-query> section of the rewrite prompt."""
        return f"<user-query>{query.resolved_query}</user-query>"

    async def process_prompt(
        self, raw_query: str, conversation_id: str, effort: EffortSettings
    ) -> str:
        """The query to retrieve with: normalised, and rewritten with the
        conversation's context when it needs it. "" for an empty message."""
        if not effort.rewrite:
            return raw_query

        # normalize query, remove filler words/content
        norm_query = self._normalize_query(raw_query)
        if not norm_query:
            return ""

        # No conversation id means there is nothing to resolve pronouns against
        # (the resolve-by-code path). Skip context retrieval and the LLM rewrite
        # entirely: it would only add latency and risk turning a good standalone
        # query into a worse one.
        if not conversation_id:
            return norm_query

        # retrieve context
        prev_context = await self._retrieve_context(conversation_id)

        # introduce query class to manage query and context
        query = self._create_query(norm_query, prev_context)

        # Only pay for the LLM rewrite when there is context AND the query
        # actually needs coreference resolution (pronouns or a very short query).
        if not self._req_coref_rewrite(query):
            return norm_query

        # search DB for relevant keywords used in domain glossary
        keyword_str = await self._collect_keywords(query, prev_context, effort)

        # create the context string
        context_str = self._process_context(prev_context, effort.context_k)

        query_str = self._format_query(query)

        # The final query is structured as:
        # <instruction> \n <rules> \n <domain-glossary> \n <context> \n <user-query>
        formatted_query = f"{QUERY_REWRITE_PROMPT}\n{keyword_str}\n{context_str}\n{query_str}"

        rewritten_query = await self._rewrite_model.generate(
            prompt=formatted_query, tokens=effort.num_rewrite
        )

        # fall back to the normalized query if the model returns nothing usable
        return (rewritten_query or "").strip() or norm_query

    def store_context(
        self, conversation_id: str, query: str, response: str, alarm: str | None
    ) -> None:
        """Record a finished turn so later messages can refer back to it. Blocking
        (sync DB write): callers on the async path should run it in a thread."""
        self._chat_db.store_query_result(conversation_id, query, response, alarm)
