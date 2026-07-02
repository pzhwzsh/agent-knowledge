from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
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

    def delete_expired(self, *, before: datetime, limit: int = 500) -> int:
        expired_ids = list(
            self.db.scalars(
                select(RevokedToken.id)
                .where(RevokedToken.expires_at < before)
                .order_by(RevokedToken.expires_at.asc())
                .limit(limit)
            )
        )
        if not expired_ids:
            return 0
        result = self.db.execute(delete(RevokedToken).where(RevokedToken.id.in_(expired_ids)))
        self.db.flush()
        return int(result.rowcount or 0)
