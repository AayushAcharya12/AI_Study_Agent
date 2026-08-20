from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, add_messages


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    docs: List[str]
    search_result: List[str]
    confidence: float