from typing import List, Optional, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import MessagesState, add_messages


class AgentState(MessagesState):
    tool_messages: Annotated[list[AnyMessage], add_messages]
    router_decision : List[str] = []

    order_response: Optional[str]= ""
    product_response: Optional[str]= ""
    general_response: Optional[str]= ""

    waiting_user: bool = False
    human_response: str = ""