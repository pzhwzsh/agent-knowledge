from sqlalchemy import JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

JsonDict = JSONB().with_variant(JSON(), "sqlite")
StringList = JSONB().with_variant(JSON(), "sqlite")
UUIDType = Uuid(as_uuid=True)
EmbeddingVector = Vector(1536).with_variant(JSON(), "sqlite")
