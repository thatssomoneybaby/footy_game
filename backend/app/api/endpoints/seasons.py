from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import Season, Fixture

router = APIRouter()


@router.get("/", response_model=List[Season])
async def get_seasons(
    tier: int = None,
    is_active: bool = None,
    session: Session = Depends(get_session)
):
    """Get all seasons, optionally filtered."""
    query = select(Season)
    
    if tier is not None:
        query = query.where(Season.tier == tier)
    
    if is_active is not None:
        query = query.where(Season.is_active == is_active)
    
    seasons = session.exec(query).all()
    return seasons


@router.get("/{season_id}", response_model=Season)
async def get_season(
    season_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific season by ID."""
    season = session.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    return season


@router.get("/{season_id}/fixtures")
async def get_season_fixtures(
    season_id: int,
    round: int = None,
    session: Session = Depends(get_session)
):
    """Get fixtures for a season, optionally filtered by round."""
    from app.db.models import Club
    
    season = session.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    query = select(Fixture).where(Fixture.season_id == season_id)
    
    if round is not None:
        query = query.where(Fixture.round == round)
    
    fixtures = session.exec(query).all()
    
    # Enrich fixtures with club information
    enriched_fixtures = []
    for fixture in fixtures:
        home_club = session.get(Club, fixture.home_id)
        away_club = session.get(Club, fixture.away_id)
        
        enriched_fixture = {
            "id": fixture.id,
            "season_id": fixture.season_id,
            "round": fixture.round,
            "home_club": {
                "id": home_club.id,
                "name": home_club.name,
                "nickname": home_club.nickname,
                "primary_colour": home_club.primary_colour,
                "secondary_colour": home_club.secondary_colour,
                "tier": home_club.tier
            },
            "away_club": {
                "id": away_club.id,
                "name": away_club.name,
                "nickname": away_club.nickname,
                "primary_colour": away_club.primary_colour,
                "secondary_colour": away_club.secondary_colour,
                "tier": away_club.tier
            },
            "played": fixture.played,
            "home_score": fixture.home_score,
            "away_score": fixture.away_score,
            "home_goals": fixture.home_goals,
            "home_behinds": fixture.home_behinds,
            "away_goals": fixture.away_goals,
            "away_behinds": fixture.away_behinds,
            "scheduled_date": fixture.scheduled_date,
            "played_at": fixture.played_at
        }
        enriched_fixtures.append(enriched_fixture)
    
    return {
        "season_id": season_id,
        "round": round,
        "fixtures_count": len(enriched_fixtures),
        "fixtures": enriched_fixtures
    }


@router.get("/{season_id}/ladder")
async def get_season_ladder(
    season_id: int,
    session: Session = Depends(get_session)
):
    """Get the current ladder for a season."""
    from app.services.ladder import LadderCalculator
    
    season = session.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    calculator = LadderCalculator(session)
    ladder = calculator.get_ladder_json(season_id)
    
    return {
        "season_id": season_id,
        "season_year": season.year,
        "tier": season.tier,
        "current_round": season.current_round,
        "ladder": ladder
    }


@router.get("/{season_id}/finals")
async def get_finals_bracket(
    season_id: int,
    session: Session = Depends(get_session)
):
    """Get the finals bracket for a season."""
    from app.services.ladder import LadderCalculator
    
    season = session.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    calculator = LadderCalculator(session)
    bracket = calculator.get_finals_bracket(season_id)
    
    return {
        "season_id": season_id,
        "finals_bracket": bracket
    }


@router.get("/{season_id}/promotion-relegation")
async def get_promotion_relegation(
    season_id: int,
    vfl_season_id: int = None,
    session: Session = Depends(get_session)
):
    """Get promotion and relegation information."""
    from app.services.ladder import LadderCalculator
    
    season = session.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    # If no VFL season specified, try to find it
    if not vfl_season_id:
        vfl_season_query = select(Season).where(
            Season.year == season.year,
            Season.tier == 1,
            Season.is_active == True
        )
        vfl_season = session.exec(vfl_season_query).first()
        if vfl_season:
            vfl_season_id = vfl_season.id
    
    if not vfl_season_id:
        raise HTTPException(status_code=400, detail="VFL season not found for promotion/relegation")
    
    calculator = LadderCalculator(session)
    
    if season.tier == 0:  # AFL season
        info = calculator.get_relegation_promotion_info(season_id, vfl_season_id)
    else:  # VFL season
        info = calculator.get_relegation_promotion_info(vfl_season_id, season_id)
    
    return {
        "afl_season_id": season_id if season.tier == 0 else vfl_season_id,
        "vfl_season_id": vfl_season_id if season.tier == 0 else season_id,
        **info
    }