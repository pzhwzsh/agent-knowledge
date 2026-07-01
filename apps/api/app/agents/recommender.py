from app.agents.base import AgentRunner
from app.agents.llm_summary import complete_json
from app.llm.base import ChatModel
from app.llm.providers import get_chat_model
from app.schemas.agents import RecommendationDecision


class RecommenderAgent(AgentRunner[dict[str, object], RecommendationDecision]):
    def __init__(self, chat_model: ChatModel | None = None) -> None:
        self.chat_model = chat_model or get_chat_model()

    def run(self, payload: dict[str, object]) -> RecommendationDecision:
        fallback = _rule_based_decision(payload)
        return complete_json(
            self.chat_model,
            schema=RecommendationDecision,
            task=(
                "判断内容是否值得推荐给当前用户。结合标题、正文、分类、兴趣关键词、"
                "不感兴趣关键词和启用分类，返回 0-100 score、should_push、reason、"
                "matched_interests、negative_signals 和 category。"
            ),
            payload={
                "title": payload.get("title") or "",
                "text": str(payload.get("text") or "")[:12000],
                "category": payload.get("category") or "other",
                "interests": payload.get("interests", []),
                "negative_interests": payload.get("negative_interests", []),
                "enabled_categories": payload.get("enabled_categories", []),
            },
            fallback=fallback,
        )


def _rule_based_decision(payload: dict[str, object]) -> RecommendationDecision:
    title = str(payload.get("title") or "")
    text = str(payload.get("text") or "")
    category = str(payload.get("category") or "other")
    haystack = f"{title} {text}".lower()
    interests = [str(item).lower() for item in payload.get("interests", []) if str(item).strip()]
    negatives = [str(item).lower() for item in payload.get("negative_interests", []) if str(item).strip()]
    enabled_categories = {str(item) for item in payload.get("enabled_categories", [])}

    matched = [interest for interest in interests if interest in haystack]
    negative_signals = [negative for negative in negatives if negative in haystack]
    score = 50 + len(matched) * 20 - len(negative_signals) * 30
    if enabled_categories and category not in enabled_categories:
        score -= 25
    score = max(0, min(100, score))
    return RecommendationDecision(
        score=score,
        should_push=score >= 50 and not negative_signals,
        reason=_build_reason(matched, negative_signals, category),
        matched_interests=matched,
        negative_signals=negative_signals,
        category=category,
    )


def _build_reason(matched: list[str], negatives: list[str], category: str) -> str:
    if negatives:
        return f"Contains negative signals for category {category}: {', '.join(negatives)}"
    if matched:
        return f"Matched interests for category {category}: {', '.join(matched)}"
    return f"Baseline recommendation for category {category}."
