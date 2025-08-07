"""
Season Management Service

Handles end-of-season processes including promotion/relegation and new season setup.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlmodel import Session, select

from app.core.config import settings
from app.db.models import Club, Season, Fixture
from app.services.ladder import LadderCalculator
from app.services.fixture_generator import FixtureGenerator


class SeasonManager:
    """Manages season lifecycle including promotion/relegation."""

    def __init__(self, session: Session):
        self.session = session

    def process_end_of_season(self, afl_season_id: int, vfl_season_id: int) -> Dict[str, Any]:
        """Process end-of-season promotion and relegation."""
        calculator = LadderCalculator(self.session)
        
        # Get final ladders
        afl_ladder = calculator.calculate_season_ladder(afl_season_id)
        vfl_ladder = calculator.calculate_season_ladder(vfl_season_id)

        # Identify clubs for promotion/relegation
        relegation_clubs = afl_ladder[-2:] if len(afl_ladder) >= 2 else []
        promotion_clubs = vfl_ladder[:2] if len(vfl_ladder) >= 2 else []

        changes = []

        # Process relegations (AFL to VFL)
        for entry in relegation_clubs:
            club = self.session.get(Club, entry.club_id)
            if club and club.tier == 0:
                club.tier = 1
                self.session.add(club)
                changes.append({
                    "club_id": club.id,
                    "club_name": club.name,
                    "change": "relegated",
                    "from_tier": 0,
                    "to_tier": 1,
                    "final_position": entry.position
                })

        # Process promotions (VFL to AFL)
        for entry in promotion_clubs:
            club = self.session.get(Club, entry.club_id)
            if club and club.tier == 1:
                club.tier = 0
                self.session.add(club)
                changes.append({
                    "club_id": club.id,
                    "club_name": club.name,
                    "change": "promoted",
                    "from_tier": 1,
                    "to_tier": 0,
                    "final_position": entry.position
                })

        # Mark current seasons as inactive
        afl_season = self.session.get(Season, afl_season_id)
        vfl_season = self.session.get(Season, vfl_season_id)
        
        if afl_season:
            afl_season.is_active = False
            self.session.add(afl_season)
        
        if vfl_season:
            vfl_season.is_active = False
            self.session.add(vfl_season)

        self.session.commit()

        return {
            "season_completed": True,
            "afl_season_id": afl_season_id,
            "vfl_season_id": vfl_season_id,
            "changes": changes,
            "summary": {
                "clubs_relegated": len([c for c in changes if c["change"] == "relegated"]),
                "clubs_promoted": len([c for c in changes if c["change"] == "promoted"])
            }
        }

    def create_new_season(self, year: int, generate_fixtures: bool = True) -> Dict[str, Any]:
        """Create new AFL and VFL seasons for the given year."""
        # Create AFL season
        afl_season = Season(
            year=year,
            tier=0,
            current_round=1,
            total_rounds=settings.AFL_ROUNDS,
            is_active=True
        )
        self.session.add(afl_season)

        # Create VFL season  
        vfl_season = Season(
            year=year,
            tier=1,
            current_round=1,
            total_rounds=settings.VFL_ROUNDS,
            is_active=True
        )
        self.session.add(vfl_season)

        self.session.commit()
        self.session.refresh(afl_season)
        self.session.refresh(vfl_season)

        result = {
            "afl_season": {
                "id": afl_season.id,
                "year": afl_season.year,
                "tier": afl_season.tier,
                "total_rounds": afl_season.total_rounds
            },
            "vfl_season": {
                "id": vfl_season.id,
                "year": vfl_season.year,
                "tier": vfl_season.tier,
                "total_rounds": vfl_season.total_rounds
            },
            "fixtures_generated": False
        }

        # Generate fixtures if requested
        if generate_fixtures:
            generator = FixtureGenerator(self.session)
            
            try:
                afl_fixtures = generator.generate_season_fixtures(afl_season.id)
                vfl_fixtures = generator.generate_season_fixtures(vfl_season.id)
                
                # Save fixtures
                for fixture in afl_fixtures + vfl_fixtures:
                    self.session.add(fixture)
                
                self.session.commit()
                
                result["fixtures_generated"] = True
                result["afl_fixtures_count"] = len(afl_fixtures)
                result["vfl_fixtures_count"] = len(vfl_fixtures)
                
            except Exception as e:
                result["fixture_error"] = str(e)

        return result

    def advance_season_to_next_round(self, season_id: int) -> Dict[str, Any]:
        """Advance a season to the next round if current round is complete."""
        season = self.session.get(Season, season_id)
        if not season:
            raise ValueError(f"Season {season_id} not found")

        # Check if current round is complete
        current_round_query = select(Fixture).where(
            Fixture.season_id == season_id,
            Fixture.round == season.current_round,
            Fixture.played == False
        )
        remaining_fixtures = self.session.exec(current_round_query).all()

        if remaining_fixtures:
            return {
                "advanced": False,
                "reason": f"Round {season.current_round} has {len(remaining_fixtures)} unplayed fixtures",
                "current_round": season.current_round
            }

        # Check if season is complete
        if season.current_round >= season.total_rounds:
            return {
                "advanced": False,
                "reason": "Season is complete",
                "current_round": season.current_round,
                "season_complete": True
            }

        # Advance to next round
        season.current_round += 1
        self.session.add(season)
        self.session.commit()

        return {
            "advanced": True,
            "previous_round": season.current_round - 1,
            "current_round": season.current_round,
            "season_complete": season.current_round > season.total_rounds
        }

    def get_season_status(self, season_id: int) -> Dict[str, Any]:
        """Get comprehensive status information for a season."""
        season = self.session.get(Season, season_id)
        if not season:
            raise ValueError(f"Season {season_id} not found")

        # Count fixtures by status
        total_fixtures_query = select(Fixture).where(Fixture.season_id == season_id)
        total_fixtures = len(list(self.session.exec(total_fixtures_query).all()))

        played_fixtures_query = select(Fixture).where(
            Fixture.season_id == season_id,
            Fixture.played == True
        )
        played_fixtures = len(list(self.session.exec(played_fixtures_query).all()))

        # Current round status
        current_round_query = select(Fixture).where(
            Fixture.season_id == season_id,
            Fixture.round == season.current_round
        )
        current_round_fixtures = list(self.session.exec(current_round_query).all())
        current_round_played = len([f for f in current_round_fixtures if f.played])

        # Calculate progress
        progress_percentage = (played_fixtures / total_fixtures * 100) if total_fixtures > 0 else 0

        return {
            "season_id": season.id,
            "year": season.year,
            "tier": season.tier,
            "tier_name": "AFL" if season.tier == 0 else "VFL",
            "current_round": season.current_round,
            "total_rounds": season.total_rounds,
            "is_active": season.is_active,
            "progress": {
                "fixtures_played": played_fixtures,
                "total_fixtures": total_fixtures,
                "percentage": round(progress_percentage, 1)
            },
            "current_round_status": {
                "round": season.current_round,
                "fixtures_played": current_round_played,
                "total_fixtures": len(current_round_fixtures),
                "complete": current_round_played == len(current_round_fixtures)
            },
            "season_complete": season.current_round > season.total_rounds
        }

    def get_active_seasons(self) -> List[Dict[str, Any]]:
        """Get all currently active seasons."""
        query = select(Season).where(Season.is_active == True)
        seasons = self.session.exec(query).all()

        result = []
        for season in seasons:
            status = self.get_season_status(season.id)
            result.append(status)

        return result

    def simulate_full_season(self, season_id: int) -> Dict[str, Any]:
        """Simulate an entire season from current point to completion."""
        from app.services.simulation import SimulationService
        
        season = self.session.get(Season, season_id)
        if not season:
            raise ValueError(f"Season {season_id} not found")

        simulation_service = SimulationService(self.session)
        results = []

        # Simulate each remaining round
        for round_num in range(season.current_round, season.total_rounds + 1):
            round_result = simulation_service.simulate_round(season_id, round_num)
            if isinstance(round_result, dict) and "matches_played" in round_result:
                results.append({
                    "round": round_num,
                    "matches_played": round_result["matches_played"]
                })

        # Get final ladder
        calculator = LadderCalculator(self.session)
        final_ladder = calculator.get_ladder_json(season_id)

        return {
            "season_id": season_id,
            "rounds_simulated": len(results),
            "simulation_results": results,
            "final_ladder": final_ladder
        }