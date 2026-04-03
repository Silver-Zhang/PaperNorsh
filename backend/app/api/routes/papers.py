import logging
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.paper import Paper, PaperInteraction
from app.models.user import User
from app.schemas.paper import InteractionCreate, InteractionRead, PaperListItem, PaperRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/papers", tags=["papers"])

_VALID_ACTIONS = {"saved", "ignored", "highly_relevant", "none"}


@router.get("", response_model=list[PaperListItem])
def list_papers(
    source: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Paper]:
    q = db.query(Paper)
    if source:
        q = q.filter(Paper.source == source)
    if date_from:
        q = q.filter(Paper.published_date >= date_from)
    if date_to:
        q = q.filter(Paper.published_date <= date_to)
    if keyword:
        term = f"%{keyword.lower()}%"
        q = q.filter(
            or_(
                Paper.title.ilike(term),
                Paper.abstract.ilike(term),
            )
        )
    offset = (page - 1) * per_page
    return q.order_by(Paper.published_date.desc().nullslast()).offset(offset).limit(per_page).all()


@router.get("/saved", response_model=list[PaperListItem])
def saved_papers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Paper]:
    interactions = (
        db.query(PaperInteraction)
        .filter(
            PaperInteraction.user_id == current_user.id,
            PaperInteraction.action == "saved",
        )
        .all()
    )
    paper_ids = [i.paper_id for i in interactions]
    return db.query(Paper).filter(Paper.id.in_(paper_ids)).all()


@router.get("/ignored", response_model=list[PaperListItem])
def ignored_papers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Paper]:
    interactions = (
        db.query(PaperInteraction)
        .filter(
            PaperInteraction.user_id == current_user.id,
            PaperInteraction.action == "ignored",
        )
        .all()
    )
    paper_ids = [i.paper_id for i in interactions]
    return db.query(Paper).filter(Paper.id.in_(paper_ids)).all()


@router.get("/{paper_id}", response_model=PaperRead)
def get_paper(paper_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Paper:
    paper = db.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return paper


@router.post("/{paper_id}/interact", status_code=status.HTTP_200_OK)
def interact_with_paper(
    paper_id: uuid.UUID,
    payload: InteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response | PaperInteraction:
    if payload.action not in _VALID_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"action must be one of {sorted(_VALID_ACTIONS)}",
        )
    paper = db.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    interaction = (
        db.query(PaperInteraction)
        .filter(
            PaperInteraction.user_id == current_user.id,
            PaperInteraction.paper_id == paper_id,
        )
        .first()
    )

    if payload.action == "none":
        if interaction:
            db.delete(interaction)
            db.commit()
            logger.info("User %s removed interaction with paper %s", current_user.id, paper_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if interaction:
        interaction.action = payload.action
        interaction.updated_at = datetime.now(timezone.utc)
    else:
        interaction = PaperInteraction(
            user_id=current_user.id,
            paper_id=paper_id,
            action=payload.action,
        )
        db.add(interaction)

    db.commit()
    db.refresh(interaction)
    logger.info("User %s marked paper %s as %s", current_user.id, paper_id, payload.action)
    return interaction
