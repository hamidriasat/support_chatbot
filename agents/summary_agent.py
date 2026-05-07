import logging
from langchain_groq import ChatGroq
from langchain_core.messages import RemoveMessage
from state.graph_state import AgentState
from prompts.prompt_loader import load_prompt
from utils.config import settings
from utils.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)


LLM = None
_SUMMARY_PROMPT_CONTENT = None


def _initialize_llm():
    global LLM, _SUMMARY_PROMPT_CONTENT
    
    if LLM is not None and _SUMMARY_PROMPT_CONTENT is not None:
        return

    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("SUMMARY_PROMPT")
    model_name = settings.get("LLM")

    if not groq_api_key:
        logger.error("Configuration error: Check GROQ_API_KEY")
        raise ValueError("GROQ_API_KEY is missing for order node.")
    if not path:
        logger.error("Configuration error: Prompt path is missing")
        raise ValueError("Missing configuration: Could not load prompt from SUMMARY_PROMPT path.")
    if not model_name:
        logger.error("Configuration error: LLM model name is missing")
        raise ValueError("Missing configuration: LLM model name is not set.")

    _SUMMARY_PROMPT_CONTENT = load_prompt(path)
    
    if not _SUMMARY_PROMPT_CONTENT:
        logger.error("Configuration error: Prompt is missing")
        raise ValueError("Missing configuration: Could not load prompt content.")

    LLM = ChatGroq(model=model_name, temperature=0.3, api_key=groq_api_key)


def summary_node(state: AgentState):

    _initialize_llm()

    existing_summary = state.get("summary", "No summary yet.")
    messages_to_summarize = state["messages"][:-3]

    if not messages_to_summarize:
        return {}
    
    prompt = _SUMMARY_PROMPT_CONTENT.format(
        summary=existing_summary,
        messages=messages_to_summarize
    )

    response = LLM.invoke(prompt)

    #return only last 3 messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-3]]
    return {"summary": response.content, "messages": delete_messages }