from fastapi import FastAPI
from app.core.dependencies import chat_service, kb_service
from app.models.schemas import ChatRequest, ChatResponse, SessionHistoryResponse, MemoryResponse

app = FastAPI(title="Recipe RAG Backend")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/kb/stats")
def kb_stats():
    return kb_service.stats()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return chat_service.chat(req.session_id, req.message)

@app.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
def history(session_id: str):
    return {
        "session_id": session_id,
        "history": chat_service.get_history(session_id)
    }

@app.get("/sessions/{session_id}/memory", response_model=MemoryResponse)
def memory(session_id: str):
    return chat_service.get_memory(session_id)