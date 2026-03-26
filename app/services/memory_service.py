from app.models.session import MemoryItem
from difflib import SequenceMatcher

class MemoryService:
    def build_history_text(self, session, window: int = 6) -> str:
        recent = session.history[-window:]
        return "\n".join([f"{m.role}: {m.content}" for m in recent])
    
    def _normalize_text(self, text: str) -> str:
        return (text or "").strip().lower()

    def _sim(self, a: str, b: str) -> float:
        a = self._normalize_text(a)
        b = self._normalize_text(b)
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()
    
    def _dedup_memory_items(self, items, threshold: float = 0.88):
        result = []
        for item in items:
            duplicated = False
            for existing in result:
                if self._sim(item.content, existing.content) >= threshold:
                    duplicated = True
                    break
            if not duplicated:
                result.append(item)
        return result
    
    def build_short_memory(self, session, window: int = 6, max_items: int = 6):
        """
        short memory 不调用 LLM，直接从最近对话中构建
        重点保留：最近菜品列表、当前关注对象、最近用户问题
        """
        recent = session.history[-window:]
        if not recent:
            return []

        items = []

        # 1. 保留最近几条用户/助手消息摘要（轻量）
        for msg in recent[-4:]:
            prefix = "用户最近提到" if msg.role == "user" else "助手最近回复"
            items.append(
                MemoryItem(
                    content=f"{prefix}: {msg.content[:120]}",
                    source="recent_history",
                    memory_type="short"
                )
            )

        # 2. 如果最近一次 assistant 回复是列表型，保留一个顺序映射提示
        last_assistant_msgs = [m.content for m in recent if m.role == "assistant"]
        if last_assistant_msgs:
            last_answer = last_assistant_msgs[-1]
            if "1." in last_answer or "2." in last_answer:
                items.append(
                    MemoryItem(
                        content=f"最近推荐列表: {last_answer[:200]}",
                        source="recent_list_answer",
                        memory_type="short"
                    )
                )

        items = self._dedup_memory_items(items)
        return items[-max_items:]
    
    def retrieve_memories(self, session, query: str, short_top_k: int = 3, long_top_k: int = 3):
        """
        简单记忆召回：
        - short memory：按时间近 + 轻相似度
        - long memory：按相似度
        """
        short_scored = []
        for idx, item in enumerate(session.short_memory):
            sim_score = self._sim(query, item.content)
            recency_bonus = 0.05 * (idx + 1)
            short_scored.append((sim_score + recency_bonus, item))

        long_scored = []
        for item in session.long_memory:
            sim_score = self._sim(query, item.content)
            long_scored.append((sim_score, item))

        short_scored.sort(key=lambda x: x[0], reverse=True)
        long_scored.sort(key=lambda x: x[0], reverse=True)

        short_items = [x[1].content for x in short_scored[:short_top_k]]
        long_items = [x[1].content for x in long_scored[:long_top_k]]

        return {
            "short_memory": short_items,
            "long_memory": long_items,
        }

    def extract_long_memory(self, kb_service, session):
        """
        只提取长期稳定信息，不再混入短期任务态
        """    
        history_text = self.build_history_text(session, window=6)
        if not history_text.strip():
            return []

#         prompt = f"""
# 请从以下对话中提取适合长期保存的用户偏好或稳定事实。
# 仅提取未来回答会有帮助的内容，不要提取一次性内容。
# 每条单独一行；如果没有可提取内容，返回“无”。

# 对话：
# {history_text}
# """
        
        prompt = f"""
请从以下对话中提取“适合长期保存”的稳定信息，只保留未来很多轮对话仍然有帮助的信息。

重点提取：
1. 用户饮食偏好
- 喜欢/不喜欢的口味
- 忌口、过敏、宗教限制
- 减脂、增肌、控糖、低盐、低油等目标

2. 用户做饭习惯
- 可接受的复杂度、耗时、预算
- 偏好家常菜、快手菜、汤类、川菜等

3. 回答偏好
- 喜欢简洁还是详细
- 是否偏好分步骤、表格、食材克数

不要提取：
- 当前正在聊哪一道菜
- 最近推荐列表
- “第一个/第二个/那个菜”这类短期指代
- 一次性上下文
- 客套话和废话

输出规则：
- 每条单独一行
- 只输出长期稳定信息
- 没有则输出“无”

对话：
{history_text}
"""
        result = kb_service.generation_module.llm.invoke(prompt)
        text = getattr(result, "content", str(result)).strip()

        if text == "无":
            return []

        items = []
        for line in text.splitlines():
            line = line.strip("- ").strip()
            if line:
                items.append(
                    MemoryItem(
                        content=line,
                        source="llm_extract",
                        memory_type="long"
                    )
                )
        return self._dedup_memory_items(items)