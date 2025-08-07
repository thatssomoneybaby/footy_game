import random
from typing import Dict, Any, List

from sqlmodel import Session, select

from app.db.models import Club, Fixture, Season, MatchStat, GOAL_POINTS, BEHIND_POINTS


class SimulationService:
    def __init__(self, session: Session):
        self.session = session

    def simulate_match(self, home_club: Club, away_club: Club) -> Dict[str, Any]:
        """Simulate a single match between two clubs."""
        # Basic simulation - replace with more sophisticated engine later
        home_goals = random.randint(8, 18)
        home_behinds = random.randint(6, 15)
        away_goals = random.randint(8, 18)
        away_behinds = random.randint(6, 15)
        
        home_score = (home_goals * GOAL_POINTS) + (home_behinds * BEHIND_POINTS)
        away_score = (away_goals * GOAL_POINTS) + (away_behinds * BEHIND_POINTS)
        
        result = {
            "home_club": home_club.name,
            "away_club": away_club.name,
            "home_score": home_score,
            "away_score": away_score,
            "home_goals": home_goals,
            "home_behinds": home_behinds,
            "away_goals": away_goals,
            "away_behinds": away_behinds,
            "winner": home_club.name if home_score > away_score else away_club.name if away_score > home_score else "Draw"
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