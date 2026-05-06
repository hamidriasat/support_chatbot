import logging
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage
from state.graph_state import AgentState
from utils.config import settings
from prompts.prompt_loader import load_prompt
from utils.logger import setup_logger

setup_logger()

logger = logging.getLogger(__name__)

LLM = None
_AGGREGATOR_PROMPT_CONTENT = None


def _initialize_llm():
    global LLM, _AGGREGATOR_PROMPT_CONTENT
    
    if LLM is not None and _AGGREGATOR_PROMPT_CONTENT is not None:
        return

    groq_api_key = settings.get("GROQ_API_KEY")
    path = settings.get("AGGREGATOR_PROMPT")
    model_name = settings.get("LLM")

    if not groq_api_key:
        logger.error("Configuration error: Check GROQ_API_KEY")
        raise ValueError("GROQ_API_KEY is missing for aggregator node.")
    if not path:
        logger.error("Configuration error: Prompt path is missing")
        raise ValueError("Missing configuration: Could not load prompt from AGGREGATOR_PROMPT path.")
    if not model_name:
        logger.error("Configuration error: LLM model name is missing")
        raise ValueError("Missing configuration: LLM model name is not set.")

    _AGGREGATOR_PROMPT_CONTENT = load_prompt(path)
    
    if not _AGGREGATOR_PROMPT_CONTENT:
        logger.error("Configuration error: Prompt is missing")
        raise ValueError("Missing configuration: Could not load prompt content.")

    LLM = ChatGroq(model=model_name, temperature=0.3, api_key=groq_api_key)


def aggregator_node(state: AgentState)-> AgentState:
    
    _initialize_llm()
    
    responses = {
        "order": state.get("order_response", ""),
        "product": state.get("product_response", ""),
        "general": state.get("general_response", "")
    }
    # Filter out empty responses
    active_responses = {k: v for k, v in responses.items() if v}

    # Extract the latest user question from the messages
    human_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    if human_messages:
        user_question = human_messages[-1].content
    else:
        user_question = "User question not found in messages."

    formatted_responses = "\n".join([
        f"- {agent}_agent: \"{response}\"" 
        for agent, response in active_responses.items()
    ])

    if not formatted_responses:
        formatted_responses = "- No agent responses available"
    
    final_prompt = _AGGREGATOR_PROMPT_CONTENT.format(
        user_question=user_question,
        agent_responses=formatted_responses
    )
    response = LLM.invoke(final_prompt)
    logger.info(f"Aggregator Agent Response: {response}")

    return {"messages": [AIMessage(content = response.content)],
            "order_response": "",
            "product_response": "",
            "general_response": "",
            "router_decision": []
            }