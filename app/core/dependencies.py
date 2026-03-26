from app.core.config import settings
from app.services.kb_service import KnowledgeBaseService
from app.services.session_store import SQLiteSessionStore
from app.services.memory_service import MemoryService
from app.services.reflection_service import ReflectionService
from app.services.decision_service import DecisionService
from app.services.chat_service import ChatService

kb_service = KnowledgeBaseService(settings)
kb_service.initialize()

session_store = SQLiteSessionStore(settings.sqlite_path)
memory_service = MemoryService()
reflection_service = ReflectionService()
decision_service = DecisionService(settings)

chat_service = ChatService(
    settings=settings,
    kb_service=kb_service,
    session_store=session_store,
    memory_service=memory_service,
    reflection_service=reflection_service,
    decision_service=decision_service,
)