import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.messages import HumanMessage
from graph import build_workflow
from pydantic_models.request_model import InputModel
from pydantic_models.response_model import ResponseModel


app = FastAPI(title="Chatbot Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000/"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


GRAPH = build_workflow()

@app.post("/chat", response_model=ResponseModel)
async def chat_endpoint(request: InputModel):

    user_message = {"messages": [HumanMessage(content= request.message)]}
    config = {
    "configurable": {
        "thread_id": request.chat_id
    },
    "recursion_limit": 5
    }
    response = GRAPH.invoke(user_message, config=config)

    return {"response": response["messages"][-1].content}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app=app, host= "0.0.0.0", port= 8000)