from langgraph.types import StateSnapshot
from langchain_core.messages import HumanMessage

def extract_message_from_interrupted_subgraph(state: StateSnapshot) -> str:
    """
    Walk the task tree of a StateSnapshot (returned with subgraphs=True)
    to find the last meaningful AI message from an interrupted child graph.
    
    LangGraph exposes child graph states inside state.tasks[i].state
    when you pass subgraphs=True.
    """
    for task in state.tasks:
        # Each task has a .state attribute if it's a subgraph task
        child_state = getattr(task, "state", None)
        if child_state is None:
            continue

        # Recursively check nested subgraphs (grandchild agents, etc.)
        nested_content = extract_message_from_interrupted_subgraph(child_state)
        if nested_content:
            return nested_content

        # Read messages from this child's state
        messages = child_state.values.get("messages", [])
        for msg in reversed(messages):
            if (
                hasattr(msg, "content")
                and msg.content
                and not isinstance(msg, HumanMessage)
            ):
                return msg.content

    return ""