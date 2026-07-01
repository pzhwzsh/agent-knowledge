from sqlalchemy.orm import Session

from app.agents.github import GitHubAgent
from app.agents.lifestyle import LifestyleAgent
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


def test_mock_specialized_agents_return_structured_outputs() -> None:
    lifestyle = LifestyleAgent().run({"text": "??????"})
    github = GitHubAgent().run({"description": "A demo repo", "topics": ["python"], "stars": 42})

    assert lifestyle.worth_saving is True
    assert github.metadata["stars"] == 42
    assert github.tech_stack == ["python"]
