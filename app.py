import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.messages import HumanMessage
from graph import graph
from models.request_model import InputModel
from models.response_model import ResponseModel


app = FastAPI(title="Chatbot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ResponseModel)
async def chat_endpoint(request: InputModel):

    user_message = {"messages": [HumanMessage(content= request.message)]}
    response = graph.invoke(user_message)

    return {"response": response["messages"][-1].content}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app=app, host= "0.0.0.0", port= 8000)