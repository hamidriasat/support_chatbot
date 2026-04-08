from email import message
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from pydantic_models.graph_state import AgentState
from utils.config import settings
from utils.logger import setup_logger
from agents.prompts.prompt_loader import load_prompt

setup_logger()

logger = logging.getLogger(__name__)

def order_manager(state: AgentState) -> AgentState:

    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("ORDER_PROMPT")
    prompt = load_prompt(path)
    model_name = settings.get("LLM")

    if not all([groq_api_key, prompt, model_name]):
        logger.error("Configuration missing: Check GROQ_API_KEY and ROUTER_PROMPT and LLM")
        raise ValueError("Missing required configuration for Router node.")
    
    try:
        llm = ChatGroq(model=model_name, temperature=0.3, api_key=groq_api_key)
        messages = [SystemMessage(content=prompt)] + state["messages"]

        response = llm.invoke(messages)
        logger.info(f"Order Agent Response: {response}")

        return {"order_response": response.content}
    
    except Exception as e:
        logger.error(f"Router node failed: {e}")
        return {
            "order_response": "I encountered a technical error processing this request."
        }
