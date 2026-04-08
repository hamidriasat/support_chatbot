from typing import  Annotated, List
from langgraph.graph.message import MessagesState
import operator


class AgentState(MessagesState):
    router_decision : List[str] = []

    order_response: str
    product_response: str
    general_response: str

    waiting_user: bool = False
    human_response: str = ""