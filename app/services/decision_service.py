class DecisionService:
    def __init__(self, settings):
        self.settings = settings

    def decide(self, query: str, route_from_llm: str, session) -> dict:
        retrieve_top_k = self.settings.top_k
        use_memory = True
        rewrite_query = route_from_llm != "list"
        need_reflection = True

        if any(x in query for x in ["继续", "刚才", "上一个", "那个菜", "这个步骤"]):
            use_memory = True
            retrieve_top_k += 1

        if route_from_llm == "detail":
            retrieve_top_k += 1

        if session.reflections:
            latest = session.reflections[-1].content
            if "检索不足" in latest:
                retrieve_top_k += 1

        return {
            "route": route_from_llm,
            "use_memory": use_memory,
            "rewrite_query": rewrite_query,
            "retrieve_top_k": retrieve_top_k,
            "need_reflection": need_reflection,
        }