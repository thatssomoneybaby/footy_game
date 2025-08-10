import random
from typing import Dict, Any, List

from sqlmodel import Session, select

from app.db.models import Club, Fixture, Season, MatchStat, GOAL_POINTS, BEHIND_POINTS
from app.services.advanced_simulation import AdvancedSimulationEngine, MatchConditions


class SimulationService:
    def __init__(self, session: Session):
        self.session = session
        self.advanced_engine = AdvancedSimulationEngine(session)

    def simulate_match(self, home_club: Club, away_club: Club) -> Dict[str, Any]:
        """Simulate a single match between two clubs using advanced engine."""
        
        # Randomly select match conditions to add variety
        conditions = random.choices(
            list(MatchConditions), 
            weights=[0.6, 0.15, 0.15, 0.05, 0.05],  # Perfect weather most common
            k=1
        )[0]
        
        # Use advanced simulation engine
        detailed_result = self.advanced_engine.simulate_match(home_club, away_club, conditions)
        
        # Extract basic result format for compatibility
        result = {
            "home_club": detailed_result["home_club"],
            "away_club": detailed_result["away_club"],
            "home_score": detailed_result["home_score"],
            "away_score": detailed_result["away_score"],
            "home_goals": detailed_result["home_goals"],
            "home_behinds": detailed_result["home_behinds"],
            "away_goals": detailed_result["away_goals"],
            "away_behinds": detailed_result["away_behinds"],
            "winner": detailed_result["winner"],
            "margin": detailed_result["margin"],
            "conditions": detailed_result["conditions"],
            "quarters": detailed_result["quarters"],
            "match_summary": detailed_result["match_summary"]
        }
        
        return result

    def simulate_round(self, season_id: int, round_num: int) -> List[Dict[str, Any]]:
        """Simulate all matches in a round."""
        from datetime import datetime
        
        # Get all unplayed fixtures for this round
        query = select(Fixture).where(
            Fixture.season_id == season_id,
            Fixture.round == round_num,
            Fixture.played == False
        )
        fixtures = self.session.exec(query).all()
        
        if not fixtures:
            return {"message": f"No unplayed fixtures found for round {round_num}"}
        
        results = []
        for fixture in fixtures:
            home_club = self.session.get(Club, fixture.home_id)
            away_club = self.session.get(Club, fixture.away_id)
            
            if home_club and away_club:
                # Simulate the match
                match_result = self.simulate_match(home_club, away_club)
                
                # Update the fixture
                fixture.played = True
                fixture.home_score = match_result["home_score"]
                fixture.away_score = match_result["away_score"]
                fixture.home_goals = match_result["home_goals"]
                fixture.home_behinds = match_result["home_behinds"]
                fixture.away_goals = match_result["away_goals"]
                fixture.away_behinds = match_result["away_behinds"]
                fixture.played_at = datetime.utcnow()
                
                self.session.add(fixture)
                results.append({
                    "fixture_id": fixture.id,
                    **match_result
                })
        
        # Update season current round if all games played
        season = self.session.get(Season, season_id)
        if season and round_num >= season.current_round:
            # Check if all games in this round are now played
            remaining_query = select(Fixture).where(
                Fixture.season_id == season_id,
                Fixture.round == round_num,
                Fixture.played == False
            )
            remaining_fixtures = self.session.exec(remaining_query).all()
            
            if not remaining_fixtures:
                # Round is complete, advance to next round
                season.current_round = min(round_num + 1, season.total_rounds)
                self.session.add(season)
        
        self.session.commit()
        
        # Return results with ladder update
        from app.services.ladder import LadderCalculator
        calculator = LadderCalculator(self.session)
        updated_ladder = calculator.get_ladder_json(season_id)
        
        return {
            "round": round_num,
            "season_id": season_id,
            "matches_played": len(results),
            "results": results,
            "updated_ladder": updated_ladder[:8]  # Top 8 for summary
        }

    def calculate_ladder(self, season_id: int) -> List[Dict[str, Any]]:
        """Calculate the current ladder standings for a season."""
        # TODO: Implement proper ladder calculation
        # This would involve:
        # 1. Get all played fixtures for the season
        # 2. Calculate wins, losses, draws, points for/against
        # 3. Sort by ladder points (4 for win, 2 for draw, 0 for loss)
        # 4. Handle percentage tie-breaker
        
        return []