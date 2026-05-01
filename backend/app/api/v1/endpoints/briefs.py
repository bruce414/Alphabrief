from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.brief import BriefCreate, BriefResponse
from app.services import brief_service

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.post("", response_model=BriefResponse, status_code=status.HTTP_201_CREATED)
def create_brief(
    data: BriefCreate,
    db: Session = Depends(get_db),
) -> BriefResponse:
    brief = brief_service.create_brief(db, data)
    return BriefResponse.model_validate(brief)


@router.get("", response_model=list[BriefResponse])
def list_briefs(
    db: Session = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BriefResponse]:
    briefs = brief_service.list_briefs(db, limit=limit, offset=offset)
    return [BriefResponse.model_validate(b) for b in briefs]


@router.get("/{brief_id}", response_model=BriefResponse)
def get_brief(
    brief_id: UUID,
    db: Session = Depends(get_db),
) -> BriefResponse:
    brief = brief_service.get_brief_by_id(db, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Brief not found")
    return BriefResponse.model_validate(brief)
