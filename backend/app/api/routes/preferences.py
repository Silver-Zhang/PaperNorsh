import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.preference import UserPreference
from app.models.user import User
from app.schemas.preference import PreferenceRead, PreferenceUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("", response_model=PreferenceRead)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreference:
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if pref is None:
        # Auto-create default preferences on first access
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("", response_model=PreferenceRead)
def upsert_preferences(
    payload: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreference:
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if pref is None:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pref, field, value)
    pref.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(pref)
    logger.info("Preferences updated for user %s", current_user.id)
    return pref
