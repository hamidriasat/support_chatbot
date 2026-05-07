import uvicorn
from groq import Groq
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain.messages import HumanMessage
from langgraph.types import Command
from graph.graph import build_workflow
from models.request_model import InputTextModel
from models.response_model import ResponseModel, VoiceResponseModel
from utils.state_helper import extract_message_from_interrupted_subgraph
from utils.config import settings


app = FastAPI(title="Chatbot Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

GROQ_CLIENT = Groq(api_key=settings.get("GROQ_API_KEY"))
GRAPH = build_workflow()


# Endpoint for handling text input
@app.post("/chat", response_model=ResponseModel)
async def chat_endpoint(request: InputTextModel):
    config = {
        "configurable": {
            "thread_id": request.chat_id
        },
        "recursion_limit": 10
    }

    current_state = GRAPH.get_state(config, subgraphs=True)
    
    if current_state.next:
        # Graph is interrupted — resume with user's confirmation
        response = GRAPH.invoke(
            Command(resume=HumanMessage(content=request.message)),
            config=config
        )
    else:
        user_message = {"messages": [HumanMessage(content=request.message)]}
        response = GRAPH.invoke(user_message, config=config)
    
    new_state = GRAPH.get_state(config, subgraphs=True)
    waiting = len(new_state.next) > 0
    # Get the final message content
    final_content = ""
    # If we're waiting and there's no content, check the state values for the last message
    if waiting:
        final_content = extract_message_from_interrupted_subgraph(new_state)
    
    if not final_content:
        parent_messages = new_state.values.get("messages", [])
        for msg in reversed(parent_messages):
            if hasattr(msg, "content") and msg.content:
                if not isinstance(msg, HumanMessage):
                    final_content = msg.content
                    break
    return {
        "response": final_content,
        "waiting_for_approval": waiting
    }


# Endpoint for handling voice input
@app.post("/voice", response_model=VoiceResponseModel)
async def voice_endpoint(audio: UploadFile = File(...),
                         chat_id: str = Form(...)):
    config = {
        "configurable": {
            "thread_id": chat_id
        },
        "recursion_limit": 10
    }

    audio_bytes = await audio.read()
    transcription = GROQ_CLIENT.audio.transcriptions.create(
        file=(audio.filename, audio_bytes),
        model="whisper-large-v3-turbo"
        )
    user_text = transcription.text
    print(f"Transcribed audio to text: {user_text}")

    current_state = GRAPH.get_state(config, subgraphs=True)
    
    if current_state.next:
        response = GRAPH.invoke(
            Command(resume=HumanMessage(content=user_text)),
            config=config
        )
    else:
        user_message = {"messages": [HumanMessage(content=user_text)]}
        response = GRAPH.invoke(user_message, config=config)
    
    new_state = GRAPH.get_state(config, subgraphs=True)
    waiting = len(new_state.next) > 0
    # Get the final message content
    final_content = ""
    # If we're waiting and there's no content, check the state values for the last message
    if waiting:
        final_content = extract_message_from_interrupted_subgraph(new_state)
    
    if not final_content:
        parent_messages = new_state.values.get("messages", [])
        for msg in reversed(parent_messages):
            if hasattr(msg, "content") and msg.content:
                if not isinstance(msg, HumanMessage):
                    final_content = msg.content
                    break
    return {
        "transcription": user_text,
        "response": final_content,
        "waiting_for_approval": waiting
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app=app, host= "0.0.0.0", port= 8000)