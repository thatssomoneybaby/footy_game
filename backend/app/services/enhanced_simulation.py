import random
from typing import Dict, Any, List, Tuple
from sqlmodel import Session, select

from app.db.models import Club, Player, Position, GOAL_POINTS, BEHIND_POINTS


class EnhancedSimulationEngine:
    """
    Enhanced AFL match simulation that considers:
    - Player attributes and ratings
    - Team composition and strategy
    - Home ground advantage
    - Form and morale
    """
    
    def __init__(self, session: Session):
        self.session = session
        
    def simulate_match(self, home_club: Club, away_club: Club) -> Dict[str, Any]:
        """Simulate a match between two clubs using player attributes."""
        
        # Get team rosters
        home_players = self._get_available_players(home_club.id)
        away_players = self._get_available_players(away_club.id)
        
        # Calculate team ratings
        home_ratings = self._calculate_team_ratings(home_players)
        away_ratings = self._calculate_team_ratings(away_players)
        
        # Apply home ground advantage (small boost to home team)
        home_ratings = self._apply_home_advantage(home_ratings)
        
        # Simulate the match
        home_score, away_score = self._simulate_match_engine(
            home_ratings, away_ratings, home_club.name, away_club.name
        )
        
        # Generate match statistics
        home_goals = home_score // GOAL_POINTS
        home_behinds = home_score % GOAL_POINTS
        away_goals = away_score // GOAL_POINTS
        away_behinds = away_score % GOAL_POINTS
        
        # Determine winner
        if home_score > away_score:
            winner = home_club.name
        elif away_score > home_score:
            winner = away_club.name
        else:
            winner = "Draw"
        
        return {
            "home_club": home_club.name,
            "away_club": away_club.name,
            "home_score": home_score,
            "away_score": away_score,
            "home_goals": home_goals,
            "home_behinds": home_behinds,
            "away_goals": away_goals,
            "away_behinds": away_behinds,
            "winner": winner,
            "home_ratings": home_ratings,
            "away_ratings": away_ratings
        }
    
    def _get_available_players(self, club_id: int) -> List[Player]:
        """Get all available (not injured/suspended) players for a club."""
        query = select(Player).where(
            Player.club_id == club_id,
            Player.injured == False,
            Player.suspended == False
        )
        return list(self.session.exec(query).all())
    
    def _calculate_team_ratings(self, players: List[Player]) -> Dict[str, float]:
        """Calculate overall team ratings based on player attributes."""
        if not players:
            return self._default_ratings()
        
        # Group players by position
        forwards = [p for p in players if p.position in [Position.KPF, Position.SMALL_FWD]]
        midfielders = [p for p in players if p.position == Position.MID]
        defenders = [p for p in players if p.position in [Position.HALF_BACK, Position.KP_BACK]]
        rucks = [p for p in players if p.position == Position.RUCK]
        utility = [p for p in players if p.position == Position.UTILITY]
        
        # Calculate positional ratings
        attack_rating = self._calculate_attack_rating(forwards + utility[:2])
        midfield_rating = self._calculate_midfield_rating(midfielders + utility[2:4])
        defense_rating = self._calculate_defense_rating(defenders + utility[4:6])
        ruck_rating = self._calculate_ruck_rating(rucks + utility[6:])
        
        # Overall team rating
        overall_rating = (attack_rating + midfield_rating + defense_rating + ruck_rating) / 4
        
        # Team chemistry (based on leadership and morale)
        chemistry = self._calculate_team_chemistry(players)
        
        return {
            "attack": attack_rating,
            "midfield": midfield_rating,
            "defense": defense_rating,
            "ruck": ruck_rating,
            "overall": overall_rating,
            "chemistry": chemistry,
            "depth": len(players)  # Squad depth affects consistency
        }
    
    def _calculate_attack_rating(self, forwards: List[Player]) -> float:
        """Calculate team's attacking rating."""
        if not forwards:
            return 50.0  # Default mediocre rating
        
        # Focus on marking, kicking, and speed for forwards
        total_rating = sum(
            (player.marking + player.kicking + player.speed + player.composure) / 4 
            * (1 + player.morale * 0.02)  # Morale affects performance
            for player in forwards
        )
        return min(100.0, total_rating / len(forwards))
    
    def _calculate_midfield_rating(self, midfielders: List[Player]) -> float:
        """Calculate team's midfield rating."""
        if not midfielders:
            return 50.0
        
        # Midfielders need good all-round skills
        total_rating = sum(
            (player.kicking + player.handball + player.endurance + 
             player.decision_making + player.speed) / 5
            * (1 + player.morale * 0.02)
            for player in midfielders
        )
        return min(100.0, total_rating / len(midfielders))
    
    def _calculate_defense_rating(self, defenders: List[Player]) -> float:
        """Calculate team's defensive rating."""
        if not defenders:
            return 50.0
        
        # Defenders need spoiling, marking, and decision making
        total_rating = sum(
            (player.spoiling + player.marking + player.strength + 
             player.decision_making) / 4
            * (1 + player.morale * 0.02)
            for player in defenders
        )
        return min(100.0, total_rating / len(defenders))
    
    def _calculate_ruck_rating(self, rucks: List[Player]) -> float:
        """Calculate team's ruck rating."""
        if not rucks:
            return 50.0
        
        # Rucks need ruck_work, strength, and marking
        total_rating = sum(
            (player.ruck_work + player.strength + player.marking + player.endurance) / 4
            * (1 + player.morale * 0.02)
            for player in rucks
        )
        return min(100.0, total_rating / len(rucks))
    
    def _calculate_team_chemistry(self, players: List[Player]) -> float:
        """Calculate team chemistry based on leadership and morale."""
        if not players:
            return 50.0
        
        avg_leadership = sum(p.leadership for p in players) / len(players)
        avg_morale = sum(p.morale for p in players) / len(players)
        
        # Chemistry affects how well the team plays together
        chemistry = (avg_leadership + (avg_morale + 5) * 10) / 2  # Scale morale to 0-100
        return min(100.0, max(0.0, chemistry))
    
    def _apply_home_advantage(self, ratings: Dict[str, float]) -> Dict[str, float]:
        """Apply small home ground advantage."""
        home_boost = 1.05  # 5% boost for home team
        
        return {
            key: min(100.0, value * home_boost) if key != 'depth' else value
            for key, value in ratings.items()
        }
    
    def _simulate_match_engine(self, home_ratings: Dict[str, float], away_ratings: Dict[str, float],
                             home_name: str, away_name: str) -> Tuple[int, int]:
        """Core match simulation engine using team ratings."""
        
        # Calculate team strengths (0.0 to 1.0)
        home_strength = home_ratings["overall"] / 100.0
        away_strength = away_ratings["overall"] / 100.0
        
        # Apply chemistry multiplier
        home_strength *= (home_ratings["chemistry"] / 100.0 * 0.2 + 0.8)  # 80-100% based on chemistry
        away_strength *= (away_ratings["chemistry"] / 100.0 * 0.2 + 0.8)
        
        # Expected scores based on team strength
        # AFL average is roughly 80-120 points per team
        base_score = 85
        strength_variance = 35
        
        home_expected = base_score + (home_strength - 0.5) * strength_variance
        away_expected = base_score + (away_strength - 0.5) * strength_variance
        
        # Add randomness (football is unpredictable!)
        random_factor = 0.3  # 30% randomness, 70% skill
        
        home_score = int(
            home_expected * (1 - random_factor) + 
            random.randint(60, 140) * random_factor
        )
        away_score = int(
            away_expected * (1 - random_factor) + 
            random.randint(60, 140) * random_factor
        )
        
        # Ensure realistic AFL score ranges
        home_score = max(30, min(200, home_score))
        away_score = max(30, min(200, away_score))
        
        return home_score, away_score
    
    def _default_ratings(self) -> Dict[str, float]:
        """Default ratings when no players available."""
        return {
            "attack": 50.0,
            "midfield": 50.0,
            "defense": 50.0,
            "ruck": 50.0,
            "overall": 50.0,
            "chemistry": 50.0,
            "depth": 22
        }
    
    def get_team_form_summary(self, club_id: int) -> Dict[str, Any]:
        """Get a summary of team form and key players."""
        players = self._get_available_players(club_id)
        ratings = self._calculate_team_ratings(players)
        
        # Find key players (highest rated in each position)
        key_players = self._identify_key_players(players)
        
        # Injury concerns
        all_players = list(self.session.exec(
            select(Player).where(Player.club_id == club_id)
        ))
        injured_players = [p for p in all_players if p.injured or p.suspended]
        
        return {
            "ratings": ratings,
            "key_players": key_players,
            "injuries": len(injured_players),
            "squad_size": len(players),
            "form_summary": self._get_form_description(ratings["overall"])
        }
    
    def _identify_key_players(self, players: List[Player]) -> Dict[str, str]:
        """Identify the best player in each position."""
        if not players:
            return {}
        
        # Find best players by position
        best_players = {}
        positions = {
            "Forward": [Position.KPF, Position.SMALL_FWD],
            "Midfielder": [Position.MID],
            "Defender": [Position.HALF_BACK, Position.KP_BACK],
            "Ruck": [Position.RUCK]
        }
        
        for pos_group, positions_list in positions.items():
            group_players = [p for p in players if p.position in positions_list]
            if group_players:
                # Rate players based on their position requirements
                if pos_group == "Forward":
                    best = max(group_players, key=lambda p: (p.marking + p.kicking + p.speed) / 3)
                elif pos_group == "Midfielder":
                    best = max(group_players, key=lambda p: (p.kicking + p.handball + p.endurance + p.decision_making) / 4)
                elif pos_group == "Defender":
                    best = max(group_players, key=lambda p: (p.spoiling + p.marking + p.strength) / 3)
                else:  # Ruck
                    best = max(group_players, key=lambda p: (p.ruck_work + p.strength + p.marking) / 3)
                
                best_players[pos_group] = best.name
        
        return best_players
    
    def _get_form_description(self, overall_rating: float) -> str:
        """Convert overall rating to descriptive form."""
        if overall_rating >= 85:
            return "Excellent"
        elif overall_rating >= 75:
            return "Very Good"
        elif overall_rating >= 65:
            return "Good"
        elif overall_rating >= 55:
            return "Average"
        elif overall_rating >= 45:
            return "Below Average"
        else:
            return "Poor"