
from fastapi import FastAPI
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, AIMessage
from src.rag import answer_question_stream

app = FastAPI(
    title="Tamil Nadu Agricultural Scheme AI",
    description="AI assistant for Tamil Nadu agricultural schemes",
    version="1.0.0"
)


class ChatMessage(BaseModel):
    role: str
    content: str


class QuestionRequest(BaseModel):
    question: str
    chat_history: list[ChatMessage] = Field(default_factory=list)


@app.get("/")
def home():
    return {
        "message": "Tamil Nadu Agricultural Scheme API is running"
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):

    # Convert frontend messages into LangChain messages
    history = []

    for message in request.chat_history:

        if message.role == "user":
            history.append(
                HumanMessage(content=message.content)
            )

        elif message.role == "assistant":
            history.append(
                AIMessage(content=message.content)
            )

    answer = answer_question_stream(
        request.question,
        chat_history=history
    )

    return {
        "question": request.question,
        "answer": answer
    }
