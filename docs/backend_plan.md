# Backend Plan – AFL Manager

> **Stack:** FastAPI · Python 3.11 · SQLModel 🡒 Postgres · Alembic · JWT Auth  
> **Goals:** deterministic simulations, secure saves, cheap to host (single small VM
  or containers on Fly.io / Render).

---

## 0. High‑Level Checklist

| Phase | Deliverables | Status |
|-------|--------------|--------|
| **Foundation** | Repo scaffold, linting, healthcheck route | ✅ |
| **Core Data** | Clubs, Players, Fixture, Season tables + seed | ✅ |
| **Sim API** | `/simulate_round`, `/simulate_match` | ✅ |
| **Auth & Saves** | JWT login, save/load endpoints | ⚠️ |
| **Ops** | Dockerfile, prod config, metrics | ✅ |

> ✅ = Complete | ⚠️ = Partial | ☐ = Not Started

### Current Implementation Status (December 2024)
- ✅ **Foundation Complete**: Poetry setup, FastAPI app, dev tools (ruff, black, mypy)
- ✅ **Database Layer**: Full SQLModel schema with AFL-specific models
- ✅ **API Structure**: RESTful endpoints with OpenAPI docs
- ✅ **Docker Ready**: Multi-stage Dockerfile + docker-compose
- ✅ **Quick Start**: Automated setup script (`start.sh`)
- ⚠️ **Authentication**: Models ready, fastapi-users not integrated
- 🔄 **Next Phase**: Fixture generation + ladder calculation

> Keep each phase in its own milestone branch; `main` must stay deployable.

---

## 1. Repository Scaffold

1. `poetry new backend`
2. Add **dev tools**  
   ```bash
   poetry add --group dev black ruff mypy pytest pytest-asyncio httpx
   pre-commit install
   ```
3. Folder layout  
   ```
   backend/
     app/                 # FastAPI application
       api/
       core/              # settings, security, utils
       db/                # models, migrations
       services/          # thin business logic wrappers
     tests/
   ```

---

## 2. Database Layer

### 2.1 Models (SQLModel)

```py
class Club(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    tier: int = 0          # 0 = AFL, 1 = VFL
    primary_colour: str

class Player(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    club_id: int = ForeignKey("club.id")
    name: str
    position: str
    kicking: int
    handball: int
    ...

class Fixture(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    season_id: int = ForeignKey("season.id")
    round: int
    home_id: int
    away_id: int
    played: bool = False
```

### 2.2 Migrations

```bash
alembic init migrations
alembic revision -m "initial schema"
alembic upgrade head
```

Seed script: `alembic/versions/2025_seed_afl.py`.

---

## 3. FastAPI App

```py
app = FastAPI(title="AFL Manager API")

@app.get("/health")
def health():
    return {"status": "ok"}
```

### 3.1 Settings

Use **pydantic‑settings**; read from environment:
```py
class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    JWT_SECRET: str
    CORS_ORIGINS: list[str] = ["*"]
```

---

## 4. Simulation Endpoints

| Route | Method | Body | Purpose |
|-------|--------|------|---------|
| `/api/match/simulate` | POST | `{home: id, away: id}` | Returns `MatchResult` JSON |
| `/api/season/{sid}/round/{n}/simulate` | POST | – | Sim all unplayed fixtures in round |
| `/api/club/{id}/roster` | GET/PUT | – / `{players:[...]}` | Retrieve/update roster & training |

### 4.1 Wiring the Engine

```py
from afl_engine import season_service

@app.post("/api/season/{season_id}/round/{round}/simulate")
async def sim_round(season_id: int, round: int):
    result = season_service.play_round(season_id, round)
    return result.model_dump()
```

---

## 5. Auth & Saves

- **fastapi‑users** with PostgreSQL backend.
- JWT access token 1 h, refresh 7 d.
- Save slots table:  
  ```py
  class Save(SQLModel, table=True):
      id: int | None
      user_id: uuid.UUID
      blob: bytes  # gzipped JSON from engine
      ts: datetime
  ```

---

## 6. Ops & Deployment

| Item | Choice |
|------|--------|
| Web server | `gunicorn -k uvicorn.workers.UvicornWorker -w 2` |
| Container | `Dockerfile` multi‑stage; Alpine base for runtime |
| Env | Fly.io app + Lite Postgres; alt: Render Blueprint |
| Observability | Prometheus exporter (`prometheus-fastapi-instrumentator`) |
| CI | GitHub Actions → test, lint, build, push image |

---

## 7. Security Checks

- `bandit` scan in CI.
- OWASP secure headers middleware.
- CORS restricted to prod front‑end origin.
- Rate limit `/simulate_*` routes (`slowapi`).

---

## 8. Future Enhancements

* GraphQL gateway (Hasura) for community dashboards.  
* WebSocket push endpoint for live match feed.  
* Multi‑tenant schema per league for multiplayer v2.0.
