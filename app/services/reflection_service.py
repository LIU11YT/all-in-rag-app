from app.models.session import ReflectionItem

class ReflectionService:
    def reflect(self, kb_service, query: str, answer: str, retrieval_debug: list) -> ReflectionItem:
        retrieval_text = "\n".join([
            f"- {x['dish_name']} | {x['preview']}"
            for x in retrieval_debug
        ])

        prompt = f"""
你是RAG系统的评估器。请对本轮问答进行简短反思，输出1段中文，不超过80字。
关注：
1. 路由是否合理
2. 检索是否足够
3. 回答是否遗漏关键点
4. 下轮可优化什么

用户问题：
{query}

回答：
{answer}

检索片段：
{retrieval_text}
"""
        result = kb_service.generation_module.llm.invoke(prompt)
        text = getattr(result, "content", str(result)).strip()
        return ReflectionItem(content=text)