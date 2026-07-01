from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.preferences import PreferenceResponse, PreferenceUpdateRequest
from app.services.preferences import PreferenceService

router = APIRouter()


@router.get("", response_model=PreferenceResponse)
def get_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return PreferenceService(db).get_for_user(current_user.id)


@router.put("", response_model=PreferenceResponse)
def update_preferences(
    payload: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PreferenceService(db).update_for_user(current_user.id, payload)
