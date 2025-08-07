"""
AFL Ladder Calculation Service

Calculates ladder standings with AFL-specific rules including percentage calculation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from sqlmodel import Session, select

from app.db.models import Club, Fixture, Season


@dataclass
class LadderEntry:
    """Represents a single club's ladder position and statistics."""
    club_id: int
    club_name: str
    club_tier: int
    position: int
    games_played: int
    wins: int
    losses: int
    draws: int
    points_for: int
    points_against: int
    percentage: float
    ladder_points: int  # 4 for win, 2 for draw, 0 for loss


class LadderCalculator:
    """Calculates and manages AFL/VFL ladder standings."""

    def __init__(self, session: Session):
        self.session = session

    def calculate_season_ladder(self, season_id: int) -> List[LadderEntry]:
        """Calculate the complete ladder for a season."""
        season = self.session.get(Season, season_id)
        if not season:
            raise ValueError(f"Season {season_id} not found")

        # Get all clubs in this tier
        clubs_query = select(Club).where(Club.tier == season.tier)
        clubs = list(self.session.exec(clubs_query).all())

        # Get all played fixtures for this season
        fixtures_query = select(Fixture).where(
            Fixture.season_id == season_id,
            Fixture.played == True
        )
        fixtures = list(self.session.exec(fixtures_query).all())

        # Calculate statistics for each club
        ladder_entries = []
        for club in clubs:
            entry = self._calculate_club_statistics(club, fixtures)
            ladder_entries.append(entry)

        # Sort ladder by AFL rules
        ladder_entries.sort(key=self._ladder_sort_key, reverse=True)

        # Assign positions
        for i, entry in enumerate(ladder_entries):
            entry.position = i + 1

        return ladder_entries

    def _calculate_club_statistics(self, club: Club, fixtures: List[Fixture]) -> LadderEntry:
        """Calculate all statistics for a single club."""
        stats = {
            'games_played': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'points_for': 0,
            'points_against': 0
        }

        # Process each fixture involving this club
        for fixture in fixtures:
            if fixture.home_id == club.id:
                # Club playing at home
                stats['games_played'] += 1
                stats['points_for'] += fixture.home_score or 0
                stats['points_against'] += fixture.away_score or 0

                if fixture.home_score > fixture.away_score:
                    stats['wins'] += 1
                elif fixture.home_score < fixture.away_score:
                    stats['losses'] += 1
                else:
                    stats['draws'] += 1

            elif fixture.away_id == club.id:
                # Club playing away
                stats['games_played'] += 1
                stats['points_for'] += fixture.away_score or 0
                stats['points_against'] += fixture.home_score or 0

                if fixture.away_score > fixture.home_score:
                    stats['wins'] += 1
                elif fixture.away_score < fixture.home_score:
                    stats['losses'] += 1
                else:
                    stats['draws'] += 1

        # Calculate percentage (for ÷ against × 100)
        percentage = 100.0
        if stats['points_against'] > 0:
            percentage = (stats['points_for'] / stats['points_against']) * 100

        # Calculate ladder points (4 for win, 2 for draw, 0 for loss)
        ladder_points = (stats['wins'] * 4) + (stats['draws'] * 2)

        return LadderEntry(
            club_id=club.id,
            club_name=club.name,
            club_tier=club.tier,
            position=0,  # Will be set after sorting
            games_played=stats['games_played'],
            wins=stats['wins'],
            losses=stats['losses'],
            draws=stats['draws'],
            points_for=stats['points_for'],
            points_against=stats['points_against'],
            percentage=round(percentage, 2),
            ladder_points=ladder_points
        )

    def _ladder_sort_key(self, entry: LadderEntry) -> tuple:
        """Generate sort key for AFL ladder rules."""
        # AFL ladder sorting rules:
        # 1. Ladder points (primary)
        # 2. Percentage (tie-breaker)
        # 3. Points for (secondary tie-breaker)
        return (entry.ladder_points, entry.percentage, entry.points_for)

    def get_ladder_json(self, season_id: int) -> List[Dict[str, Any]]:
        """Get ladder in JSON-serializable format."""
        ladder = self.calculate_season_ladder(season_id)
        
        return [
            {
                'position': entry.position,
                'club_id': entry.club_id,
                'club_name': entry.club_name,
                'games_played': entry.games_played,
                'wins': entry.wins,
                'losses': entry.losses,
                'draws': entry.draws,
                'points_for': entry.points_for,
                'points_against': entry.points_against,
                'percentage': entry.percentage,
                'ladder_points': entry.ladder_points
            }
            for entry in ladder
        ]

    def get_club_position(self, season_id: int, club_id: int) -> Optional[int]:
        """Get a specific club's ladder position."""
        ladder = self.calculate_season_ladder(season_id)
        
        for entry in ladder:
            if entry.club_id == club_id:
                return entry.position
        
        return None

    def get_top_clubs(self, season_id: int, count: int = 8) -> List[LadderEntry]:
        """Get the top N clubs from the ladder."""
        ladder = self.calculate_season_ladder(season_id)
        return ladder[:count]

    def get_bottom_clubs(self, season_id: int, count: int = 2) -> List[LadderEntry]:
        """Get the bottom N clubs from the ladder."""
        ladder = self.calculate_season_ladder(season_id)
        return ladder[-count:]

    def get_finals_bracket(self, season_id: int) -> Dict[str, Any]:
        """Generate AFL finals bracket (top 8 teams)."""
        top_8 = self.get_top_clubs(season_id, 8)
        
        if len(top_8) < 8:
            return {"error": "Not enough teams for finals", "teams_available": len(top_8)}

        # AFL Finals System (4-week finals)
        return {
            "qualifying_finals": {
                "qf1": {"home": top_8[0], "away": top_8[3]},  # 1st vs 4th
                "qf2": {"home": top_8[1], "away": top_8[2]}   # 2nd vs 3rd
            },
            "elimination_finals": {
                "ef1": {"home": top_8[4], "away": top_8[7]},  # 5th vs 8th
                "ef2": {"home": top_8[5], "away": top_8[6]}   # 6th vs 7th
            },
            "note": "Winners of QF go to Preliminary Finals, losers play winners of EF"
        }

    def get_relegation_promotion_info(self, afl_season_id: int, vfl_season_id: int) -> Dict[str, Any]:
        """Get information about clubs eligible for promotion/relegation."""
        afl_ladder = self.calculate_season_ladder(afl_season_id)
        vfl_ladder = self.calculate_season_ladder(vfl_season_id)

        # Bottom 2 AFL clubs face relegation
        relegation_candidates = afl_ladder[-2:] if len(afl_ladder) >= 2 else []
        
        # Top 2 VFL clubs eligible for promotion
        promotion_candidates = vfl_ladder[:2] if len(vfl_ladder) >= 2 else []

        return {
            "relegation_zone": [
                {
                    "position": entry.position,
                    "club_name": entry.club_name,
                    "club_id": entry.club_id,
                    "ladder_points": entry.ladder_points,
                    "percentage": entry.percentage
                }
                for entry in relegation_candidates
            ],
            "promotion_zone": [
                {
                    "position": entry.position,
                    "club_name": entry.club_name,
                    "club_id": entry.club_id,
                    "ladder_points": entry.ladder_points,
                    "percentage": entry.percentage
                }
                for entry in promotion_candidates
            ]
        }

    def simulate_ladder_after_round(self, season_id: int, round_num: int) -> List[Dict[str, Any]]:
        """Get projected ladder if all fixtures up to specified round were played."""
        # This is useful for "what if" scenarios
        # For now, just return current ladder
        # TODO: Implement projection based on simulated results
        return self.get_ladder_json(season_id)