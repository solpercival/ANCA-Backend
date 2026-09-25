import re
from pydantic import BaseModel, Field

PRONOUN_RE = re.compile(r"\b(i|it|its|that|this|those|these|they|them|their|he|she|same)\b", re.IGNORECASE)

class Query:
    is_topic_pivot: bool = False
    resolved_query: str = ""
    lexical_tokens: list[str] = []
    context: dict[str,str]

    def __init__(self, query: str, context: dict[str,str]):
        self.resolved_query = query
        self.context = context

class QueryPreprocessor:
