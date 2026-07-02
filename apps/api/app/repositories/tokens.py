from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.token import RevokedToken


class RevokedTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: UUID, jti: str, expires_at: datetime) -> RevokedToken:
        token = RevokedToken(user_id=user_id, jti=jti, expires_at=expires_at)
        self.db.add(token)
        self.db.flush()
        return token

    def exists(self, jti: str) -> bool:
        statement = select(RevokedToken.id).where(RevokedToken.jti == jti).limit(1)
        return self.db.scalar(statement) is not None
