import re
from pydantic import BaseModel, Field

PRONOUN_RE = re.compile(r"\b(my|i|it|its|that|this|those|these|they|them|their|he|she|same)\b", re.IGNORECASE)
CONVERSATIONAL_RE = re.compile(
    r"^(?:please\s+)?(?:can|could|would)\s+you\s+(?:tell|show|explain|help)\s+(?:me\s+)?(?:about\s+|what\s+|how\s+)?|"
    r"^(?:i\s+want\s+to\s+know|i'm\s+looking\s+for|search\s+for)\s+", re.IGNORECASE )
PUNCTUATION_RE = r"[?!.]+$"

class Query:
    is_topic_pivot: bool = False
    resolved_query: str = ""
    lexical_tokens: list[str] = []
    context: list[str]

    def __init__(self, query: str, context: list[str]):
        self.resolved_query = query
        self.context = context

class QueryPreprocessor:

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

    def process_prompt(self, raw_query: str, prev_context: list[str]) -> str:
        norm_query = self._normalize_query(raw_query)

        # nothing valuable in the query, return 
        if not norm_query:
            return ""

        query = self._create_query(norm_query, prev_context)

        

        return ""
