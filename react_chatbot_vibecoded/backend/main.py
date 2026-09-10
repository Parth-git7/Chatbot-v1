from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage


app = FastAPI()


# Allow React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str


@app.post("/chat")
def chat(request: ChatRequest):

    config = {
        "configurable": {
            "thread_id": request.thread_id
        }
    }

    result = chatbot.invoke(
        {
            "messages": [
                HumanMessage(content=request.message)
            ]
        },
        config=config
    )

    ai_message = result["messages"][-1]

    return {
        "response": ai_message.content
    }


@app.get("/conversation/{thread_id}")
def get_conversation(thread_id: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = chatbot.get_state(config=config)

    messages = state.values.get("messages", [])

    conversation = []

    for message in messages:

        if isinstance(message, HumanMessage):

            conversation.append({
                "role": "user",
                "content": message.content
            })

        else:

            conversation.append({
                "role": "assistant",
                "content": message.content
            })

    return {
        "messages": conversation
    }