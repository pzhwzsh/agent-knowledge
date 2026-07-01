from app.agents.base import AgentRunner
from app.agents.llm_summary import complete_json_summary
from app.llm.base import ChatModel
from app.llm.providers import get_chat_model
from app.schemas.agents import ArticleSummary


class GeneralAgent(AgentRunner[dict[str, str], ArticleSummary]):
    def __init__(self, chat_model: ChatModel | None = None) -> None:
        self.chat_model = chat_model or get_chat_model()

    def run(self, payload: dict[str, str]) -> ArticleSummary:
        fallback = _fallback_summary(payload)
        return complete_json_summary(
            self.chat_model,
            schema=ArticleSummary,
            task="总结一篇通用文章，提取短摘要、长摘要、要点、标签、受众、行动项和引用。",
            payload={
                "title": payload.get("title") or "Untitled",
                "text": (payload.get("text") or "")[:12000],
                "source": payload.get("source", ""),
            },
            fallback=fallback,
        )


def _fallback_summary(payload: dict[str, str]) -> ArticleSummary:
    title = payload.get("title") or "Untitled"
    text = payload.get("text", "")
    excerpt = text[:200] or "No content provided."
    return ArticleSummary(
        title=title,
        short_summary=excerpt,
        long_summary=excerpt,
        key_points=[excerpt],
        tags=["general", "fallback"],
        audience="General readers",
        action_items=[],
        citations=[payload.get("source", "")],
    )
