from app.models.session import Message
import time

class ChatService:
    def __init__(
        self,
        settings,
        kb_service,
        session_store,
        memory_service,
        reflection_service,
        decision_service,
    ):
        self.settings = settings
        self.kb_service = kb_service
        self.session_store = session_store
        self.memory_service = memory_service
        self.reflection_service = reflection_service
        self.decision_service = decision_service

    def _extract_filters_from_query(self, query: str) -> dict:
        filters = {}
        category_keywords = self.kb_service.data_module.get_supported_categories()
        for cat in category_keywords:
            if cat in query:
                filters["category"] = cat
                break

        difficulty_keywords = self.kb_service.data_module.get_supported_difficulties()
        for diff in sorted(difficulty_keywords, key=len, reverse=True):
            if diff in query:
                filters["difficulty"] = diff
                break
        return filters
    
    def _log_step(self, session_id: str, step: str, start_time: float):
        elapsed = time.perf_counter() - start_time
        print(f"[chat][{session_id}] {step} finished in {elapsed:.2f}s", flush=True)

    def chat(self, session_id: str, user_message: str):
        session = self.session_store.get_or_create(session_id)

        session.history.append(Message(role="user", content=user_message))

        route = self.kb_service.generation_module.query_router(user_message)

        decision = self.decision_service.decide(user_message, route, session)

        rewritten_query = user_message
        if decision["rewrite_query"]:
            rewritten_query = self.kb_service.generation_module.query_rewrite(user_message)

        filters = self._extract_filters_from_query(user_message)

        _, parent_docs, retrieval_debug = self.kb_service.retrieve(
            rewritten_query,
            filters=filters if filters else None,
            top_k=decision["retrieve_top_k"]
        )

        history_text = self.memory_service.build_history_text(
            session,
            window=self.settings.history_window
        )

        session.short_memory = self.memory_service.build_short_memory(
            session,
            window=self.settings.history_window,
            max_items=6
        )

        memory_dict = self.memory_service.retrieve_memories(
            session,
            query=user_message,
            short_top_k=2,
            long_top_k=self.settings.memory_top_k
        )
        short_memory_items = memory_dict["short_memory"]
        long_memory_items = memory_dict["long_memory"]

        reflection_text = ""
        if session.reflections:
            reflection_text = "\n".join(
                [r.content for r in session.reflections[-self.settings.reflection_window:]]
            )

        if decision["route"] == "list":
            answer = self.kb_service.generation_module.generate_list_answer(user_message, parent_docs)
        elif decision["route"] == "detail":
            answer = self.kb_service.generation_module.generate_step_by_step_answer(
                user_message,
                parent_docs,
                conversation_history=history_text,
                short_memory_context="\n".join(short_memory_items),
                long_memory_context="\n".join(long_memory_items),
                reflection_context=reflection_text,
            )
        else:
            answer = self.kb_service.generation_module.generate_basic_answer(
                user_message,
                parent_docs,
                conversation_history=history_text,
                short_memory_context="\n".join(short_memory_items),
                long_memory_context="\n".join(long_memory_items),
                reflection_context=reflection_text,
            )

        session.history.append(Message(role="assistant", content=answer))

        new_long_memories = self.memory_service.extract_long_memory(self.kb_service, session)
        existing = {m.content for m in session.long_memory}
        for item in new_long_memories:
            if item.content not in existing:
                session.long_memory.append(item)

        reflection = self.reflection_service.reflect(
            self.kb_service, user_message, answer, retrieval_debug
        )

        session.reflections.append(reflection)

        self.session_store.save(session)

        return {
            "session_id": session_id,
            "answer": answer,
            "route": decision["route"],
            "rewritten_query": rewritten_query,
            "memory_used": [
                *[f"[short] {x}" for x in short_memory_items],
                *[f"[long] {x}" for x in long_memory_items],
            ],
            "reflection": reflection.content,
            "references": [doc.metadata.get("dish_name", "未知菜品") for doc in parent_docs],
            "retrieval_debug": retrieval_debug,
        }

    def get_history(self, session_id: str):
        session = self.session_store.get_or_create(session_id)
        return [{"role": m.role, "content": m.content} for m in session.history]

    def get_memory(self, session_id: str):
        session = self.session_store.get_or_create(session_id)
        return {
            "session_id": session_id,
            "short_memory": [m.content for m in session.short_memory],
            "long_memory": [m.content for m in session.long_memory],
            "reflections": [r.content for r in session.reflections],
        }