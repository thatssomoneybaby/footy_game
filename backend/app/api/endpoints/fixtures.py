from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db.database import get_session
from app.db.models import Season, Fixture
from app.services.fixture_generator import FixtureGenerator

router = APIRouter()


class GenerateFixturesRequest(BaseModel):
    season_id: int
    regenerate: bool = False


@router.post("/generate")
async def generate_fixtures(
    request: GenerateFixturesRequest,
    session: Session = Depends(get_session)
):
    """Generate fixtures for a season."""
    generator = FixtureGenerator(session)
    
    try:
        if request.regenerate:
            fixtures = generator.regenerate_season_fixtures(request.season_id)
            action = "regenerated"
        else:
            fixtures = generator.generate_season_fixtures(request.season_id)
            
            # Save new fixtures to database
            for fixture in fixtures:
                session.add(fixture)
            session.commit()
            action = "generated"
        
        return {
            "message": f"Successfully {action} {len(fixtures)} fixtures",
            "season_id": request.season_id,
            "fixtures_count": len(fixtures),
            "action": action
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating fixtures: {str(e)}")


@router.delete("/{season_id}")
async def clear_season_fixtures(
    season_id: int,
    session: Session = Depends(get_session)
):
    """Clear all fixtures for a season."""
    generator = FixtureGenerator(session)
    
    try:
        deleted_count = generator.clear_season_fixtures(season_id)
        return {
            "message": f"Cleared {deleted_count} fixtures",
            "season_id": season_id,
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing fixtures: {str(e)}")


@router.get("/{season_id}/round/{round_num}")
async def get_round_fixtures(
    season_id: int,
    round_num: int,
    session: Session = Depends(get_session)
):
    """Get all fixtures for a specific round."""
    from sqlmodel import select
    
    season = session.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    fixtures_query = select(Fixture).where(
        Fixture.season_id == season_id,
        Fixture.round == round_num
    )
    fixtures = session.exec(fixtures_query).all()
    
    return {
        "season_id": season_id,
        "round": round_num,
        "fixtures": list(fixtures)
    }