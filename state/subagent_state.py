from typing import Optional
from langgraph.graph.message import MessagesState


class SubAgentState(MessagesState):
    summary: Optional[str] = ""