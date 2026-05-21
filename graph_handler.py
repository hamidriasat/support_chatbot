from fastapi import UploadFile
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from graph.graph import build_workflow
from utils.voice_handle import (
    sst_groq,
    tts_groq
)
from utils.state_helper import extract_message_from_interrupted_subgraph


GRAPH = build_workflow()


def _get_config(chat_id: str) -> dict:
    """Builds the graph config for a given chat_id."""
    return {
        "configurable": {"thread_id": chat_id},
        "recursion_limit": 10
    }


def _extract_final_content(new_state, waiting: bool) -> str:
    """Extracts the final message content from graph state."""
    final_content = ""

    if waiting:
        final_content = extract_message_from_interrupted_subgraph(new_state)

    if not final_content:
        parent_messages = new_state.values.get("messages", [])
        for msg in reversed(parent_messages):
            if hasattr(msg, "content") and msg.content:
                if not isinstance(msg, HumanMessage):
                    final_content = msg.content
                    break

    return final_content


async def handle_chat(message: str, chat_id: str) -> dict:
    """
    Pure chat logic — no FastAPI dependency.
    Called by both chat_endpoint (app.py) and process_text_message (whatsapp_helpers.py)
    """
    config = _get_config(chat_id)

    current_state = GRAPH.get_state(config, subgraphs=True)

    if current_state.next:
        # Graph is interrupted — resume with user's confirmation
        GRAPH.invoke(
            Command(resume=HumanMessage(content=message)),
            config=config
        )
    else:
        user_message = {"messages": [HumanMessage(content=message)]}
        GRAPH.invoke(user_message, config=config)

    new_state = GRAPH.get_state(config, subgraphs=True)
    waiting   = len(new_state.next) > 0

    final_content = _extract_final_content(new_state, waiting)

    return {
        "response": final_content,
        "waiting_for_approval": waiting
    }


async def handle_voice(audio: UploadFile, chat_id: str) -> dict:
    """
    Pure voice logic — no FastAPI dependency.
    Called by both voice_endpoint (app.py) and process_voice_message (whatsapp_helpers.py)
    """
    config = _get_config(chat_id)

    # Transcribe audio
    user_text = await sst_groq(audio)

    # Handle empty transcription
    if not user_text:
        nudge_text   = "I'm sorry, I didn't catch that. Could you please repeat?"
        audio_base64 = tts_groq(nudge_text)
        return {
            "response": nudge_text,
            "audio": audio_base64,
            "transcription": "",
            "waiting_for_approval": False
        }

    # Handle transcription error
    if "error" in user_text.lower():
        audio_base64 = tts_groq(user_text)
        return {
            "response": user_text,
            "audio": audio_base64,
            "transcription": "",
            "waiting_for_approval": False
        }

    current_state = GRAPH.get_state(config, subgraphs=True)

    if current_state.next:
        GRAPH.invoke(
            Command(resume=HumanMessage(content=user_text)),
            config=config
        )
    else:
        user_message = {"messages": [HumanMessage(content=user_text)]}
        GRAPH.invoke(user_message, config=config)

    new_state     = GRAPH.get_state(config, subgraphs=True)
    waiting       = len(new_state.next) > 0
    final_content = _extract_final_content(new_state, waiting)

    # Generate audio reply
    audio_base64 = tts_groq(final_content)

    # Handle TTS error
    if "error" in audio_base64.lower():
        return {
            "response": audio_base64,
            "audio": "",
            "transcription": user_text,
            "waiting_for_approval": False
        }

    return {
        "transcription": user_text,
        "response": final_content,
        "waiting_for_approval": waiting,
        "audio": audio_base64
    }