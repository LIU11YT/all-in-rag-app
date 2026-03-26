from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    session_id: str
    message: str
    stream: bool = False

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    route: str
    rewritten_query: str
    memory_used: List[str]
    reflection: str
    references: List[str]
    retrieval_debug: List[Dict[str, Any]]

class SessionHistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, str]]

class MemoryResponse(BaseModel):
    session_id: str
    short_memory: List[str]
    long_memory: List[str]
    reflections: List[str]