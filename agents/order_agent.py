import logging
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage
from state.subagent_state import SubAgentState
from utils.config import settings
from utils.logger import setup_logger
from prompts.prompt_loader import load_prompt
from tools.order_tools import read_order, update_order, read_inventory

setup_logger()

logger = logging.getLogger(__name__)

READ_TOOLS = [read_order, read_inventory]
WRITE_TOOLS = [update_order]
ALL_TOOLS = READ_TOOLS + WRITE_TOOLS
_LLM_WITH_TOOLS = None
_ORDER_PROMPT_CONTENT = None


def _initialize_llm():
    global _LLM_WITH_TOOLS, _ORDER_PROMPT_CONTENT
    
    if _LLM_WITH_TOOLS is not None and _ORDER_PROMPT_CONTENT is not None:
        return

    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("ORDER_PROMPT")
    model_name = settings.get("LLM")

    if not groq_api_key:
        logger.error("Configuration error: Check GROQ_API_KEY")
        raise ValueError("GROQ_API_KEY is missing for order node.")
    if not path:
        logger.error("Configuration error: Prompt path is missing")
        raise ValueError("Missing configuration: Could not load prompt from ORDER_PROMPT path.")
    if not model_name:
        logger.error("Configuration error: LLM model name is missing")
        raise ValueError("Missing configuration: LLM model name is not set.")

    _ORDER_PROMPT_CONTENT = load_prompt(path)
    
    if not _ORDER_PROMPT_CONTENT:
        logger.error("Configuration error: Prompt is missing")
        raise ValueError("Missing configuration: Could not load prompt content.")

    llm = ChatGroq(model=model_name, temperature=0.3, api_key=groq_api_key)
    _LLM_WITH_TOOLS = llm.bind_tools(ALL_TOOLS)


def order_node(state: SubAgentState):
    try:
        _initialize_llm()
        messages = [SystemMessage(content=_ORDER_PROMPT_CONTENT)] + state["messages"]

        response = _LLM_WITH_TOOLS.invoke(messages)
        logger.info(f"Order Agent Response: {response}")

        if hasattr(response, "tool_calls") and response.tool_calls and not response.content:
            # Check if any of the tools being called are the 'update_order' tool
            update_calls = [tc for tc in response.tool_calls if tc["name"] == "update_order"]
            
            if update_calls:
                # Build a dynamic message based on the tool's arguments
                summaries = []
                for tc in update_calls:
                    # Extract the arguments your tool uses
                    order_id = tc["args"].get("order_id", "Unknown Order")
                    updates = tc["args"].get("updates", {})
                    change_list = [f"{key} to '{val}'" for key, val in updates.items()]

                    if change_list:
                        changes_str = ", ".join(change_list)
                        summaries.append(f"Order {order_id} ({changes_str})")
                
                if summaries:
                    # Assign the manual message directly to the response content
                    response.content = f"I am preparing to update your order: {', '.join(summaries)}. Do you approve?"
        return {"messages": [response]}
    
    except Exception as e:
        logger.error(f"Order node failed: {e}")
        return {"messages": [AIMessage(content = "I encountered a technical error processing this request.")]}


# tool condition
def order_should_continue(state: SubAgentState) -> str:
    """Checks the messages list to see if a tool needs to run."""
    
    if not state["messages"]:
        return "end"
    
    # Find the last AIMessage
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return "end"
    
    tool_names = {tc["name"] for tc in last_message.tool_calls}
    
    read_tool_names = {tool.name for tool in READ_TOOLS}
    write_tool_names = {tool.name for tool in WRITE_TOOLS}

    if tool_names & write_tool_names:  # Any overlap with write tools
        return "update_tools"
    elif tool_names & read_tool_names:
        return "read_tools"
    else:
        return "end"


# order agent sub-graph
def create_order_subgraph():
    """Create order agent subgraph with tool calling loop"""
    subgraph = StateGraph(SubAgentState)
    
    # Add nodes
    subgraph.add_node("agent", order_node)
    subgraph.add_node("read_tools", ToolNode(READ_TOOLS))
    subgraph.add_node("update_tools", ToolNode(WRITE_TOOLS))
    
    # Entry point
    subgraph.add_edge(START,"agent")
    
    # Agent decides: call tools or finish
    subgraph.add_conditional_edges(
        "agent",
        order_should_continue,
        {
            "update_tools": "update_tools",
            "read_tools":"read_tools",
            "end": END
        }
    )
    
    # After tools, always go back to agent
    subgraph.add_edge("read_tools", "agent")
    subgraph.add_edge("update_tools", "agent") 
    
    return subgraph.compile(interrupt_before=["update_tools"])
