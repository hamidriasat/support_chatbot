import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage
from pydantic_models.graph_state import AgentState
from utils.config import settings
from agents.prompts.prompt_loader import load_prompt
from utils.logger import setup_logger

setup_logger()

logger = logging.getLogger(__name__)

def aggregator_node(state: AgentState)-> AgentState:
    
    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("AGGREGATOR_PROMPT")
    prompt_text = load_prompt(path)
    model_name = settings.get("LLM")

    if not groq_api_key:
        logger.error("Configuration error: Check GROQ_API_KEY")
        raise ValueError("GROQ_API_KEY is missing in for aggregator node.")
    if not prompt_text:
        logger.error("Configuration error: Prompt is missing")
        raise ValueError("Missing configuration: Could not load prompt from AGGREGATOR_PROMPT path.")
    if not model_name:
        logger.error("Configuration error: LLM model name is missing")
        raise ValueError("Missing configuration: LLM model name is not set.")
    
    responses = {
        "order": state.get("order_response", ""),
        "product": state.get("product_response", ""),
        "general": state.get("general_response", "")
    }
    # Filter out empty responses
    active_responses = {k: v for k, v in responses.items() if v}
    user_question = state["messages"][-1]

    formatted_responses = "\n".join([
        f"- {agent}_agent: \"{response}\"" 
        for agent, response in active_responses.items()
    ])

    if not formatted_responses:
        formatted_responses = "- No agent responses available"
    
    final_prompt = prompt_text.format(
        user_question=user_question,
        agent_responses=formatted_responses
    )

    llm = ChatGroq(model=model_name, temperature=0.2, api_key=groq_api_key)
    response = llm.invoke(final_prompt)
    logger.info(f"Aggregator Agent Response: {response}")

    return {"messages": [AIMessage(content = response.content)],
            "order_response": "",
            "product_response": "",
            "general_response": "",
            "router_decision": []
            }