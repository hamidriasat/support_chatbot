import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agents.router_agent import router
from state.graph_state import AgentState
from agents.general_agent import general_queries
from agents.order_management_agent import order_manager
from agents.product_agent import create_product_subgraph
from agents.aggregator_agent import aggregator_node
from graph.conditions import route_to_agent, after_worker_route
from utils.logger import setup_logger


setup_logger()
logger = logging.getLogger(__name__)

PRODUCT_AGENT = create_product_subgraph()

def build_workflow():

    workflow = StateGraph(AgentState)

    workflow.add_node("router", router)
    workflow.add_node("general", general_queries)
    workflow.add_node("order_manager", order_manager)
    workflow.add_node("product_support", PRODUCT_AGENT)
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
                "end": END
            }
        )
    workflow.add_edge("aggregator_node", END)

    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    #print(graph.get_graph().draw_mermaid())
    logger.info("Graph is compiled")
    return graph
