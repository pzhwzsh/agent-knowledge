from app.agents.base import AgentRunner
from app.agents.llm_summary import complete_json_summary
from app.llm.base import ChatModel
from app.llm.providers import get_chat_model
from app.schemas.agents import LifestyleSummary


class LifestyleAgent(AgentRunner[dict[str, str], LifestyleSummary]):
    def __init__(self, chat_model: ChatModel | None = None) -> None:
        self.chat_model = chat_model or get_chat_model()

    def run(self, payload: dict[str, str]) -> LifestyleSummary:
        fallback = _fallback_summary()
        return complete_json_summary(
            self.chat_model,
            schema=LifestyleSummary,
            task="总结生活类内容，提取建议、适合人群、注意事项、风险、检查清单，并判断是否值得保存。",
            payload={
                "title": payload.get("title", ""),
                "text": (payload.get("text") or "")[:12000],
                "source": payload.get("source", ""),
            },
            fallback=fallback,
        )


def _fallback_summary() -> LifestyleSummary:
    return LifestyleSummary(
        advice=["Extract practical steps before saving the article."],
        audience="Readers interested in daily life improvements",
        cautions=["Validate health or finance claims with authoritative sources."],
        risks=[],
        checklist=["Decide whether the advice applies to your context."],
        worth_saving=True,
    )
