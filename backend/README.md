# AFL Manager Backend

A FastAPI-based backend for the AFL Manager simulation game with full season management and promotion/relegation system.

## 🚀 Quick Start

The easiest way to get started is with the automated setup script:

```bash
./start.sh
```

This will handle everything:
- Install Poetry (if needed)
- Install dependencies
- Set up PostgreSQL database
- Run migrations
- Seed initial data
- Start the development server

## 🎮 Game Features

### ✅ Core Game Logic (IMPLEMENTED!)
- **Fixture Generation**: Realistic AFL (22 rounds) and VFL (20 rounds) seasons
- **Ladder Calculation**: Real-time standings with AFL percentage rules
- **Season Management**: Round progression and season completion
- **Promotion/Relegation**: Automatic tier changes at season end
- **Match Simulation**: Basic random results with realistic AFL scoring

### ✅ Complete API Endpoints
- `POST /api/v1/fixtures/generate` - Generate season fixtures
- `GET /api/v1/seasons/{id}/ladder` - Current ladder standings
- `GET /api/v1/seasons/{id}/finals` - Finals bracket (top 8)
- `POST /api/v1/matches/simulate-round` - Simulate full round
- `GET /api/v1/management/game-status` - Overall game state
- `POST /api/v1/management/seasons/end-season` - Promotion/relegation

### 🎯 Quick Play Guide
1. **Generate Fixtures**: `POST /fixtures/generate {"season_id": 1}`
2. **Simulate Rounds**: `POST /matches/simulate-round {"season_id": 1, "round": 1}`
3. **Check Ladder**: `GET /seasons/1/ladder`
4. **End Season**: `POST /management/seasons/end-season`

## 📋 Manual Setup

If you prefer manual setup:

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Poetry

### Installation

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Create database:**
   ```bash
   createdb afl_manager
   ```

4. **Run migrations:**
   ```bash
   poetry run alembic revision --autogenerate -m "Initial schema"
   poetry run alembic upgrade head
   ```

5. **Seed data (optional):**
   ```bash
   poetry run python seed_data.py
   ```

6. **Start server:**
   ```bash
   poetry run python run.py
   # or
   poetry run uvicorn app.main:app --reload
   ```

## 🐳 Docker Setup

For containerized development:

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- AFL Manager API
- Adminer (database admin) at http://localhost:8080

## 📚 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database Admin**: http://localhost:8080 (Docker only)

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/          # API route handlers
│   │   └── routes.py          # Route registration
│   ├── core/
│   │   └── config.py          # Settings and configuration
│   ├── db/
│   │   ├── database.py        # Database connection
│   │   └── models.py          # SQLModel definitions
│   ├── services/
│   │   ├── fixture_generator.py  # Season fixture creation
│   │   ├── ladder.py             # Ladder calculations
│   │   ├── season_manager.py     # Season lifecycle
│   │   └── simulation.py        # Match simulation
│   └── main.py                # FastAPI application
├── migrations/                 # Alembic migrations
├── tests/                     # Test suite
├── .env.example              # Environment template
├── start.sh                  # Quick start script
├── seed_data.py             # Database seeding
└── docker-compose.yml       # Docker setup
```

## 🏈 AFL-Specific Features

### Database Models
- **Club**: AFL/VFL teams with tier system (0=AFL, 1=VFL)
- **Player**: Full attribute system (technical, physical, mental)
- **Season**: Multi-tier league management with round tracking
- **Fixture**: Match scheduling and results with AFL scoring
- **MatchStat**: Detailed player statistics

### Player Attributes
Players have realistic AFL-style attributes:
- **Technical**: Kicking, Handball, Marking, Spoiling, Ruck Work
- **Physical**: Speed, Endurance, Strength
- **Mental**: Decision Making, Leadership, Composure
- **Hidden**: Potential, Morale

### Game Mechanics
- **AFL Fixture**: 22 rounds with strategic additional matchups
- **VFL Fixture**: 20 rounds with round-robin scheduling
- **Ladder System**: AFL rules with percentage tie-breaker
- **Finals**: Top 8 system with qualifying and elimination finals
- **Promotion/Relegation**: Bottom 2 AFL ↔ Top 2 VFL

## 🧪 Development

### Code Quality
```bash
# Linting
poetry run ruff check app/

# Formatting  
poetry run black app/

# Type checking
poetry run mypy app/
```

### Database
```bash
# Create migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Reset database
poetry run alembic downgrade base
poetry run alembic upgrade head
```

### Testing
```bash
poetry run pytest
```

## 🔧 Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/afl_manager` |
| `DEBUG` | Enable debug mode | `False` |
| `SECRET_KEY` | Application secret key | Required |
| `AFL_ROUNDS` | AFL season rounds | `22` |
| `VFL_ROUNDS` | VFL season rounds | `20` |

## 📈 Development Roadmap

### ✅ COMPLETED (Phase 1 & 2)
- ✅ Complete backend infrastructure
- ✅ AFL/VFL database models with full attribute system
- ✅ Fixture generation with AFL-specific scheduling
- ✅ Ladder calculation with percentage tie-breakers
- ✅ Season progression and management
- ✅ Promotion/relegation between tiers
- ✅ Basic match simulation

### 🔄 NEXT PRIORITIES (Phase 3)
1. **Enhanced Match Engine** - Player attribute-based simulation
2. **Authentication System** - JWT user management
3. **Test Suite** - Comprehensive testing coverage
4. **Statistics System** - Detailed AFL statistics tracking

### 🚀 FUTURE FEATURES (Phase 4+)
- **Training System** - Weekly player development
- **Draft Mechanics** - End-of-season recruitment
- **Injury System** - Realistic player availability
- **Financial Modeling** - Salary cap and revenue
- **WebSocket Support** - Real-time match updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

---

**Current Status**: Core game mechanics complete! The AFL Manager backend now supports full season simulation with fixture generation, ladder calculation, and promotion/relegation system.