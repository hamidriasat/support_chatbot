import logging
import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from state.graph_state import AgentState
from utils.config import settings
from utils.logger import setup_logger
from prompts.prompt_loader import load_prompt


setup_logger()
logger = logging.getLogger(__name__)


#frst node
def router(state: AgentState) -> AgentState:
    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("ROUTER_PROMPT")
    prompt = load_prompt(path)
    model_name = settings.get("LLM")

    if not groq_api_key:
        logger.error("Configuration error: Check GROQ_API_KEY")
        raise ValueError("GROQ_API_KEY is missing in for router node.")
    if not prompt:
        logger.error("Configuration error: Prompt is missing")
        raise ValueError("Missing configuration: Could not load prompt from ROUTER_PROMPT path.")
    if not model_name:
        logger.error("Configuration error: LLM model name is missing")
        raise ValueError("Missing configuration: LLM model name is not set.")

    try:
        llm = ChatGroq(model=model_name, temperature=0.2, api_key=groq_api_key)

        messages = [SystemMessage(content=prompt)] + state["messages"]
        response = llm.invoke(messages)
        logger.info(f"Router Agent Response: {response}")
        router_decisions = json.loads(response.content)
        return {"router_decision": router_decisions}

    except Exception as e:
        logger.error(f"Router node failed: {e}")
        return {
            "router_decision": ["error"]
        }