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
    The query that needs to be formulated is in the <query> tag. Previous chat context is provided in <context> tag. Relevant keywords are
    provided in the <domain-glossary> tag.
    </instruction>
    
    <rules>
    * DO NOT answer questions or generate hypothetical explanations.
    * DO NOT expand acronyms or replace proprietary terms using general internet knowledge.
    * Every term listed in the <domain-glossary> below is a proprietary system identifier. You MUST preserve exact spelling and casing if referenced.
    * If the user's latest query pivots to a new topic unrelated to the <context>, DO NOT INTEGRATE any past context into the rewrittten query.
    * <context> is structured as {"user": ... } for a user's query followed by {"assist": ... } for the assistant's response. Each entry is separated by a \n delimiter.
    </rules>
"""

class Query:
    resolved_query: str = ""
    lexical_tokens: list[str] = []
    context: list[str]

    def __init__(self, query: str, context: list[str]):
        self.resolved_query = query
        self.context = context

class QueryPreprocessor:
    def __init__(self, keyword_db: KeywordStore, top_k: int, context_k: int, rewrite_model: Generator):
        self._top_k = top_k
        self._context_k = context_k
        self._keyword_db = keyword_db
        self._rewrite_model = rewrite_model
        
    def _normalize_query(self, text: str) -> str:
        query = text.strip().lower().replace("\n", " ")
        query = CONVERSATIONAL_RE.sub("", query).strip()
        query = re.sub(PUNCTUATION_RE, "", query).strip()
        return query
        
    def _create_query(self, text: str, context: list[str]) -> Query:
        return Query(text, context)

    def _req_coref_rewrite(self, query: Query) -> bool:
        if not query.context:
            return False

        if PRONOUN_RE.search(query) or len(query.split()) <= 5:
            return True

        return False # prefer not to process

    def _collect_keywords(self, query: Query) -> str:
        settings = get_settings()

        matched_kws = self._keyword_db.keyword_search(query.resolved_query, top_k=self._top_k)

        return f"<domain-glossary>{"|".join(matched_kws)}</domain-glossary>"

    def _process_context(self, context: list[str], prev_k: int = 3) -> str:
        if not context:
            return ""

        context_json: dict[str,str] = {}
        # assume the first message is from the user
        # context is assumed to be populated from oldest to latest in order (0 is the first message, -1 is the latest)
        preserved_context = context[-prev_k:]
        formatted = "\n".join(f"[{'user' if i % 2 == 0 else 'assist'}]: {msg}" for i, msg in enumerate(preserved_context))

        return f"<context>{formatted}</context>"

    def _format_query(self, query: Query) -> str:
        return f"<query>{query.resolved_query}</query>"
    
    def process_prompt(self, raw_query: str, prev_context: list[str]) -> str:
        # normalize query, remove filler words/content
        norm_query = self._normalize_query(raw_query)
        if not norm_query:
            return ""

        # introduce query class to manage query and context
        query = self._create_query(norm_query, prev_context)

        keyword_str = self._collect_keywords(query)

        context_str = self._process_context(prev_context)

        query_str = self._format_query(query)

        formatted_query = f"{QUERY_REWRITE_PROMPT}\n{keyword_str}\n{context_str}\n{query_str}"

        rewritten_query = self._rewrite_model.generate(formatted_query)
        
        return rewritten_query
