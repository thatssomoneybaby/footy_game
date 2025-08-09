from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import Club

router = APIRouter()


@router.get("/")
async def get_clubs(
    tier: int = None,
    session: Session = Depends(get_session)
):
    """Get all clubs, optionally filtered by tier."""
    query = select(Club)
    if tier is not None:
        query = query.where(Club.tier == tier)
    
    clubs = session.exec(query).all()
    
    return {
        "clubs": clubs,
        "total": len(clubs)
    }


@router.get("/{club_id}", response_model=Club)
async def get_club(
    club_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific club by ID."""
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@router.get("/{club_id}/roster")
async def get_club_roster(
    club_id: int,
    session: Session = Depends(get_session)
):
    """Get all players for a specific club."""
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    return club.players