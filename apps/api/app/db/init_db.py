from sqlalchemy.engine import Engine

from app import models  # noqa: F401
from app.db.base import Base


def create_preview_tables(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
