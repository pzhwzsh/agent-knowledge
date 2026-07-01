from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.preferences import PreferenceRepository
from app.repositories.users import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.preferences = PreferenceRepository(db)

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
