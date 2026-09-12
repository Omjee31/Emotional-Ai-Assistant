from pathlib import Path
import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

PERSONALITIES = {
    "happy": "You are a warm, energetic assistant. Be encouraging and positive without being over the top.",
    "sad": "You are a calm, emotionally sensitive assistant. Be gentle, patient, and grounded.",
    "angry": "You are a direct, frustrated-toned assistant. Keep answers short and clear without abuse or hostility.",
    "professional": "You are a precise professional assistant. Be structured, concise, and practical.",
    "sarcastic": "You are a witty assistant. Use light, clever sarcasm while staying helpful and respectful.",
}

Personality = Literal["happy", "sad", "angry", "professional", "sarcastic"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    personality: Personality = "professional"
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    personality: Personality
    provider: str


app = FastAPI(title="Moodmate API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def fallback_reply(message: str, personality: str) -> str:
    """Keep the product usable locally when no hosted model credentials exist."""
    starters = {
        "happy": "I am glad you brought this here. ",
        "sad": "That sounds heavy, and it is okay to take it one step at a time. ",
        "angry": "Let us get to the point. ",
        "professional": "Here is a clear way to think about it. ",
        "sarcastic": "Ah, the timeless art of making one problem wear a tiny hat. ",
    }
    return (
        starters[personality]
        + f"You said: \"{message}\". I am running in local demo mode right now, "
        "so connect a model provider to receive a generated response."
    )


def generate_reply(request: ChatRequest) -> tuple[str, str]:
    huggingface_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if huggingface_token:
        try:
            from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

            llm = HuggingFaceEndpoint(
                repo_id=os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-V4.1-Flash"),
                huggingfacehub_api_token=huggingface_token,
                temperature=0.7,
                max_new_tokens=512,
            )
            model = ChatHuggingFace(llm=llm)
            messages = [SystemMessage(content=PERSONALITIES[request.personality])]
            messages.extend(
                HumanMessage(content=item.content) if item.role == "user" else AIMessage(content=item.content)
                for item in request.history[-10:]
            )
            messages.append(HumanMessage(content=request.message))
            response = model.invoke(messages)
            return str(response.content), "Hugging Face"
        except Exception as exc:
            print(f"Hugging Face provider unavailable, using demo mode: {exc}")
            return fallback_reply(request.message, request.personality), "Local demo (Hugging Face unavailable)"

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

            model = ChatGoogleGenerativeAI(
                model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
                temperature=0.7,
                google_api_key=api_key,
            )
            messages = [SystemMessage(content=PERSONALITIES[request.personality])]
            messages.extend(
                HumanMessage(content=item.content) if item.role == "user" else AIMessage(content=item.content)
                for item in request.history[-10:]
            )
            messages.append(HumanMessage(content=request.message))
            response = model.invoke(messages)
            return str(response.content), "Google Gemini"
        except Exception as exc:
            print(f"Model provider unavailable, using demo mode: {exc}")

    return fallback_reply(request.message, request.personality), "Local demo"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "moodmate"}


@app.get("/api/personalities")
def personalities() -> dict[str, list[dict[str, str]]]:
    return {
        "personalities": [
            {"id": key, "label": key.title(), "description": value.split(".")[0] + "."}
            for key, value in PERSONALITIES.items()
        ]
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply, provider = generate_reply(request)
        return ChatResponse(reply=reply, personality=request.personality, provider=provider)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to generate a response") from exc


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
