import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage
from pydantic_models.graph_state import AgentState
from utils.config import settings
from utils.logger import setup_logger
from agents.prompts.prompt_loader import load_prompt


setup_logger()
logger = logging.getLogger(__name__)



def general_queries(state: AgentState) -> AgentState:
    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("GENERAL_PROMPT")
    prompt = load_prompt(path)
    model_name = settings.get("LLM")

    if not groq_api_key:
        logger.error("Configuration error: Check GROQ_API_KEY")
        raise ValueError("GROQ_API_KEY is missing in for General node.")
    if not prompt:
        logger.error("Configuration error: Prompt is missing")
        raise ValueError("Missing configuration: Could not load prompt from GENERAL_PROMPT path.")
    if not model_name:
        logger.error("Configuration error: LLM model name is missing")
        raise ValueError("Missing configuration: LLM model name is not set.")

    try:
        llm = ChatGroq(model=model_name, temperature=0.2, api_key=groq_api_key)

        messages = [SystemMessage(content=prompt)] + state["messages"]
        response = llm.invoke(messages)
        logger.info(f"General Agent Response: {response}")

        if len(state["router_decision"]) == 1:
            return {"messages": [AIMessage(content = response.content)]}

        return {"general_response": response.content}

    except Exception as e:
        logger.error(f"Router node failed: {e}")
        
        if len(state["router_decision"]) == 1:
            return {"messages": [AIMessage(content = "I encountered a technical error processing this request.")]}

        return {
            "general_response": "I encountered a technical error processing this request."
        }