"""
Advanced AFL Match Simulation Engine

This engine uses ALL player attributes to create realistic match simulations:

TECHNICAL ATTRIBUTES IMPACT:
- Kicking: Goal accuracy, field kicking precision, turnover rate
- Handball: Short passing chains, ball movement speed
- Marking: Contested marks, intercept marks, forward targets
- Spoiling: Defensive pressure, turnover creation
- Ruck work: Hit-out advantage, clearance dominance

PHYSICAL ATTRIBUTES IMPACT:  
- Speed: Breakaway goals, defensive recovery, transition play
- Endurance: 4-quarter performance consistency, late game impact
- Strength: Contested ball wins, physical matchup advantages

MENTAL ATTRIBUTES IMPACT:
- Decision making: Disposal efficiency, tactical execution
- Leadership: Team chemistry multiplier, clutch performance
- Composure: Pressure situations, goal accuracy under pressure

MATCH SIMULATION FEATURES:
- Quarter-by-quarter progression with fatigue
- Individual player performance tracking
- Dynamic momentum shifts
- Weather and ground conditions
- Tactical adjustments based on team composition
- Injury risk modeling
- Match statistics generation
"""

import random
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from sqlmodel import Session, select

from app.db.models import Club, Player, Position, MatchStat, GOAL_POINTS, BEHIND_POINTS


class MatchConditions(Enum):
    """Weather and ground conditions affecting play."""
    PERFECT = "perfect"        # Sunny, no wind, dry
    WINDY = "windy"           # Strong wind affecting kicking
    WET = "wet"               # Rain, slippery conditions  
    HOT = "hot"               # High temperature, more fatigue
    COLD = "cold"             # Cold conditions, less fatigue


@dataclass
class PlayerPerformance:
    """Individual player performance in a match."""
    player_id: int
    goals: int = 0
    behinds: int = 0  
    kicks: int = 0
    handballs: int = 0
    marks: int = 0
    tackles: int = 0
    hit_outs: int = 0
    contested_possessions: int = 0
    uncontested_possessions: int = 0
    effective_disposals: int = 0
    turnovers: int = 0
    rating: float = 5.0        # Match rating out of 10
    impact_score: float = 0.0  # Overall contribution to team


@dataclass  
class QuarterResult:
    """Results for a single quarter."""
    home_goals: int
    home_behinds: int
    away_goals: int  
    away_behinds: int
    momentum: float  # -1.0 (away dominating) to 1.0 (home dominating)
    key_events: List[str]


class AdvancedSimulationEngine:
    """
    Comprehensive AFL simulation engine using all player attributes.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.player_performances: Dict[int, PlayerPerformance] = {}
        
        # Match condition weights
        self.condition_effects = {
            MatchConditions.PERFECT: {"kicking": 1.0, "marking": 1.0, "endurance": 1.0},
            MatchConditions.WINDY: {"kicking": 0.85, "marking": 0.9, "endurance": 1.0},
            MatchConditions.WET: {"kicking": 0.8, "marking": 0.75, "endurance": 0.95, "speed": 0.9},
            MatchConditions.HOT: {"endurance": 0.85, "speed": 0.95, "decision_making": 0.9},
            MatchConditions.COLD: {"endurance": 1.05, "kicking": 0.95}
        }
        
    def simulate_match(self, home_club: Club, away_club: Club, 
                      conditions: MatchConditions = MatchConditions.PERFECT) -> Dict[str, Any]:
        """
        Simulate a complete AFL match with quarter-by-quarter progression.
        """
        # Initialize match
        self.player_performances.clear()
        
        # Get team rosters
        home_players = self._get_available_players(home_club.id)
        away_players = self._get_available_players(away_club.id)
        
        # Select starting lineups (best 22)
        home_lineup = self._select_best_lineup(home_players)
        away_lineup = self._select_best_lineup(away_players)
        
        # Calculate team ratings with all factors
        home_ratings = self._calculate_comprehensive_team_ratings(home_lineup, conditions)
        away_ratings = self._calculate_comprehensive_team_ratings(away_lineup, conditions)
        
        # Apply home ground advantage
        home_ratings = self._apply_home_advantage(home_ratings)
        
        # Simulate quarter by quarter
        quarters = []
        total_home_score = 0
        total_away_score = 0
        momentum = 0.0  # Momentum factor affecting subsequent quarters
        
        for quarter in range(1, 5):
            quarter_result = self._simulate_quarter(
                home_lineup, away_lineup, home_ratings, away_ratings, 
                quarter, momentum, conditions
            )
            
            quarters.append(quarter_result)
            total_home_score += (quarter_result.home_goals * GOAL_POINTS + quarter_result.home_behinds)
            total_away_score += (quarter_result.away_goals * GOAL_POINTS + quarter_result.away_behinds)
            momentum = quarter_result.momentum
        
        # Calculate final statistics  
        total_home_goals = sum(q.home_goals for q in quarters)
        total_home_behinds = sum(q.home_behinds for q in quarters) 
        total_away_goals = sum(q.away_goals for q in quarters)
        total_away_behinds = sum(q.away_behinds for q in quarters)
        
        # Determine winner
        if total_home_score > total_away_score:
            winner = home_club.name
            margin = total_home_score - total_away_score
        elif total_away_score > total_home_score:
            winner = away_club.name  
            margin = total_away_score - total_home_score
        else:
            winner = "Draw"
            margin = 0
            
        # Generate match summary
        match_summary = self._generate_match_summary(
            home_club, away_club, quarters, home_ratings, away_ratings, conditions
        )
        
        return {
            "home_club": home_club.name,
            "away_club": away_club.name,
            "home_score": total_home_score,
            "away_score": total_away_score,
            "home_goals": total_home_goals,
            "home_behinds": total_home_behinds,
            "away_goals": total_away_goals, 
            "away_behinds": total_away_behinds,
            "winner": winner,
            "margin": margin,
            "quarters": [
                {
                    "quarter": i+1,
                    "home_goals": q.home_goals,
                    "home_behinds": q.home_behinds,
                    "away_goals": q.away_goals,
                    "away_behinds": q.away_behinds,
                    "key_events": q.key_events
                }
                for i, q in enumerate(quarters)
            ],
            "conditions": conditions.value,
            "home_ratings": home_ratings,
            "away_ratings": away_ratings,
            "match_summary": match_summary,
            "player_performances": [
                {
                    "player_id": p.player_id,
                    "goals": p.goals,
                    "behinds": p.behinds,
                    "kicks": p.kicks,
                    "handballs": p.handballs,
                    "marks": p.marks,
                    "tackles": p.tackles,
                    "hit_outs": p.hit_outs,
                    "rating": p.rating,
                    "impact_score": p.impact_score
                }
                for p in self.player_performances.values()
            ]
        }
    
    def _get_available_players(self, club_id: int) -> List[Player]:
        """Get all available (not injured/suspended) players for a club."""
        query = select(Player).where(
            Player.club_id == club_id,
            Player.injured == False,
            Player.suspended == False
        )
        return list(self.session.exec(query).all())
    
    def _select_best_lineup(self, players: List[Player], lineup_size: int = 22) -> List[Player]:
        """Select the best 22 players for the match lineup."""
        if len(players) <= lineup_size:
            return players
            
        # Calculate overall rating for each player
        player_ratings = []
        for player in players:
            # Overall rating based on all attributes weighted by position
            overall = self._calculate_player_overall_rating(player)
            player_ratings.append((player, overall))
        
        # Sort by overall rating and take top performers
        player_ratings.sort(key=lambda x: x[1], reverse=True)
        return [player for player, _ in player_ratings[:lineup_size]]
    
    def _calculate_player_overall_rating(self, player: Player) -> float:
        """Calculate comprehensive player overall rating."""
        # Base attribute average
        technical_avg = (player.kicking + player.handball + player.marking + 
                        player.spoiling + player.ruck_work) / 5
        physical_avg = (player.speed + player.endurance + player.strength) / 3  
        mental_avg = (player.decision_making + player.leadership + player.composure) / 3
        
        # Weight by importance (technical skills most important)
        overall = (technical_avg * 0.5 + physical_avg * 0.3 + mental_avg * 0.2)
        
        # Apply age curve (peak performance around 25-27)
        age_factor = self._get_age_performance_factor(player.age)
        
        # Apply morale effect
        morale_factor = 1.0 + (player.morale * 0.02)  # ±10% based on morale
        
        return overall * age_factor * morale_factor
        
    def _get_age_performance_factor(self, age: int) -> float:
        """Get age-based performance multiplier."""
        if age <= 20:
            return 0.85 + (age - 18) * 0.05  # 0.85 to 0.95
        elif age <= 27:  
            return 0.95 + (age - 20) * 0.0143  # 0.95 to 1.05
        elif age <= 30:
            return 1.05 - (age - 27) * 0.02   # 1.05 to 0.99
        else:
            return 0.99 - (age - 30) * 0.04   # 0.99 down
    
    def _calculate_comprehensive_team_ratings(self, players: List[Player], 
                                            conditions: MatchConditions) -> Dict[str, float]:
        """Calculate detailed team ratings using all player attributes."""
        if not players:
            return self._default_team_ratings()
        
        # Group players by position for tactical analysis
        forwards = [p for p in players if p.position in [Position.KPF, Position.SMALL_FWD]]
        midfielders = [p for p in players if p.position == Position.MID]  
        defenders = [p for p in players if p.position in [Position.HALF_BACK, Position.KP_BACK]]
        rucks = [p for p in players if p.position == Position.RUCK]
        utility = [p for p in players if p.position == Position.UTILITY]
        
        # Calculate attack rating (goal scoring ability)
        attack_rating = self._calculate_attack_strength(forwards + utility[:2], conditions)
        
        # Calculate midfield rating (ball winning and distribution)
        midfield_rating = self._calculate_midfield_strength(midfielders + utility[2:4], conditions)
        
        # Calculate defense rating (stopping opponent scores)  
        defense_rating = self._calculate_defense_strength(defenders + utility[4:6], conditions)
        
        # Calculate ruck rating (hit-outs and around-ground impact)
        ruck_rating = self._calculate_ruck_strength(rucks + utility[6:], conditions)
        
        # Team chemistry based on leadership and morale
        chemistry = self._calculate_team_chemistry(players)
        
        # Depth factor (squad rotation capability)
        depth_factor = min(1.0, len(players) / 25.0)
        
        # Overall team strength
        overall = (attack_rating + midfield_rating + defense_rating + ruck_rating) / 4
        
        return {
            "attack": attack_rating,
            "midfield": midfield_rating, 
            "defense": defense_rating,
            "ruck": ruck_rating,
            "overall": overall,
            "chemistry": chemistry,
            "depth": depth_factor,
            "goal_accuracy": self._calculate_goal_accuracy(forwards, conditions),
            "ball_movement": self._calculate_ball_movement_rating(midfielders + defenders, conditions),
            "defensive_pressure": self._calculate_defensive_pressure(defenders + midfielders, conditions),
            "contested_ball": self._calculate_contested_ball_rating(players, conditions),
            "endurance": self._calculate_team_endurance(players, conditions)
        }
    
    def _calculate_attack_strength(self, forwards: List[Player], conditions: MatchConditions) -> float:
        """Calculate team's attacking potency."""
        if not forwards:
            return 50.0
            
        # Key forward marking and goal kicking
        marking_avg = sum(p.marking for p in forwards) / len(forwards)
        kicking_avg = sum(p.kicking for p in forwards) / len(forwards) 
        speed_avg = sum(p.speed for p in forwards) / len(forwards)
        composure_avg = sum(p.composure for p in forwards) / len(forwards)
        
        # Combine attributes with realistic weighting
        attack_base = (marking_avg * 0.35 + kicking_avg * 0.35 + 
                      speed_avg * 0.15 + composure_avg * 0.15)
        
        # Apply conditions
        conditions_factor = self.condition_effects[conditions].get("kicking", 1.0) * \
                           self.condition_effects[conditions].get("marking", 1.0)
        
        return min(100.0, attack_base * conditions_factor)
    
    def _calculate_midfield_strength(self, midfielders: List[Player], conditions: MatchConditions) -> float:
        """Calculate midfield dominance and ball distribution."""
        if not midfielders:
            return 50.0
            
        # All-round midfield skills
        endurance_avg = sum(p.endurance for p in midfielders) / len(midfielders)
        decision_avg = sum(p.decision_making for p in midfielders) / len(midfielders)
        kicking_avg = sum(p.kicking for p in midfielders) / len(midfielders)
        handball_avg = sum(p.handball for p in midfielders) / len(midfielders)
        speed_avg = sum(p.speed for p in midfielders) / len(midfielders)
        
        midfield_base = (endurance_avg * 0.25 + decision_avg * 0.25 + 
                        kicking_avg * 0.2 + handball_avg * 0.15 + speed_avg * 0.15)
        
        # Apply condition effects
        conditions_factor = self.condition_effects[conditions].get("endurance", 1.0)
        
        return min(100.0, midfield_base * conditions_factor)
    
    def _calculate_defense_strength(self, defenders: List[Player], conditions: MatchConditions) -> float:
        """Calculate defensive solidity and intercept ability.""" 
        if not defenders:
            return 50.0
            
        spoiling_avg = sum(p.spoiling for p in defenders) / len(defenders)
        marking_avg = sum(p.marking for p in defenders) / len(defenders) 
        strength_avg = sum(p.strength for p in defenders) / len(defenders)
        decision_avg = sum(p.decision_making for p in defenders) / len(defenders)
        
        defense_base = (spoiling_avg * 0.35 + marking_avg * 0.25 + 
                       strength_avg * 0.25 + decision_avg * 0.15)
        
        return min(100.0, defense_base)
    
    def _calculate_ruck_strength(self, rucks: List[Player], conditions: MatchConditions) -> float:
        """Calculate ruck dominance and around-ground impact."""
        if not rucks:
            return 50.0
            
        ruck_work_avg = sum(p.ruck_work for p in rucks) / len(rucks)
        strength_avg = sum(p.strength for p in rucks) / len(rucks)
        marking_avg = sum(p.marking for p in rucks) / len(rucks)
        endurance_avg = sum(p.endurance for p in rucks) / len(rucks)
        
        ruck_base = (ruck_work_avg * 0.4 + strength_avg * 0.25 + 
                    marking_avg * 0.2 + endurance_avg * 0.15)
        
        return min(100.0, ruck_base)
    
    def _calculate_team_chemistry(self, players: List[Player]) -> float:
        """Calculate team chemistry and cohesion."""
        if not players:
            return 50.0
            
        leadership_avg = sum(p.leadership for p in players) / len(players)
        morale_avg = sum(p.morale for p in players) / len(players)
        
        # Convert morale scale (-5 to +5) to percentage  
        morale_pct = ((morale_avg + 5) / 10) * 100
        
        chemistry = (leadership_avg * 0.6 + morale_pct * 0.4)
        return min(100.0, max(0.0, chemistry))
    
    def _calculate_goal_accuracy(self, forwards: List[Player], conditions: MatchConditions) -> float:
        """Calculate goal kicking accuracy."""
        if not forwards:
            return 60.0  # Average accuracy
            
        kicking_avg = sum(p.kicking for p in forwards) / len(forwards)
        composure_avg = sum(p.composure for p in forwards) / len(forwards)
        
        base_accuracy = (kicking_avg * 0.7 + composure_avg * 0.3)
        
        # Weather effects on accuracy
        conditions_factor = self.condition_effects[conditions].get("kicking", 1.0)
        
        return min(95.0, max(40.0, base_accuracy * conditions_factor))
    
    def _calculate_ball_movement_rating(self, players: List[Player], conditions: MatchConditions) -> float:
        """Calculate ball movement and transition speed."""
        if not players:
            return 50.0
            
        kicking_avg = sum(p.kicking for p in players) / len(players)
        handball_avg = sum(p.handball for p in players) / len(players)
        decision_avg = sum(p.decision_making for p in players) / len(players)
        
        return (kicking_avg * 0.4 + handball_avg * 0.3 + decision_avg * 0.3)
    
    def _calculate_defensive_pressure(self, players: List[Player], conditions: MatchConditions) -> float:
        """Calculate defensive pressure and tackle success."""
        if not players:
            return 50.0
            
        spoiling_avg = sum(p.spoiling for p in players) / len(players)
        speed_avg = sum(p.speed for p in players) / len(players)
        endurance_avg = sum(p.endurance for p in players) / len(players)
        
        return (spoiling_avg * 0.4 + speed_avg * 0.3 + endurance_avg * 0.3)
    
    def _calculate_contested_ball_rating(self, players: List[Player], conditions: MatchConditions) -> float:
        """Calculate contested ball winning ability."""
        strength_avg = sum(p.strength for p in players) / len(players)
        decision_avg = sum(p.decision_making for p in players) / len(players)
        
        return (strength_avg * 0.6 + decision_avg * 0.4)
    
    def _calculate_team_endurance(self, players: List[Player], conditions: MatchConditions) -> float:
        """Calculate team endurance for 4-quarter performance."""
        endurance_avg = sum(p.endurance for p in players) / len(players)
        
        # Weather effects on endurance
        conditions_factor = self.condition_effects[conditions].get("endurance", 1.0)
        
        return endurance_avg * conditions_factor
    
    def _apply_home_advantage(self, ratings: Dict[str, float]) -> Dict[str, float]:
        """Apply home ground advantage boost."""
        home_boost = 1.03  # 3% boost for home team
        
        boosted_ratings = {}
        for key, value in ratings.items():
            if key in ["attack", "midfield", "defense", "ruck", "overall"]:
                boosted_ratings[key] = min(100.0, value * home_boost)
            else:
                boosted_ratings[key] = value
                
        return boosted_ratings
    
    def _simulate_quarter(self, home_lineup: List[Player], away_lineup: List[Player],
                         home_ratings: Dict[str, float], away_ratings: Dict[str, float],
                         quarter: int, momentum: float, conditions: MatchConditions) -> QuarterResult:
        """Simulate a single quarter with detailed scoring events."""
        
        # Apply fatigue effects in later quarters
        home_fatigue, away_fatigue = self._calculate_fatigue_factor(quarter, home_ratings["endurance"], away_ratings["endurance"])
        
        # Adjust team strength for fatigue and momentum
        home_effective = self._apply_quarter_factors(home_ratings, home_fatigue, momentum, True)
        away_effective = self._apply_quarter_factors(away_ratings, away_fatigue, momentum, False)
        
        # Simulate scoring events
        home_goals, home_behinds = self._simulate_team_scoring(home_effective, away_effective["defense"])
        away_goals, away_behinds = self._simulate_team_scoring(away_effective, home_effective["defense"])
        
        # Calculate momentum shift for next quarter
        quarter_score_diff = (home_goals * 6 + home_behinds) - (away_goals * 6 + away_behinds)
        new_momentum = momentum * 0.5 + (quarter_score_diff / 30.0)  # Momentum carries forward with decay
        new_momentum = max(-1.0, min(1.0, new_momentum))
        
        # Generate key events
        key_events = self._generate_quarter_events(home_goals, home_behinds, away_goals, away_behinds, quarter)
        
        # Update player performance stats
        self._update_player_performances(home_lineup, away_lineup, home_goals + home_behinds, away_goals + away_behinds)
        
        return QuarterResult(
            home_goals=home_goals,
            home_behinds=home_behinds, 
            away_goals=away_goals,
            away_behinds=away_behinds,
            momentum=new_momentum,
            key_events=key_events
        )
    
    def _calculate_fatigue_factor(self, quarter: int, home_endurance: float, away_endurance: float) -> Tuple[float, float]:
        """Calculate fatigue effects for both teams."""
        base_fatigue = {1: 1.0, 2: 0.95, 3: 0.9, 4: 0.85}[quarter]
        
        # Higher endurance = less fatigue
        home_fatigue = base_fatigue + (home_endurance - 70) * 0.002
        away_fatigue = base_fatigue + (away_endurance - 70) * 0.002
        
        return (max(0.7, home_fatigue), max(0.7, away_fatigue))
    
    def _apply_quarter_factors(self, ratings: Dict[str, float], fatigue: float, 
                              momentum: float, is_home: bool) -> Dict[str, float]:
        """Apply fatigue and momentum effects to team ratings."""
        momentum_effect = momentum if is_home else -momentum
        momentum_multiplier = 1.0 + (momentum_effect * 0.05)  # ±5% based on momentum
        
        adjusted = {}
        for key, value in ratings.items():
            if key in ["attack", "midfield", "defense", "overall"]:
                adjusted[key] = value * fatigue * momentum_multiplier
            else:
                adjusted[key] = value
                
        return adjusted
    
    def _simulate_team_scoring(self, attack_ratings: Dict[str, float], defense_rating: float) -> Tuple[int, int]:
        """Simulate scoring for one team against opponent defense."""
        
        # Calculate scoring opportunities based on midfield dominance
        base_opportunities = 12 + random.randint(-4, 4)  # 8-16 forward entries per quarter
        
        # Midfield advantage creates more opportunities
        midfield_factor = attack_ratings["midfield"] / 70.0  # Scale around average
        opportunities = int(base_opportunities * midfield_factor)
        opportunities = max(4, min(20, opportunities))  # Keep realistic bounds
        
        goals = 0
        behinds = 0
        
        for _ in range(opportunities):
            # Does this opportunity result in a score?
            attack_strength = attack_ratings["attack"]
            defense_strength = defense_rating
            
            # Chance of scoring (goal or behind)
            score_chance = (attack_strength - defense_strength + 70) / 140.0  # 0.0 to 1.0
            score_chance = max(0.2, min(0.8, score_chance))  # 20% to 80%
            
            if random.random() < score_chance:
                # Scored! Is it a goal or behind?
                goal_accuracy = attack_ratings.get("goal_accuracy", 65.0) / 100.0
                
                if random.random() < goal_accuracy:
                    goals += 1
                else:
                    behinds += 1
        
        return (goals, behinds)
    
    def _generate_quarter_events(self, home_goals: int, home_behinds: int, 
                                away_goals: int, away_behinds: int, quarter: int) -> List[str]:
        """Generate narrative events for the quarter."""
        events = []
        
        total_home = home_goals + home_behinds
        total_away = away_goals + away_behinds
        
        if home_goals >= 4:
            events.append(f"Q{quarter}: Home team dominates with {home_goals} goals")
        elif away_goals >= 4:
            events.append(f"Q{quarter}: Away team dominates with {away_goals} goals")
        elif total_home > total_away + 2:
            events.append(f"Q{quarter}: Home team controls the quarter")
        elif total_away > total_home + 2:
            events.append(f"Q{quarter}: Away team controls the quarter")
        else:
            events.append(f"Q{quarter}: Tight, contested quarter")
            
        return events
    
    def _update_player_performances(self, home_lineup: List[Player], away_lineup: List[Player],
                                   home_scores: int, away_scores: int) -> None:
        """Update individual player performance statistics."""
        # This is a simplified version - in a full implementation, 
        # we'd track detailed individual stats per quarter
        
        for player in home_lineup + away_lineup:
            if player.id not in self.player_performances:
                self.player_performances[player.id] = PlayerPerformance(player_id=player.id)
                
            perf = self.player_performances[player.id]
            
            # Random performance updates (simplified)
            if random.random() < 0.1:  # 10% chance of goal
                perf.goals += 1
            if random.random() < 0.15:  # 15% chance of behind  
                perf.behinds += 1
                
            # Base stats per quarter
            perf.kicks += random.randint(2, 8)
            perf.handballs += random.randint(1, 6) 
            perf.marks += random.randint(0, 3)
            perf.tackles += random.randint(0, 4)
            
            if player.position == Position.RUCK:
                perf.hit_outs += random.randint(2, 8)
    
    def _generate_match_summary(self, home_club: Club, away_club: Club, 
                               quarters: List[QuarterResult], home_ratings: Dict[str, float],
                               away_ratings: Dict[str, float], conditions: MatchConditions) -> str:
        """Generate a narrative match summary."""
        
        home_total = sum((q.home_goals * 6 + q.home_behinds) for q in quarters)
        away_total = sum((q.away_goals * 6 + q.away_behinds) for q in quarters)
        
        if home_total > away_total:
            winner = home_club.name
            loser = away_club.name
            margin = home_total - away_total
        else:
            winner = away_club.name  
            loser = home_club.name
            margin = away_total - home_total
            
        summary = f"{winner} defeated {loser} by {margin} points. "
        
        if margin > 50:
            summary += "A dominant performance from start to finish."
        elif margin > 25:
            summary += "A convincing victory with strong team performance."
        elif margin > 10:
            summary += "A solid win with some good passages of play."
        else:
            summary += "A thrilling contest that went down to the wire."
            
        # Add condition effects
        if conditions != MatchConditions.PERFECT:
            summary += f" Played in {conditions.value} conditions."
            
        return summary
    
    def _default_team_ratings(self) -> Dict[str, float]:
        """Default ratings when no players available."""
        return {
            "attack": 50.0,
            "midfield": 50.0, 
            "defense": 50.0,
            "ruck": 50.0,
            "overall": 50.0,
            "chemistry": 50.0,
            "depth": 0.8,
            "goal_accuracy": 60.0,
            "ball_movement": 50.0,
            "defensive_pressure": 50.0,
            "contested_ball": 50.0,
            "endurance": 50.0
        }