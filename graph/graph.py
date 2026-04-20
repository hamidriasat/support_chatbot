import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from agents.router_agent import router
from state.graph_state import AgentState
from agents.general_agent import general_node
from agents.order_agent import create_order_subgraph
from agents.product_agent import create_product_subgraph
from agents.aggregator_agent import aggregator_node
from graph.conditions import route_to_agent, after_worker_route
from utils.logger import setup_logger


setup_logger()
logger = logging.getLogger(__name__)
MEMORY = MemorySaver()

PRODUCT_AGENT = create_product_subgraph(checkpointer=MEMORY)
ORDER_AGENT = create_order_subgraph(checkpointer=MEMORY)


# bridge node for product agent
def prodcut_node(state: AgentState, config: RunnableConfig):

    user_query = state["messages"][-1]
    initial_sub_state = {"messages": [user_query]}

    subgraph_config = config.copy()
    subgraph_config["configurable"] = {
        **config.get("configurable", {}),
        "checkpoint_ns": "product_subgraph" 
    }

    subgraph_response = PRODUCT_AGENT.invoke(initial_sub_state, config=subgraph_config)
    final_message = subgraph_response["messages"][-1]

    if len(state["router_decision"]) == 1:
        return {"messages": [final_message]}
    else:
        return {"product_response": final_message.content}


# bridge node for product agent
def order_node(state: AgentState, config: RunnableConfig):

    user_query = state["messages"][-1]
    initial_sub_state = {"messages": [user_query]}

    subgraph_config = config.copy()
    subgraph_config["configurable"] = {
        **config.get("configurable", {}),
        "checkpoint_ns": "order_subgraph"
    }
    subgraph_response = ORDER_AGENT.invoke(initial_sub_state, config=subgraph_config)
    final_message = subgraph_response["messages"][-1]

    if len(state["router_decision"]) == 1:
        return {"messages": [final_message]}
    else:
        return {"order_response": final_message.content}


# Main graph
def build_workflow():

    workflow = StateGraph(AgentState)

    workflow.add_node("router", router)
    workflow.add_node("general", general_node)
    workflow.add_node("order_manager", order_node)
    workflow.add_node("product_support", prodcut_node)
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

    graph = workflow.compile(checkpointer=MEMORY)
    #print(graph.get_graph().draw_mermaid())
    logger.info("Graph is compiled")
    return graph
