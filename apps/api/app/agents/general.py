from app.agents.base import AgentRunner
from app.schemas.agents import ArticleSummary


class GeneralAgent(AgentRunner[dict[str, str], ArticleSummary]):
    def run(self, payload: dict[str, str]) -> ArticleSummary:
        title = payload.get("title") or "Untitled"
        text = payload.get("text", "")
        excerpt = text[:200] or "No content provided."
        return ArticleSummary(
            title=title,
            short_summary=excerpt,
            long_summary=excerpt,
            key_points=[excerpt],
            tags=["general"],
            audience="General readers",
            action_items=[],
            citations=[payload.get("source", "")],
        )
