from app.agents.base import AgentRunner
from app.agents.llm_summary import complete_json_summary
from app.llm.base import ChatModel
from app.llm.providers import get_chat_model
from app.schemas.agents import GitHubSummary


class GitHubAgent(AgentRunner[dict[str, object], GitHubSummary]):
    def __init__(self, chat_model: ChatModel | None = None) -> None:
        self.chat_model = chat_model or get_chat_model()

    def run(self, payload: dict[str, object]) -> GitHubSummary:
        fallback = _fallback_summary(payload)
        return complete_json_summary(
            self.chat_model,
            schema=GitHubSummary,
            task="总结 GitHub 仓库，提取用途、技术栈、核心功能、使用场景、学习价值、面试价值和可复用设计。",
            payload={**payload, "readme": str(payload.get("readme") or "")[:12000]},
            fallback=fallback,
        )


def _fallback_summary(payload: dict[str, object]) -> GitHubSummary:
    topics = payload.get("topics")
    topic_list = topics if isinstance(topics, list) else []
    return GitHubSummary(
        purpose=str(payload.get("description") or "Summarize the repository purpose."),
        tech_stack=[str(topic) for topic in topic_list],
        core_features=[],
        use_cases=[],
        learning_value="Useful for learning once README parsing is implemented.",
        interview_value="Can be reviewed for architecture and implementation tradeoffs.",
        reusable_design=[],
        readme_summary=str(payload.get("readme") or "README content not provided."),
        metadata={"stars": payload.get("stars", 0), "topics": topic_list},
    )
