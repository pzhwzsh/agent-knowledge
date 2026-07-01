from app.agents.base import AgentRunner
from app.schemas.agents import RouteResult


class RouterAgent(AgentRunner[dict[str, str], RouteResult]):
    def run(self, payload: dict[str, str]) -> RouteResult:
        source = payload.get("source", "")
        text = payload.get("text", "")
        lowered = f"{source} {text}".lower()
        if "github.com" in lowered:
            return RouteResult(
                source_type="github",
                category="programming",
                route_to="github_agent",
                confidence=0.9,
                reason="Input looks like a GitHub repository or GitHub content.",
            )
        if any(keyword in lowered for keyword in ["??", "??", "??", "??", "??"]):
            return RouteResult(
                source_type="article",
                category="daily_life",
                route_to="lifestyle_agent",
                confidence=0.75,
                reason="Input contains lifestyle-oriented keywords.",
            )
        return RouteResult(
            source_type="article" if source.startswith("http") else "text",
            category="other",
            route_to="general_agent",
            confidence=0.6,
            reason="No specialized route matched; using the general agent.",
        )
