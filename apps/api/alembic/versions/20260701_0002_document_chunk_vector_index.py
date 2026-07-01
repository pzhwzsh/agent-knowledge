"""add document chunk vector index

Revision ID: 20260701_0002
Revises: 20260629_0001
Create Date: 2026-07-01
"""
from alembic import op

revision = "20260701_0002"
down_revision = "20260629_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_cosine "
        "ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100) "
        "WHERE embedding IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_cosine")
