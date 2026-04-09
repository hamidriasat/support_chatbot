import logging
from typing import List, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agents.router_agent import router
from pydantic_models.graph_state import AgentState
from agents.sub_agents.general_agent import general_queries
from agents.sub_agents.order_management_agent import order_manager
from agents.sub_agents.product_agent import product_support
from agents.sub_agents.aggregator_agent import aggregator_node
from utils.logger import setup_logger


setup_logger()
logger = logging.getLogger(__name__)


def route_to_agent(state: AgentState) -> List[str]:
    """
    Conditional edge: decides which specialized agent to call.
    
    Based on router's classification.
    """
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

def after_worker_route(state: AgentState) -> Literal["aggregator_node", END]:
    """
    Decides whether to aggregate or finish.
    """
    if len(state.get("router_decision", [])) > 1:
        return "aggregator_node"
    
    return END

def build_workflow():

    workflow = StateGraph(AgentState)

    workflow.add_node("router", router)
    workflow.add_node("general", general_queries)
    workflow.add_node("order_manager", order_manager)
    workflow.add_node("product_support", product_support)
    workflow.add_node("aggregator_node", aggregator_node)

    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_to_agent, {
        "order_manager": "order_manager",
        "product_support": "product_support",
        "general": "general",
        "router": "router"
    })
    
    for worker in ["order_manager", "product_support", "general"]:
        workflow.add_conditional_edges(
            worker,
            after_worker_route,
            {
                "aggregator_node": "aggregator_node", 
                END: END
            }
        )
    workflow.add_edge("aggregator_node", END)

    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    #print(graph.get_graph().draw_mermaid())
    logger.info("Graph is compiled")
    return graph
