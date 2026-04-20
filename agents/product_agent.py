import logging
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage
from state.subagent_state import SubAgentState
from utils.config import settings
from utils.logger import setup_logger
from prompts.prompt_loader import load_prompt
from tools.product_tools import product_search_id, product_search_category,\
      product_search_brand, product_search_sub_category, prodcut_search_name,\
      prodcut_search_description


setup_logger()
logger = logging.getLogger(__name__)

PRODUCT_TOOLS = [product_search_id, product_search_category, product_search_brand, 
                 product_search_sub_category, prodcut_search_name, prodcut_search_description]
_LLM_WITH_TOOLS = None
_PRODUCT_PROMPT_CONTENT = None


def _initialize_llm():
    global _LLM_WITH_TOOLS, _PRODUCT_PROMPT_CONTENT
    
    if _LLM_WITH_TOOLS is not None and _PRODUCT_PROMPT_CONTENT is not None:
        return

    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("PRODUCT_PROMPT")
    model_name = settings.get("LLM")

    if not groq_api_key:
        logger.error("Configuration error: Check GROQ_API_KEY")
        raise ValueError("GROQ_API_KEY is missing for product node.")
    if not path:
        logger.error("Configuration error: Prompt path is missing")
        raise ValueError("Missing configuration: Could not load prompt from PRODUCT_PROMPT path.")
    if not model_name:
        logger.error("Configuration error: LLM model name is missing")
        raise ValueError("Missing configuration: LLM model name is not set.")

    _PRODUCT_PROMPT_CONTENT = load_prompt(path)
    
    if not _PRODUCT_PROMPT_CONTENT:
        logger.error("Configuration error: Prompt is missing")
        raise ValueError("Missing configuration: Could not load prompt content.")

    llm = ChatGroq(model=model_name, temperature=0.3, api_key=groq_api_key)
    _LLM_WITH_TOOLS = llm.bind_tools(PRODUCT_TOOLS)
    logger.info("ChatGroq LLM and Product Tools globally initialized.")


def product_node(state: SubAgentState):
    try:
        _initialize_llm()
        messages = [SystemMessage(content=_PRODUCT_PROMPT_CONTENT)] + state["messages"]

        response = _LLM_WITH_TOOLS.invoke(messages)
        logger.info(f"Product Agent Response: {response}")
        
        return {"messages": [response]}
    
    except Exception as e:
        logger.error(f"Prodcut node failed: {e}")
        return {"messages": [AIMessage(content = "I encountered a technical error processing this request.")]}


# tool condition
def prodcut_should_continue(state: SubAgentState) -> str:
    """Checks the tool_messages list to see if a tool needs to run."""
    
    if not state["messages"]:
        return "end"
    
    # Find the last AIMessage
    last_message = state["messages"][-1]
    if getattr(last_message, 'tool_calls', None):
            return "tools"
    
    return "end"


# prodcut agent sub-graph
def create_product_subgraph(checkpointer=None):
    """Create product agent subgraph with tool calling loop"""
    subgraph = StateGraph(SubAgentState)
    
    # Add nodes
    subgraph.add_node("agent", product_node)
    subgraph.add_node("tools", ToolNode(PRODUCT_TOOLS))
    
    # Entry point
    subgraph.add_edge(START,"agent")
    
    # Agent decides: call tools or finish
    subgraph.add_conditional_edges(
        "agent",
        prodcut_should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # After tools, always go back to agent
    subgraph.add_edge("tools", "agent")
    
    return subgraph.compile(checkpointer=checkpointer)