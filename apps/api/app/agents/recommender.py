from app.agents.base import AgentRunner
from app.schemas.agents import RecommendationDecision


class RecommenderAgent(AgentRunner[dict[str, object], RecommendationDecision]):
    def run(self, payload: dict[str, object]) -> RecommendationDecision:
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
