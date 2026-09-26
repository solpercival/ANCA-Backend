import re
import json
from rag_engine.config import get_settings
from rag_engine.retrieval.interfaces import KeywordStore, Generator

PRONOUN_RE = re.compile(r"\b(my|i|it|its|that|this|those|these|they|them|their|he|she|same)\b", re.IGNORECASE)
CONVERSATIONAL_RE = re.compile(
    r"^(?:please\s+)?(?:can|could|would)\s+you\s+(?:tell|show|explain|help)\s+(?:me\s+)?(?:about\s+|what\s+|how\s+)?|"
    r"^(?:i\s+want\s+to\s+know|i'm\s+looking\s+for|search\s+for)\s+", re.IGNORECASE )
PUNCTUATION_RE = r"[?!.]+$"

QUERY_REWRITE_PROMPT = """
    <instruction>
    You are a deterministic Conversational Query Reformulator for a hybrid search engine.
    Your ONLY job is to resolve pronouns and omitted context from conversation history(stored in <context>) into a standalone search query.
    The query that needs to be formulated is in the <user-query> tag. Previous chat context is provided in <context> tag. Relevant keywords are
    provided in the <domain-glossary> tag.
    </instruction>
    
    <rules>
    * DO NOT answer questions or generate hypothetical explanations.
    * DO NOT expand acronyms or replace proprietary terms using general internet knowledge.
    * Every term listed in the <domain-glossary> below is a proprietary system identifier. You MUST preserve exact spelling and casing if referenced.
    * If the user's latest query pivots to a new topic unrelated to the <context>, DO NOT INTEGRATE any past context into the rewrittten query.
    * <context> is structured as {"user": ... } for a user's query followed by {"assist": ... } for the assistant's response. Each entry is separated by a \n delimiter.
    * If a response was tried and worked, it will be indicated with [status: success]. If a response was tried and failed, it will be indicated with [status: failed].
    </rules>
"""

class Query:
    # Query class used to store all relevant data for query preprocessing
    resolved_query: str = ""
    context: list[tuple[str, bool | None]]

    def __init__(self, query: str, context: list[tuple[str, bool | None]]):
        self.resolved_query = query
        self.context = context

class QueryPreprocessor:
    def __init__(self, keyword_db: KeywordStore, rewrite_model: Generator, keywd_k: int, context_k: int):
        self._keywd_k = keywd_k # top k keywords selected
        self._context_k = context_k # recent k context used
        self._keyword_db = keyword_db
        self._rewrite_model = rewrite_model
        
    def _normalize_query(self, text: str) -> str:
        query = text.strip().lower().replace("\n", " ")
        query = CONVERSATIONAL_RE.sub("", query).strip()
        query = re.sub(PUNCTUATION_RE, "", query).strip()
        return query
        
    def _create_query(self, text: str, context: list[tuple[str, bool | None]]) -> Query:
        # creates Query class for storing context and query data
        return Query(text, context)

    def _req_coref_rewrite(self, query: Query) -> bool:
        # determines if there are any recognized pronouns that need resolution or if query is too short
        if not query.context:
            return False

        if PRONOUN_RE.search(query) or len(query.split()) <= 5:
            return True

        return False # prefer not to process

    def _collect_keywords(self, query: Query) -> str:
        # collects keywords from exact and fuzzy search to enforce preservation of domain specific terms/acronyms/labels
        settings = get_settings()

        matched_kws = self._keyword_db.keyword_search(query.resolved_query, top_k=self._keywd_k)

        return f"<domain-glossary>{"|".join(matched_kws)}</domain-glossary>"

    def _process_context(self, context: list[tuple[str, bool | None]], prev_k: int = 3) -> str:
        # context is expected in the format (context string, status). 
        # status can be True indicating success, False indicating failure or None indicating no recorded reaction

        # formats past context in order and amount requested
        if not context:
            return ""

        # assume the first message is from the user
        # context is assumed to be populated from oldest to latest in order (0 is the first message, -1 is the latest)
        preserved_context = context[-prev_k:]
        lines = []
        start_with_user = len(context) % 2 == 0
    
        for i, (msg, status) in enumerate(preserved_context):
            role = 'user' if (i % 2 == 0) == start_with_user else 'assist'

            status_indicator = ""
            if status is True:
                status_indicator = " [status: success]"
            elif status is False:
                status_indicator = " [status: failed]"
        
            lines.append(f"[{role}]: {msg}{status_indicator}")
        formatted = "\n".join(lines)

        return f"<context>{formatted}</context>"

    def _format_query(self, query: Query) -> str:
        return f"<user-query>{query.resolved_query}</user-query>"
    
    def process_prompt(self, raw_query: str, prev_context: list[tuple[str, bool | None]]) -> str:
        # normalize query, remove filler words/content
        norm_query = self._normalize_query(raw_query)
        if not norm_query:
            return ""

        # introduce query class to manage query and context
        query = self._create_query(norm_query, prev_context)

        # search DB for relevant keywords used in domain glossary
        keyword_str = self._collect_keywords(query)

        # create the context string
        context_str = self._process_context(prev_context, self._context_k)


        query_str = self._format_query(query)

        # The final query is structured as """<instruction> \n <rules> \n <domain-glossary> \n <context> \n <user-query>"""
        formatted_query = f"{QUERY_REWRITE_PROMPT}\n{keyword_str}\n{context_str}\n{query_str}"

        rewritten_query = self._rewrite_model.generate(formatted_query)
        
        return rewritten_query
