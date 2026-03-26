from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time

@dataclass
class Message:
    role: str
    content: str

@dataclass
class MemoryItem:
    content: str
    source: str = "llm_extract"
    memory_type: str = "long"   # short / long

@dataclass
class ReflectionItem:
    content: str

@dataclass
class SessionState:
    session_id: str
    history: List[Message] = field(default_factory=list)
    short_memory: List[MemoryItem] = field(default_factory=list)
    long_memory: List[MemoryItem] = field(default_factory=list)
    reflections: List[ReflectionItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)