from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ingestion import IngestionJobCreate, IngestionJobResponse, IngestionSubmitResponse
from app.services.ingestion_processor import IngestionProcessor
from app.services.ingestions import IngestionService

router = APIRouter()


@router.post("", response_model=IngestionSubmitResponse)
def submit_ingestion(
    payload: IngestionJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return IngestionProcessor(db).submit(current_user.id, payload)


@router.get("", response_model=list[IngestionJobResponse])
def list_ingestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return IngestionService(db).list_jobs(current_user.id, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=IngestionJobResponse)
def get_ingestion(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return IngestionService(db).get_job(current_user.id, job_id)
