import logging
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage
from state.graph_state import AgentState
from utils.config import settings
from utils.logger import setup_logger
from prompts.prompt_loader import load_prompt
from tools.product_search import product_search_id, product_search_category,\
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


def product_support(state: AgentState) -> AgentState:
    try:
        _initialize_llm()
        messages = [SystemMessage(content=_PRODUCT_PROMPT_CONTENT)] + state["messages"] + state["tool_messages"]

        response = _LLM_WITH_TOOLS.invoke(messages)
        logger.info(f"Product Agent Response: {response}")

        if response.tool_calls:
            return {"tool_messages":[response]}

        if len(state["router_decision"]) == 1:
            return {"messages": [AIMessage(content = response.content)]}
        
        return {"product_response": response.content}
    
    except Exception as e:
        logger.error(f"Router node failed: {e}")
        
        if len(state["router_decision"]) == 1:
            return {"messages": [AIMessage(content = "I encountered a technical error processing this request.")]}
        
        return {
            "product_response": "I encountered a technical error processing this request."
        }


def should_continue(state: AgentState) -> str:
    """Checks the tool_messages list to see if a tool needs to run."""
    
    if not state["tool_messages"]:
        return "end"
    
    # Find the last AIMessage
    last_message = state["tool_messages"][-1]
    if getattr(last_message, 'tool_calls', None):
            return "tools"
    
    return "end"



def create_product_subgraph():
    """Create product agent subgraph with tool calling loop"""
    subgraph = StateGraph(AgentState)
    
    # Add nodes
    subgraph.add_node("agent", product_support)
    subgraph.add_node("tools", ToolNode(PRODUCT_TOOLS, messages_key="tool_messages"))
    
    # Entry point
    subgraph.add_edge(START,"agent")
    
    # Agent decides: call tools or finish
    subgraph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # After tools, always go back to agent
    subgraph.add_edge("tools", "agent")
    
    return subgraph.compile()