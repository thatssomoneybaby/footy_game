"""
AFL Fixture Generation Service

Generates realistic AFL and VFL season fixtures with proper scheduling algorithms.
"""

import random
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any

from sqlmodel import Session, select

from app.core.config import settings
from app.db.models import Club, Season, Fixture


class FixtureGenerator:
    """Generates fixtures for AFL and VFL seasons."""

    def __init__(self, session: Session):
        self.session = session

    def generate_season_fixtures(self, season_id: int) -> List[Fixture]:
        """Generate all fixtures for a season."""
        season = self.session.get(Season, season_id)
        if not season:
            raise ValueError(f"Season {season_id} not found")

        # Get clubs for this tier
        clubs_query = select(Club).where(Club.tier == season.tier)
        clubs = list(self.session.exec(clubs_query).all())

        if len(clubs) < 2:
            raise ValueError(f"Need at least 2 clubs for tier {season.tier}")

        if season.tier == 0:
            # AFL fixture generation
            return self._generate_afl_fixtures(season, clubs)
        else:
            # VFL fixture generation
            return self._generate_vfl_fixtures(season, clubs)

    def _generate_afl_fixtures(self, season: Season, clubs: List[Club]) -> List[Fixture]:
        """Generate AFL season fixtures (22 rounds)."""
        fixtures = []
        num_clubs = len(clubs)

        if num_clubs != 18:
            # For non-standard club counts, use round-robin
            return self._generate_round_robin(season, clubs, season.total_rounds)

        # AFL-specific scheduling with 22 rounds for 18 teams
        # Each team plays 17 other teams once (17 rounds)
        # Plus 5 additional games against selected opponents

        # Round 1-17: Each team plays every other team once
        base_fixtures = self._generate_complete_round_robin(season, clubs)
        fixtures.extend(base_fixtures)

        # Rounds 18-22: Additional 5 rounds with strategic matchups
        additional_fixtures = self._generate_additional_afl_rounds(
            season, clubs, start_round=18
        )
        fixtures.extend(additional_fixtures)

        return fixtures

    def _generate_vfl_fixtures(self, season: Season, clubs: List[Club]) -> List[Fixture]:
        """Generate VFL season fixtures."""
        # VFL typically has fewer rounds - use round-robin approach
        return self._generate_round_robin(season, clubs, season.total_rounds)

    def _generate_complete_round_robin(self, season: Season, clubs: List[Club]) -> List[Fixture]:
        """Generate complete round-robin tournament (each team plays every other once)."""
        fixtures = []
        num_clubs = len(clubs)
        
        # Use round-robin tournament algorithm
        if num_clubs % 2 != 0:
            # Add a "bye" for odd number of teams
            clubs = clubs + [None]
            num_clubs += 1

        for round_num in range(1, num_clubs):
            round_fixtures = []
            
            for i in range(num_clubs // 2):
                home_idx = i
                away_idx = num_clubs - 1 - i
                
                if clubs[home_idx] is not None and clubs[away_idx] is not None:
                    # Alternate home/away for fairness
                    if round_num % 2 == 0:
                        home_club, away_club = clubs[away_idx], clubs[home_idx]
                    else:
                        home_club, away_club = clubs[home_idx], clubs[away_idx]
                    
                    fixture = Fixture(
                        season_id=season.id,
                        round=round_num,
                        home_id=home_club.id,
                        away_id=away_club.id,
                        played=False,
                        scheduled_date=self._calculate_round_date(season, round_num)
                    )
                    round_fixtures.append(fixture)
            
            fixtures.extend(round_fixtures)
            
            # Rotate clubs for next round (keep first club fixed)
            clubs = [clubs[0]] + clubs[2:] + [clubs[1]]

        return fixtures

    def _generate_additional_afl_rounds(
        self, season: Season, clubs: List[Club], start_round: int
    ) -> List[Fixture]:
        """Generate additional AFL rounds (18-22) with strategic matchups."""
        fixtures = []
        remaining_rounds = season.total_rounds - start_round + 1

        # For simplicity, generate additional rounds using weighted random selection
        # In a real AFL fixture, this would consider:
        # - Geographic rivalries (local derbies)
        # - Broadcast value (big clubs vs each other)
        # - Travel considerations
        # - Previous season performance

        rivalry_pairs = self._get_rivalry_pairs(clubs)
        
        for round_num in range(start_round, season.total_rounds + 1):
            round_fixtures = []
            used_clubs = set()
            
            # Try to schedule rivalry games first
            for home_club, away_club in rivalry_pairs:
                if (home_club.id not in used_clubs and 
                    away_club.id not in used_clubs and 
                    len(round_fixtures) < len(clubs) // 2):
                    
                    fixture = Fixture(
                        season_id=season.id,
                        round=round_num,
                        home_id=home_club.id,
                        away_id=away_club.id,
                        played=False,
                        scheduled_date=self._calculate_round_date(season, round_num)
                    )
                    round_fixtures.append(fixture)
                    used_clubs.add(home_club.id)
                    used_clubs.add(away_club.id)
            
            # Fill remaining slots with random matchups
            available_clubs = [c for c in clubs if c.id not in used_clubs]
            random.shuffle(available_clubs)
            
            for i in range(0, len(available_clubs) - 1, 2):
                if len(round_fixtures) < len(clubs) // 2:
                    home_club = available_clubs[i]
                    away_club = available_clubs[i + 1]
                    
                    fixture = Fixture(
                        season_id=season.id,
                        round=round_num,
                        home_id=home_club.id,
                        away_id=away_club.id,
                        played=False,
                        scheduled_date=self._calculate_round_date(season, round_num)
                    )
                    round_fixtures.append(fixture)
            
            fixtures.extend(round_fixtures)

        return fixtures

    def _generate_round_robin(
        self, season: Season, clubs: List[Club], max_rounds: int
    ) -> List[Fixture]:
        """Generate round-robin fixtures with specified maximum rounds."""
        fixtures = []
        num_clubs = len(clubs)
        
        if num_clubs < 2:
            return fixtures

        # Calculate how many complete cycles we can fit
        games_per_cycle = num_clubs - 1  # Each team plays every other once
        cycles = max_rounds // games_per_cycle
        remaining_rounds = max_rounds % games_per_cycle

        round_num = 1

        # Generate complete cycles
        for cycle in range(cycles):
            cycle_fixtures = self._generate_complete_round_robin(season, clubs.copy())
            for fixture in cycle_fixtures:
                fixture.round = round_num
                fixture.scheduled_date = self._calculate_round_date(season, round_num)
                fixtures.append(fixture)
                
                # Increment round for each fixture
                if len([f for f in cycle_fixtures if f.round == round_num]) == len(clubs) // 2:
                    round_num += 1

        # Generate remaining rounds if any
        if remaining_rounds > 0:
            partial_fixtures = self._generate_complete_round_robin(season, clubs.copy())
            for i, fixture in enumerate(partial_fixtures[:remaining_rounds * (len(clubs) // 2)]):
                fixture.round = round_num + (i // (len(clubs) // 2))
                fixture.scheduled_date = self._calculate_round_date(season, fixture.round)
                fixtures.append(fixture)

        return fixtures

    def _get_rivalry_pairs(self, clubs: List[Club]) -> List[Tuple[Club, Club]]:
        """Define rivalry pairs for more interesting additional rounds."""
        # AFL rivalry matchups (simplified)
        rivalry_names = [
            ("Collingwood Magpies", "Carlton Blues"),  # Traditional rivalry
            ("Adelaide Crows", "Port Adelaide Power"),  # Showdown
            ("West Coast Eagles", "Fremantle Dockers"),  # Western Derby
            ("Sydney Swans", "GWS Giants"),  # Sydney Derby
            ("Richmond Tigers", "Carlton Blues"),  # Traditional rivalry
            ("Essendon Bombers", "Hawthorn Hawks"),  # Historical rivalry
        ]
        
        club_map = {club.name: club for club in clubs}
        rivalry_pairs = []
        
        for home_name, away_name in rivalry_names:
            home_club = club_map.get(home_name)
            away_club = club_map.get(away_name)
            if home_club and away_club:
                rivalry_pairs.append((home_club, away_club))
        
        return rivalry_pairs

    def _calculate_round_date(self, season: Season, round_num: int) -> datetime:
        """Calculate the scheduled date for a round."""
        # Season typically starts in March
        season_start = datetime(season.year, 3, 15)  # Mid-March start
        
        # Each round is typically 1 week apart
        round_date = season_start + timedelta(weeks=round_num - 1)
        
        # Schedule for weekends (Saturday afternoon)
        # Adjust to next Saturday if not already weekend
        days_until_saturday = (5 - round_date.weekday()) % 7
        round_date += timedelta(days=days_until_saturday)
        
        # Set to typical AFL game time (2:30 PM)
        round_date = round_date.replace(hour=14, minute=30, second=0, microsecond=0)
        
        return round_date

    def clear_season_fixtures(self, season_id: int) -> int:
        """Clear all fixtures for a season. Returns number of fixtures deleted."""
        deleted_count = 0
        fixtures_query = select(Fixture).where(Fixture.season_id == season_id)
        fixtures = self.session.exec(fixtures_query).all()
        
        for fixture in fixtures:
            self.session.delete(fixture)
            deleted_count += 1
        
        self.session.commit()
        return deleted_count

    def regenerate_season_fixtures(self, season_id: int) -> List[Fixture]:
        """Clear existing fixtures and generate new ones for a season."""
        # Clear existing fixtures
        deleted_count = self.clear_season_fixtures(season_id)
        
        # Generate new fixtures
        new_fixtures = self.generate_season_fixtures(season_id)
        
        # Save to database
        for fixture in new_fixtures:
            self.session.add(fixture)
        
        self.session.commit()
        
        return new_fixtures