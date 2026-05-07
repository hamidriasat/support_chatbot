from typing import List, Literal
from state.graph_state import AgentState


def route_to_agent(state: AgentState) -> List[str]:
    """
    Conditional edge: decides which specialized agent to call.
    
    Based on router's classification.
    """
    if len(state["messages"]) > 6:
        return ["summary_node"]


    decision = state["router_decision"]

    # Simple mapping
    routing_map = {
        "order": "order_manager",
        "product": "product_support",
        "general": "general",
        "error": "router"
    }

    next_node = [routing_map[d] for d in decision if d in routing_map]
    
    if not next_node:
        return ["general"]
    
    return next_node


def after_worker_route(state: AgentState) -> Literal["aggregator_node", "end"]:
    """
    Decides whether to aggregate or finish.
    """
    if len(state.get("router_decision", [])) > 1:
        return "aggregator_node"
    
    return "end"