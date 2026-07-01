from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.agents.general import GeneralAgent
from app.agents.github import GitHubAgent
from app.agents.lifestyle import LifestyleAgent
from app.agents.recommender import RecommenderAgent
from app.agents.router import RouterAgent
from app.core.security import hash_password
from app.models.user import User
from app.repositories.documents import DocumentRepository
from app.schemas.document import DocumentCreate
from app.services.documents import DocumentService


def create_user(db: Session, email: str) -> User:
    user = User(email=email, password_hash=hash_password("password123"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_document_repository_filters_by_user(db_session: Session) -> None:
    alice = create_user(db_session, "alice-docs@example.com")
    bob = create_user(db_session, "bob-docs@example.com")
    repository = DocumentRepository(db_session)

    repository.create_for_user(
        alice.id,
        DocumentCreate(
            title="Alice Doc",
            source_type="text",
            category="other",
            tags=["alice"],
        ),
    )
    repository.create_for_user(
        bob.id,
        DocumentCreate(
            title="Bob Doc",
            source_type="text",
            category="other",
            tags=["bob"],
        ),
    )
    db_session.commit()

    alice_docs = repository.list_for_user(alice.id)
    bob_docs = repository.list_for_user(bob.id)

    assert [doc.title for doc in alice_docs] == ["Alice Doc"]
    assert [doc.title for doc in bob_docs] == ["Bob Doc"]


def test_document_service_is_idempotent_for_same_user_content(db_session: Session) -> None:
    from app.models.content import Content

    user = create_user(db_session, "idempotent@example.com")
    content = Content(source_type="text", title="Shared", content_hash="hash-1")
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    service = DocumentService(db_session)
    payload = DocumentCreate(
        content_id=content.id,
        title="Shared Doc",
        source_type="text",
        category="other",
        tags=[],
    )

    first = service.create_document_idempotent(user.id, payload)
    second = service.create_document_idempotent(user.id, payload)

    assert first.id == second.id
    assert len(DocumentRepository(db_session).list_for_user(user.id)) == 1


def test_router_agent_selects_github_route() -> None:
    result = RouterAgent().run({"source": "https://github.com/example/repo", "text": ""})

    assert result.source_type == "github"
    assert result.route_to == "github_agent"
    assert result.category == "programming"


class FakeJsonChatModel:
    def __init__(self, response: str) -> None:
        self.response = response
        self.messages: list[dict[str, str]] = []

    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        self.messages.extend(messages)
        return self.response


def test_llm_summary_agents_return_structured_outputs() -> None:
    lifestyle_model = FakeJsonChatModel(
        '{"advice":["Drink water"],"audience":"office workers","cautions":["do not overdo it"],"risks":[],"checklist":["prepare water"],"worth_saving":true}'
    )
    github_model = FakeJsonChatModel(
        '{"purpose":"A demo repo","tech_stack":["python"],"core_features":["demo"],"use_cases":["learning"],"learning_value":"high","interview_value":"medium","reusable_design":["service layer"],"readme_summary":"short","metadata":{"stars":42,"topics":["python"]}}'
    )

    lifestyle = LifestyleAgent(chat_model=lifestyle_model).run({"text": "daily hydration tips"})
    github = GitHubAgent(chat_model=github_model).run({"description": "A demo repo", "topics": ["python"], "stars": 42})

    assert lifestyle.worth_saving is True
    assert lifestyle.advice == ["Drink water"]
    assert github.metadata["stars"] == 42
    assert github.tech_stack == ["python"]
    assert "JSON schema" in github_model.messages[-1]["content"]


def test_general_agent_falls_back_when_model_returns_non_json() -> None:
    agent = GeneralAgent(chat_model=FakeJsonChatModel("not json"))

    summary = agent.run({"title": "Fallback", "text": "fallback content", "source": "local"})

    assert summary.title == "Fallback"
    assert summary.short_summary == "fallback content"
    assert "fallback" in summary.tags


def test_recommender_agent_uses_model_decision() -> None:
    model = FakeJsonChatModel(
        '{"score":88,"should_push":true,"reason":"模型判断很匹配","matched_interests":["fastapi"],"negative_signals":[],"category":"other"}'
    )

    decision = RecommenderAgent(chat_model=model).run(
        {"title": "FastAPI", "text": "agent knowledge", "category": "other", "interests": ["fastapi"]}
    )

    assert decision.score == 88
    assert decision.should_push is True
    assert decision.reason == "模型判断很匹配"
    assert decision.matched_interests == ["fastapi"]
    assert "判断内容是否值得推荐" in model.messages[-1]["content"]


def test_recommender_agent_falls_back_to_rules_when_model_returns_non_json() -> None:
    decision = RecommenderAgent(chat_model=FakeJsonChatModel("not json")).run(
        {
            "title": "FastAPI article",
            "text": "fastapi knowledge",
            "category": "other",
            "interests": ["fastapi"],
            "negative_interests": [],
            "enabled_categories": ["other"],
        }
    )

    assert decision.score >= 70
    assert decision.should_push is True
    assert decision.matched_interests == ["fastapi"]
