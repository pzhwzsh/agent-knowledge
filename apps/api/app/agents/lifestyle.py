from app.agents.base import AgentRunner
from app.schemas.agents import LifestyleSummary


class LifestyleAgent(AgentRunner[dict[str, str], LifestyleSummary]):
    def run(self, payload: dict[str, str]) -> LifestyleSummary:
        return LifestyleSummary(
            advice=["Extract practical steps before saving the article."],
            audience="Readers interested in daily life improvements",
            cautions=["Validate health or finance claims with authoritative sources."],
            risks=[],
            checklist=["Decide whether the advice applies to your context."],
            worth_saving=True,
        )
