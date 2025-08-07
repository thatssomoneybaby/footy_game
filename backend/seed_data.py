#!/usr/bin/env python3
"""
Seed script for AFL Manager database
Populates initial clubs and sample players
"""

import random
from datetime import datetime

from sqlmodel import Session, select

from app.core.config import settings
from app.db.database import engine
from app.db.models import Club, Player, Season, Position


# AFL Club data
AFL_CLUBS = [
    {"name": "Adelaide Crows", "nickname": "Crows", "primary_colour": "#002B5C", "secondary_colour": "#FFD100"},
    {"name": "Brisbane Lions", "nickname": "Lions", "primary_colour": "#A30046", "secondary_colour": "#FFD100"},
    {"name": "Carlton Blues", "nickname": "Blues", "primary_colour": "#002F5D", "secondary_colour": "#FFFFFF"},
    {"name": "Collingwood Magpies", "nickname": "Magpies", "primary_colour": "#000000", "secondary_colour": "#FFFFFF"},
    {"name": "Essendon Bombers", "nickname": "Bombers", "primary_colour": "#CC2229", "secondary_colour": "#000000"},
    {"name": "Fremantle Dockers", "nickname": "Dockers", "primary_colour": "#2E0C58", "secondary_colour": "#FFFFFF"},
    {"name": "Geelong Cats", "nickname": "Cats", "primary_colour": "#001F3B", "secondary_colour": "#FFFFFF"},
    {"name": "Gold Coast Suns", "nickname": "Suns", "primary_colour": "#FFD100", "secondary_colour": "#CC2229"},
    {"name": "GWS Giants", "nickname": "Giants", "primary_colour": "#FF6600", "secondary_colour": "#000000"},
    {"name": "Hawthorn Hawks", "nickname": "Hawks", "primary_colour": "#492F1B", "secondary_colour": "#FFD100"},
    {"name": "Melbourne Demons", "nickname": "Demons", "primary_colour": "#CC2229", "secondary_colour": "#002F5D"},
    {"name": "North Melbourne Kangaroos", "nickname": "Kangaroos", "primary_colour": "#003F7F", "secondary_colour": "#FFFFFF"},
    {"name": "Port Adelaide Power", "nickname": "Power", "primary_colour": "#00B5A0", "secondary_colour": "#000000"},
    {"name": "Richmond Tigers", "nickname": "Tigers", "primary_colour": "#FFD100", "secondary_colour": "#000000"},
    {"name": "St Kilda Saints", "nickname": "Saints", "primary_colour": "#CC2229", "secondary_colour": "#000000"},
    {"name": "Sydney Swans", "nickname": "Swans", "primary_colour": "#CC2229", "secondary_colour": "#FFFFFF"},
    {"name": "West Coast Eagles", "nickname": "Eagles", "primary_colour": "#002F5D", "secondary_colour": "#FFD100"},
    {"name": "Western Bulldogs", "nickname": "Bulldogs", "primary_colour": "#003F7F", "secondary_colour": "#CC2229"},
]

# Sample VFL clubs (simplified list)
VFL_CLUBS = [
    {"name": "Box Hill Hawks", "nickname": "Hawks", "primary_colour": "#492F1B", "secondary_colour": "#FFD100", "tier": 1},
    {"name": "Casey Demons", "nickname": "Demons", "primary_colour": "#CC2229", "secondary_colour": "#002F5D", "tier": 1},
    {"name": "Coburg Lions", "nickname": "Lions", "primary_colour": "#A30046", "secondary_colour": "#FFD100", "tier": 1},
    {"name": "Footscray Bulldogs", "nickname": "Bulldogs", "primary_colour": "#003F7F", "secondary_colour": "#CC2229", "tier": 1},
]

# Sample player names
FIRST_NAMES = [
    "Jack", "Tom", "Sam", "Josh", "Luke", "Ben", "Jake", "Matt", "Alex", "Dan",
    "James", "Michael", "David", "Ryan", "Nathan", "Adam", "Chris", "Mark", "Luke", "Aaron"
]

LAST_NAMES = [
    "Smith", "Johnson", "Brown", "Taylor", "Anderson", "Thomas", "Jackson", "White",
    "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez",
    "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright"
]


def generate_random_player(club_id: int) -> Player:
    """Generate a random player for a club."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Generate realistic age distribution
    age = random.choices(
        range(18, 35),
        weights=[1, 2, 3, 4, 5, 5, 4, 3, 3, 2, 2, 1, 1, 1, 1, 1, 1],
        k=1
    )[0]
    
    # Generate attributes based on age (younger players have more potential)
    base_skill = random.randint(40, 85)
    age_factor = max(0.7, 1.0 - (age - 22) * 0.02)  # Peak around 22-25
    
    return Player(
        club_id=club_id,
        name=f"{first_name} {last_name}",
        position=random.choice(list(Position)),
        age=age,
        # Technical attributes
        kicking=max(20, min(100, int(base_skill + random.randint(-15, 15)))),
        handball=max(20, min(100, int(base_skill + random.randint(-15, 15)))),
        marking=max(20, min(100, int(base_skill + random.randint(-15, 15)))),
        spoiling=max(20, min(100, int(base_skill + random.randint(-15, 15)))),
        ruck_work=max(20, min(100, int(base_skill + random.randint(-20, 10)))),
        # Physical attributes
        speed=max(20, min(100, int((base_skill * age_factor) + random.randint(-15, 15)))),
        endurance=max(20, min(100, int((base_skill * age_factor) + random.randint(-15, 15)))),
        strength=max(20, min(100, int(base_skill + random.randint(-15, 15)))),
        # Mental attributes
        decision_making=max(20, min(100, int(base_skill + (age - 18) * 2 + random.randint(-10, 10)))),
        leadership=max(20, min(100, int(base_skill + (age - 18) * 3 + random.randint(-15, 5)))),
        composure=max(20, min(100, int(base_skill + (age - 18) * 2 + random.randint(-10, 10)))),
        # Hidden attributes
        potential=random.randint(max(50, base_skill - 10), min(100, base_skill + 20)),
        morale=random.randint(-2, 3),
    )


def seed_database():
    """Seed the database with initial data."""
    print("🌱 Starting database seeding...")
    
    with Session(engine) as session:
        # Check if data already exists
        existing_clubs = session.exec(select(Club)).first()
        if existing_clubs:
            print("⚠️  Database already contains clubs. Skipping seeding.")
            return
        
        # Create AFL clubs
        print("🏈 Creating AFL clubs...")
        afl_clubs = []
        for club_data in AFL_CLUBS:
            club = Club(
                name=club_data["name"],
                nickname=club_data["nickname"],
                primary_colour=club_data["primary_colour"],
                secondary_colour=club_data.get("secondary_colour"),
                tier=0  # AFL tier
            )
            session.add(club)
            afl_clubs.append(club)
        
        # Create VFL clubs
        print("🏆 Creating VFL clubs...")
        vfl_clubs = []
        for club_data in VFL_CLUBS:
            club = Club(
                name=club_data["name"],
                nickname=club_data["nickname"],
                primary_colour=club_data["primary_colour"],
                secondary_colour=club_data.get("secondary_colour"),
                tier=1  # VFL tier
            )
            session.add(club)
            vfl_clubs.append(club)
        
        session.commit()
        
        # Generate players for each club
        print("👥 Generating players...")
        all_clubs = afl_clubs + vfl_clubs
        
        for club in all_clubs:
            # Generate 25-35 players per club
            num_players = random.randint(25, 35)
            print(f"  - Creating {num_players} players for {club.name}")
            
            for _ in range(num_players):
                player = generate_random_player(club.id)
                session.add(player)
        
        # Create current season
        print("📅 Creating current season...")
        current_year = datetime.now().year
        
        # AFL Season
        afl_season = Season(
            year=current_year,
            tier=0,
            current_round=1,
            total_rounds=settings.AFL_ROUNDS,
            is_active=True
        )
        session.add(afl_season)
        
        # VFL Season
        vfl_season = Season(
            year=current_year,
            tier=1,
            current_round=1,
            total_rounds=settings.VFL_ROUNDS,
            is_active=True
        )
        session.add(vfl_season)
        
        session.commit()
        
        print("✅ Database seeding completed successfully!")
        print(f"   - Created {len(AFL_CLUBS)} AFL clubs")
        print(f"   - Created {len(VFL_CLUBS)} VFL clubs")
        print("   - Generated players for all clubs")
        print("   - Created current season fixtures")


if __name__ == "__main__":
    seed_database()