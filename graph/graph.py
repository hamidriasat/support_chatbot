import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from agents.router_agent import router
from state.graph_state import AgentState
from agents.general_agent import create_general_subgraph
from agents.order_agent import create_order_subgraph
from agents.product_agent import create_product_subgraph
from agents.aggregator_agent import aggregator_node
from graph.conditions import route_to_agent, after_worker_route
from utils.postgres_conn import connection
from utils.logger import setup_logger


setup_logger()
logger = logging.getLogger(__name__)
conn_pool = connection()
MEMORY = PostgresSaver(conn_pool)
PRODUCT_AGENT = create_product_subgraph()
ORDER_AGENT = create_order_subgraph()
GENERAL_AGENT = create_general_subgraph()


# ── Entry/exit mappers ──────────────────────────────────────────────

def enter_subgraph(state: AgentState) -> dict:
    """Pass users message into the subgraph."""
    return {"messages": state["messages"]}


def exit_order(state: dict) -> dict:
    # Can't read parent AgentState here — state is the child's output
    # So we return BOTH fields; whichever the parent state schema ignores is dropped
    final = state["messages"][-1]
    return {
        "messages": [final],
        "order_response": final.content
    }


def exit_product(state: dict) -> dict:
    final = state["messages"][-1]
    return {
        "messages": [final],
        "product_response": final.content
    }


def exit_general(state: dict) -> dict:
    final = state["messages"][-1]
    return {
        "messages": [final],
        "general_response": final.content
    }


# Main graph
def build_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("router", router)

    # ✅ Subgraphs added directly as nodes with entry/exit mappers
    workflow.add_node(
        "order_manager",
        enter_subgraph | ORDER_AGENT | exit_order
    )
    workflow.add_node(
        "product_support",
        enter_subgraph | PRODUCT_AGENT | exit_product
    )
    workflow.add_node(
        "general",
        enter_subgraph | GENERAL_AGENT | exit_general
    )

    workflow.add_node("aggregator_node", aggregator_node)

    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_to_agent, {
        "order_manager":   "order_manager",
        "product_support": "product_support",
        "general":         "general",
        "router":          "router"
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

    graph = workflow.compile(checkpointer=MEMORY)
    logger.info("Graph compiled")
    return graph
