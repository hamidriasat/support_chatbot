import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.messages import HumanMessage
from langgraph.types import Command
from graph.graph import build_workflow
from models.request_model import InputModel
from models.response_model import ResponseModel

app = FastAPI(title="Chatbot Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


GRAPH = build_workflow()

@app.post("/chat", response_model=ResponseModel)
async def chat_endpoint(request: InputModel):
    config = {
        "configurable": {
            "thread_id": request.chat_id
        },
        "recursion_limit": 10
    }

    current_state = GRAPH.get_state(config)
    
    if current_state.next:
        # Determine which agent we're waiting in by checking the last message
        # and resuming appropriately
        response = GRAPH.invoke(
            Command(resume=HumanMessage(content=request.message)),
            config=config
        )
    else:
        user_message = {"messages": [HumanMessage(content=request.message)]}
        response = GRAPH.invoke(user_message, config=config)
    
    new_state = GRAPH.get_state(config)
    waiting = len(new_state.next) > 0

    # Get the final message content
    final_content = ""
    
    if response.get("messages") and len(response["messages"]) > 0:
        final_content = response["messages"][-1].content
    
    # If we're waiting and there's no content, check the state values for the last message
    if waiting and not final_content:
        state_messages = new_state.values.get("messages", [])
        if state_messages:
            # Get the last AI message from state
            for msg in reversed(state_messages):
                if hasattr(msg, 'content') and msg.content and not isinstance(msg, HumanMessage):
                    final_content = msg.content
                    break

    return {
        "response": final_content,
        "waiting_for_approval": waiting
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app=app, host= "0.0.0.0", port= 8000)