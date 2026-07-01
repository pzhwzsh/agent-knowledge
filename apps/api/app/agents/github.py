from app.agents.base import AgentRunner
from app.schemas.agents import GitHubSummary


class GitHubAgent(AgentRunner[dict[str, object], GitHubSummary]):
    def run(self, payload: dict[str, object]) -> GitHubSummary:
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
