from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db.database import get_session
from app.db.models import Club, Fixture
from app.services.simulation import SimulationService

router = APIRouter()


class SimulateMatchRequest(BaseModel):
    home_id: int
    away_id: int


class SimulateRoundRequest(BaseModel):
    season_id: int
    round: int


@router.post("/simulate")
async def simulate_match(
    request: SimulateMatchRequest,
    session: Session = Depends(get_session)
):
    """Simulate a single match between two clubs."""
    home_club = session.get(Club, request.home_id)
    away_club = session.get(Club, request.away_id)
    
    if not home_club or not away_club:
        raise HTTPException(status_code=404, detail="One or both clubs not found")
    
    # TODO: Implement actual simulation logic
    simulation_service = SimulationService(session)
    result = simulation_service.simulate_match(home_club, away_club)
    
    return result


@router.post("/simulate-round")
async def simulate_round(
    request: SimulateRoundRequest,
    session: Session = Depends(get_session)
):
    """Simulate all matches in a round."""
    simulation_service = SimulationService(session)
    results = simulation_service.simulate_round(request.season_id, request.round)
    
    return results


@router.get("/{fixture_id}")
async def get_match_result(
    fixture_id: int,
    session: Session = Depends(get_session)
):
    """Get the result of a specific match."""
    fixture = session.get(Fixture, fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    return fixture