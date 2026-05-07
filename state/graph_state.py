from typing import List, Optional
from langgraph.graph.message import MessagesState


class AgentState(MessagesState):
    router_decision : List[str] = []
    summary: Optional[str] = ""

    order_response: Optional[str]= ""
    product_response: Optional[str]= ""
    general_response: Optional[str]= ""

    waiting_for_approval: bool = False