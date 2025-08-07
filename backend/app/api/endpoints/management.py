from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db.database import get_session
from app.services.season_manager import SeasonManager

router = APIRouter()


class CreateSeasonRequest(BaseModel):
    year: int
    generate_fixtures: bool = True


class EndSeasonRequest(BaseModel):
    afl_season_id: int
    vfl_season_id: int


@router.get("/seasons/active")
async def get_active_seasons(session: Session = Depends(get_session)):
    """Get all currently active seasons."""
    manager = SeasonManager(session)
    seasons = manager.get_active_seasons()
    return {"active_seasons": seasons}


@router.get("/seasons/{season_id}/status")
async def get_season_status(
    season_id: int,
    session: Session = Depends(get_session)
):
    """Get comprehensive status for a season."""
    manager = SeasonManager(session)
    
    try:
        status = manager.get_season_status(season_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/seasons/create")
async def create_new_season(
    request: CreateSeasonRequest,
    session: Session = Depends(get_session)
):
    """Create new AFL and VFL seasons."""
    manager = SeasonManager(session)
    
    try:
        result = manager.create_new_season(request.year, request.generate_fixtures)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating season: {str(e)}")


@router.post("/seasons/{season_id}/advance")
async def advance_season(
    season_id: int,
    session: Session = Depends(get_session)
):
    """Advance season to next round if current round is complete."""
    manager = SeasonManager(session)
    
    try:
        result = manager.advance_season_to_next_round(season_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/seasons/{season_id}/simulate-full")
async def simulate_full_season(
    season_id: int,
    session: Session = Depends(get_session)
):
    """Simulate entire remaining season."""
    manager = SeasonManager(session)
    
    try:
        result = manager.simulate_full_season(season_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating season: {str(e)}")


@router.post("/seasons/end-season")
async def end_season_process(
    request: EndSeasonRequest,
    session: Session = Depends(get_session)
):
    """Process end-of-season promotion and relegation."""
    manager = SeasonManager(session)
    
    try:
        result = manager.process_end_of_season(request.afl_season_id, request.vfl_season_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing end of season: {str(e)}")


@router.post("/reset-game")
async def reset_game(session: Session = Depends(get_session)):
    """Reset the entire game - clear all data and reseed."""
    try:
        # Import here to avoid circular imports
        from app.db.models import Club, Player, Season, Fixture, MatchStat
        from sqlmodel import delete
        
        # Clear all game data
        session.exec(delete(MatchStat))
        session.exec(delete(Fixture))
        session.exec(delete(Player))
        session.exec(delete(Season))
        session.exec(delete(Club))
        session.commit()
        
        # Re-run seed data
        import subprocess
        import os
        
        # Run seed script
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        result = subprocess.run(
            ["python", "seed_data.py"], 
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Seed failed: {result.stderr}")
            
        return {
            "status": "success",
            "message": "Game reset successfully. New season ready to play!",
            "seed_output": result.stdout
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting game: {str(e)}")


@router.get("/game-status")
async def get_game_status(session: Session = Depends(get_session)):
    """Get overall game status including all active seasons."""
    manager = SeasonManager(session)
    
    active_seasons = manager.get_active_seasons()
    
    # Separate AFL and VFL seasons
    afl_seasons = [s for s in active_seasons if s["tier"] == 0]
    vfl_seasons = [s for s in active_seasons if s["tier"] == 1]
    
    return {
        "game_status": "active" if active_seasons else "no_active_seasons",
        "total_active_seasons": len(active_seasons),
        "afl_seasons": afl_seasons,
        "vfl_seasons": vfl_seasons,
        "next_actions": _get_next_actions(active_seasons)
    }


def _get_next_actions(seasons: list) -> list:
    """Determine what actions are available based on season states."""
    actions = []
    
    for season in seasons:
        if not season["current_round_status"]["complete"]:
            actions.append({
                "action": "simulate_round",
                "season_id": season["season_id"],
                "round": season["current_round"],
                "description": f"Simulate round {season['current_round']} of {season['tier_name']} season"
            })
        elif not season["season_complete"]:
            actions.append({
                "action": "advance_round", 
                "season_id": season["season_id"],
                "description": f"Advance {season['tier_name']} season to next round"
            })
        else:
            actions.append({
                "action": "end_season",
                "season_id": season["season_id"],
                "description": f"{season['tier_name']} season complete - ready for promotion/relegation"
            })
    
    # Check if both AFL and VFL seasons are complete for promotion/relegation
    afl_complete = any(s["tier"] == 0 and s["season_complete"] for s in seasons)
    vfl_complete = any(s["tier"] == 1 and s["season_complete"] for s in seasons)
    
    if afl_complete and vfl_complete:
        actions.append({
            "action": "process_promotion_relegation",
            "description": "Process end-of-season promotion and relegation"
        })
    
    return actions