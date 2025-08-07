from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class Position(str, Enum):
    KPF = "KPF"  # Key Position Forward
    SMALL_FWD = "SmallFwd"  # Small Forward
    RUCK = "Ruck"  # Ruckman
    MID = "Mid"  # Midfielder
    HALF_BACK = "HalfBack"  # Half Back
    KP_BACK = "KPBack"  # Key Position Back
    UTILITY = "Utility"  # Utility Player


class Club(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    tier: int = Field(default=0, index=True)  # 0 = AFL, 1 = VFL
    primary_colour: str
    secondary_colour: Optional[str] = None
    nickname: str
    logo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    players: list["Player"] = Relationship(back_populates="club")
    home_fixtures: list["Fixture"] = Relationship(
        back_populates="home_club", 
        sa_relationship_kwargs={"foreign_keys": "Fixture.home_id"}
    )
    away_fixtures: list["Fixture"] = Relationship(
        back_populates="away_club", 
        sa_relationship_kwargs={"foreign_keys": "Fixture.away_id"}
    )


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="club.id")
    name: str = Field(index=True)
    position: Position
    age: int
    
    # Technical attributes (0-100)
    kicking: int = Field(ge=0, le=100)
    handball: int = Field(ge=0, le=100)
    marking: int = Field(ge=0, le=100)
    spoiling: int = Field(ge=0, le=100)
    ruck_work: int = Field(ge=0, le=100)
    
    # Physical attributes (0-100)
    speed: int = Field(ge=0, le=100)
    endurance: int = Field(ge=0, le=100)
    strength: int = Field(ge=0, le=100)
    
    # Mental attributes (0-100)
    decision_making: int = Field(ge=0, le=100)
    leadership: int = Field(ge=0, le=100)
    composure: int = Field(ge=0, le=100)
    
    # Hidden attributes
    potential: int = Field(ge=50, le=100)  # Caps yearly gains
    morale: int = Field(ge=-5, le=5, default=0)  # Affects performance
    
    # Status
    injured: bool = Field(default=False)
    suspended: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    club: Club = Relationship(back_populates="players")
    match_stats: list["MatchStat"] = Relationship(back_populates="player")


class Season(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True)
    tier: int = Field(default=0, index=True)  # 0 = AFL, 1 = VFL
    current_round: int = Field(default=1)
    total_rounds: int = Field(default=22)  # AFL: 22, VFL: 20
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    fixtures: list["Fixture"] = Relationship(back_populates="season")


class Fixture(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    season_id: int = Field(foreign_key="season.id")
    round: int
    home_id: int = Field(foreign_key="club.id")
    away_id: int = Field(foreign_key="club.id")
    
    # Match details
    played: bool = Field(default=False)
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_goals: Optional[int] = None
    home_behinds: Optional[int] = None
    away_goals: Optional[int] = None
    away_behinds: Optional[int] = None
    
    # Timing
    scheduled_date: Optional[datetime] = None
    played_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    season: Season = Relationship(back_populates="fixtures")
    home_club: Club = Relationship(
        back_populates="home_fixtures",
        sa_relationship_kwargs={"foreign_keys": "Fixture.home_id"}
    )
    away_club: Club = Relationship(
        back_populates="away_fixtures",
        sa_relationship_kwargs={"foreign_keys": "Fixture.away_id"}
    )
    match_stats: list["MatchStat"] = Relationship(back_populates="fixture")


class MatchStat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fixture_id: int = Field(foreign_key="fixture.id")
    player_id: int = Field(foreign_key="player.id")
    
    # AFL specific stats
    goals: int = Field(default=0)
    behinds: int = Field(default=0)
    kicks: int = Field(default=0)
    handballs: int = Field(default=0)
    disposals: int = Field(default=0)
    marks: int = Field(default=0)
    tackles: int = Field(default=0)
    hit_outs: int = Field(default=0)  # Ruck contests won
    
    # Advanced stats
    contested_possessions: int = Field(default=0)
    uncontested_possessions: int = Field(default=0)
    effective_disposals: int = Field(default=0)
    
    # Performance rating
    rating: Optional[float] = None  # 0-10 scale
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    fixture: Fixture = Relationship(back_populates="match_stats")
    player: Player = Relationship(back_populates="match_stats")


class UserProfile(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    
    # Game preferences
    selected_club_id: Optional[int] = Field(foreign_key="club.id", default=None)
    current_season_id: Optional[int] = Field(foreign_key="season.id", default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Save(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="userprofile.id")
    name: str  # Save slot name
    blob: bytes  # Gzipped JSON from engine
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Game constants
GOAL_POINTS = 6
BEHIND_POINTS = 1
QUARTERS = 4
QUARTER_LEN_MIN = 20  # plus time-on