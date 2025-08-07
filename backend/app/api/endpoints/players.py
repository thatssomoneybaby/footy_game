from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import Player

router = APIRouter()


@router.get("/", response_model=List[Player])
async def get_players(
    club_id: int = None,
    position: str = None,
    session: Session = Depends(get_session)
):
    """Get all players, optionally filtered by club or position."""
    query = select(Player)
    
    if club_id is not None:
        query = query.where(Player.club_id == club_id)
    
    if position is not None:
        query = query.where(Player.position == position)
    
    players = session.exec(query).all()
    return players


@router.get("/{player_id}", response_model=Player)
async def get_player(
    player_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific player by ID."""
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player