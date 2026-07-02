from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_token_payload, hash_password, verify_password
from app.models.user import User
from app.repositories.preferences import PreferenceRepository
from app.repositories.tokens import RevokedTokenRepository
from app.repositories.users import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.preferences = PreferenceRepository(db)
        self.revoked_tokens = RevokedTokenRepository(db)

    def register(self, *, email: str, password: str, display_name: str | None) -> User:
        if self.users.get_by_email(email) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = self.users.create(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
        )
        self.preferences.create_default(user.id)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, *, email: str, password: str) -> str:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
        return create_access_token(str(user.id))

    def logout(self, *, token: str, user: User) -> None:
        payload = decode_token_payload(token)
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        jti = payload.get("jti")
        expires_at = payload.get("exp")
        if not isinstance(jti, str):
            return
        if self.revoked_tokens.exists(jti):
            return
        if isinstance(expires_at, (int, float)):
            expires_at_dt = datetime.fromtimestamp(expires_at, UTC)
        else:
            expires_at_dt = datetime.now(UTC)
        self.revoked_tokens.create(user_id=user.id, jti=jti, expires_at=expires_at_dt)
        self.db.commit()
