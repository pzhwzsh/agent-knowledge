from pydantic import BaseModel, Field


class RouteResult(BaseModel):
    source_type: str
    category: str
    route_to: str
    confidence: float = Field(ge=0, le=1)
    reason: str


class ArticleSummary(BaseModel):
    title: str
    short_summary: str
    long_summary: str
    key_points: list[str]
    tags: list[str]
    audience: str
    action_items: list[str]
    citations: list[str]


class GitHubSummary(BaseModel):
    purpose: str
    tech_stack: list[str]
    core_features: list[str]
    use_cases: list[str]
    learning_value: str
    interview_value: str
    reusable_design: list[str]
    readme_summary: str
    metadata: dict[str, object]


class LifestyleSummary(BaseModel):
    advice: list[str]
    audience: str
    cautions: list[str]
    risks: list[str]
    checklist: list[str]
    worth_saving: bool


class RecommendationDecision(BaseModel):
    score: int = Field(ge=0)
    should_push: bool
    reason: str
    matched_interests: list[str]
    negative_signals: list[str]
    category: str
