import logging
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage
from state.subagent_state import SubAgentState
from tools.general_tools import faq_tool
from utils.config import settings
from utils.logger import setup_logger
from prompts.prompt_loader import load_prompt


setup_logger()
logger = logging.getLogger(__name__)


GENERAL_TOOLS = [faq_tool]
_LLM_WITH_TOOLS = None
_GENERAL_PROMPT_CONTENT = None


def _initialize_llm():
    global _LLM_WITH_TOOLS, _GENERAL_PROMPT_CONTENT
    
    if _LLM_WITH_TOOLS is not None and _GENERAL_PROMPT_CONTENT is not None:
        return

    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("GENERAL_PROMPT")
    model_name = settings.get("LLM")

    if not groq_api_key:
        logger.error("Configuration error: Check GROQ_API_KEY")
        raise ValueError("GROQ_API_KEY is missing for general node.")
    if not path:
        logger.error("Configuration error: Prompt path is missing")
        raise ValueError("Missing configuration: Could not load prompt from GENERAL_PROMPT path.")
    if not model_name:
        logger.error("Configuration error: LLM model name is missing")
        raise ValueError("Missing configuration: LLM model name is not set.")

    _GENERAL_PROMPT_CONTENT = load_prompt(path)
    
    if not _GENERAL_PROMPT_CONTENT:
        logger.error("Configuration error: Prompt is missing")
        raise ValueError("Missing configuration: Could not load prompt content.")

    llm = ChatGroq(model=model_name, temperature=0.3, api_key=groq_api_key)
    _LLM_WITH_TOOLS = llm.bind_tools(GENERAL_TOOLS)


def general_node(state: SubAgentState):
    
    _initialize_llm()
    try:
        messages = [SystemMessage(content=_GENERAL_PROMPT_CONTENT)] + state["messages"]
        response = _LLM_WITH_TOOLS.invoke(messages)
        logger.info(f"General Agent Response: {response}")

        return {"messages": [response]}

    except Exception as e:
        logger.error(f"General node failed: {e}")
        return {"messages": [AIMessage(content = "I encountered a technical error processing this request.")]}


# tool condition
def general_should_continue(state: SubAgentState) -> str:
    """Checks the messages list to see if a tool needs to run."""
    
    if not state["messages"]:
        return "end"
    
    # Find the last AIMessage
    last_message = state["messages"][-1]
    if getattr(last_message, 'tool_calls', None):
            return "tools"
    
    return "end"


# order agent sub-graph
def create_general_subgraph(checkpointer=None):
    """Create general agent subgraph with tool calling loop"""
    subgraph = StateGraph(SubAgentState)
    
    # Add nodes
    subgraph.add_node("agent", general_node)
    subgraph.add_node("tools", ToolNode(GENERAL_TOOLS))
    
    # Entry point
    subgraph.add_edge(START,"agent")
    
    # Agent decides: call tools or finish
    subgraph.add_conditional_edges(
        "agent",
        general_should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # After tools, always go back to agent
    subgraph.add_edge("tools", "agent")
    
    return subgraph.compile(checkpointer=checkpointer)