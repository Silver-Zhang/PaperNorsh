import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.digest import DailyDigest
from app.models.user import User
from app.schemas.digest import DigestListItem, DigestRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/digest", tags=["digest"])


@router.get("/today", response_model=DigestRead)
def today_digest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyDigest:
    today = date.today()
    digest = (
        db.query(DailyDigest)
        .filter(DailyDigest.user_id == current_user.id, DailyDigest.date == today)
        .first()
    )
    if digest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No digest found for today. Trigger one via POST /api/digest/trigger.",
        )
    return digest


@router.get("/history", response_model=list[DigestListItem])
def digest_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    offset = (page - 1) * per_page
    digests = (
        db.query(DailyDigest)
        .filter(DailyDigest.user_id == current_user.id)
        .order_by(DailyDigest.date.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )
    # Attach paper_count derived field
    result = []
    for d in digests:
        result.append(
            {
                "id": d.id,
                "date": d.date,
                "status": d.status,
                "paper_count": len(d.papers) if d.papers else 0,
                "email_sent_at": d.email_sent_at,
                "created_at": d.created_at,
            }
        )
    return result


@router.post("/trigger", response_model=DigestRead, status_code=status.HTTP_202_ACCEPTED)
def trigger_digest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyDigest:
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manual trigger not allowed in production",
        )
    from app.tasks.pipeline import generate_user_digest

    digest = generate_user_digest(current_user.id, db)
    logger.info("Manually triggered digest for user %s", current_user.id)
    return digest
