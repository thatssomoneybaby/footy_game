# AFL Manager Web Game — Functional Specification

## 1. Purpose & Scope

- **Goal:** Deliver a browser‑based AFL management game where users visit a URL, pick a club, and play through a season with promotion and relegation between AFL and VFL tiers.
- **Audience:** Players and fans of Australian Rules Football seeking a strategic management experience accessible from any modern web browser.
- **Responsive UX:** Optimized for desktop, tablet, and mobile layouts.
- **Accessibility:** Meets WCAG 2.1 AA standards, including keyboard navigation and colour contrast.
- **Low‑bandwidth compatibility:** Loads quickly and remains functional on slow or unreliable connections.
- **Out‑of‑scope:** 3‑D graphics, real‑time arcade gameplay, commercial closed‑source releases.

---

## 1.1 High‑Level User Journey

1. **Landing & Sign‑In** – player hits `aflmanager.game` → lightweight login or guest play.
2. **Club Selection** – pick an AFL club (or VFL club in lower tier); confirm team colours and nickname.
3. **Season Dashboard** – central hub between fixtures; shows calendar, ladder, finances, roster health.
4. **Pre‑Match Flow** – click upcoming fixture → review lineup, tactics, injury warnings → press **Start Match**.
5. **Live Match View** – real‑time text commentary panel, score ticker, momentum graph; pause/fast‑forward options.
6. **Post‑Match Summary** – box score, best‑on‑ground, injury outcomes, training XP earned.
7. **Off‑Season Workflow** – draft, trade period, contract renewals, promotion/relegation ceremony.

---

## 2. Technical Assumptions & Prerequisites

| Category | Requirement | Notes |
|----------|-------------|-------|
| Tooling  | Modern web stack (Node 20+, pnpm or yarn) + Python 3.11+ for sim engine |  |
| Data     | 2025 AFL & VFL player/club lists (CSV/SQLite) | Must at least include DOB, positions, basic 2024 stats |
| Skillset | Front‑end (React/TypeScript or equivalent), REST API design, Python for engine |  |

---

## 3. Site Architecture Overview

### 3.1 Page Map
| Page | Purpose | Key UI Elements |
|------|---------|-----------------|
| `/` (Landing) | Brand intro, sign‑in/create game | Call‑to‑action, continue save |
| `/club-select` | Choose club & difficulty | Team cards, search |
| `/dashboard` | Season hub | Sidebar nav, fixture calendar, news feed |
| `/roster` | Player list & training | Table, filters, position badges |
| `/lineup` | Drag‑and‑drop game‑day 22 | Formation board, auto‑pick |
| `/match/:id` | Live simulation | Text feed, stats sidebar, scoreworm |
| `/season-summary` | End‑of‑year wrap | Awards, finances, promotion/relegation graphic |

### 3.2 Front‑end Shell
- **Responsive grid** with a collapsible **sidebar** (links: Dashboard · Roster · Line‑up · Ladder · Draft).
- **Top bar** shows current club logo, season/round, quick finances.

### 3.3 Back‑end Expectations
- REST/JSON API (`/api/...`) exposing season, roster, and simulation endpoints.
- Stateless engine runs in Python; called via `/simulate_round` and `/simulate_match`.
- Store persistent data in Postgres; allow localStorage fallback for guest play.

### 3.4 Non‑Functional
- ≤ 2‑second TTI on broadband, ≤ 5‑second on 3G.
- WCAG 2.1 AA colour contrast and keyboard navigation.

---

## 4. Domain Models & Game Rules

1. **Copy football models** `ofm/domain/football/` → `ofm/domain/afl/`.
2. Rename entities: `Club`, `Player`, `Fixture` stay the same.
3. Add **enum `Position`**: `KPF`, `SmallFwd`, `Ruck`, `Mid`, `HalfBack`, `KPBack`, `Utility`.
4. Add `tier: int = 0` in `Club` (`0 = AFL`, `1 = VFL`).
5. Add scoring constants:

```python
GOAL_POINTS = 6
BEHIND_POINTS = 1
QUARTERS = 4
QUARTER_LEN_MIN = 20  # plus time‑on
```

6. Engine will be packaged as `afl_engine` and imported server‑side; deployment details covered in §13.

## 5. Match Engine Replacement

| Step | Task |
|------|------|
| 5.1 | Create `ofm/match_engine/afl_engine.py` that exposes `simulate_match(home, away)` |
| 5.2 | Implement event loop: centre‑bounce → ruck contest → clearance → disposal chain → shot outcome |
| 5.3 | Weight decisions using player attributes (`kicking`, `handball`, etc.) |
| 5.4 | Produce `MatchResult` object with goals, behinds, per‑player stat lines |
| 5.5 | Wire engine selector in CLI: `--sport afl` |

## 5.5 API Contract (summary)

| Endpoint | Verb | Purpose |
|----------|------|---------|
| `/api/season/{seasonId}/round/{round}/simulate` | POST | Runs all fixtures in the round and returns updated ladder + box scores |
| `/api/match/simulate` | POST | One‑off friendly match |
| `/api/club/{id}/roster` | GET/PUT | Fetch or update player list, training focuses |

---

## 6. League Structure & Relegation

1. **Schedule generation**  
   - Separate fixtures for `tier == 0` and `tier == 1`.  
   - 22‑round AFL fixture; 20‑round VFL fixture (adjustable).

2. **End‑of‑season phase**  
   - After finals, run `relegate_promote()`:
     ```python
     def relegate_promote(db_session):
         afl_bottom = ladder(tier=0).bottom(2)
         vfl_top = ladder(tier=1).top(2)
         for club in afl_bottom: club.tier = 1
         for club in vfl_top: club.tier = 0
     ```

3. **Update fixtures** for next season based on new tiers.

---

## 7. Player Attributes & Progression

| Category | Attributes | Notes |
|----------|------------|-------|
| Technical | kicking, handball, marking, spoiling, ruck_work | 0‑100 |
| Physical  | speed, endurance, strength | Gaussian age curve |
| Mental    | decision_making, leadership, composure | Slower progression |
| Hidden    | potential (50‑100), morale (-5 … +5) | Potential caps yearly gains |

**Training module:** weekly XP split across attributes per squad training focus.

---

## 8. Data Import & Seeding

```bash
poetry run python tools/import_afl_data.py --src ../stats/players2025.sqlite --out init_afl.json
```

- Map 2024 per‑game stats → ratings via linear scaling.
- Store generated JSON in `data/seeds/2025_afl_vfl.json`.
- Add CLI flag `--seed 2025` to load on new game.

---

## 9. Persistence & Save System

- Default JSON save already exists; extend schema to include `tier`, new attributes.
- Optional: switch to SQLite via `sqlmodel` for faster queries.

### 9.1 Database Schema & Migrations

- **Core tables (in Postgres via SQLModel):** `club`, `player`, `fixture`, `season`, `match_stat`, `user_profile`.
- Alembic migrations are version‑controlled in `/alembic/versions`.
- The `tier` column is indexed to accelerate ladder queries.
- Demo seed inserts live under `alembic/seed_001_initial_afl.py`.

---

## 10. User Interface Roadmap

| Phase | UI Stack | Deliverable |
|-------|----------|-------------|
| P0 | Bracket default React pages | Team/Player CRUD, Ladder, Fixtures |
| P1 | New “Sim Round” controls + live box‑score modal | One‑click season advance |
| P2 | Branding pass (club colours, logos), PWA installability | Mobile‑friendly manager |
| P3 | Optional Textual TUI for power users | Low‑resource offline play |

---

## 11. Testing & CI

- Unit test new engine with deterministic random seed.
- Use **pytest** coverage ≥ 80 %.
- GitHub Actions: lint (`ruff`), test, build poetry distribution wheel.

### 11.1 Branching & Release Strategy

- **main** → always deployable, green CI.
- **dev** → integration branch; feature PRs target this.
- **feature/*** → short‑lived branches per ticket; squash‑merge into dev.
- **release‑vX.Y** → cut from main; tags follow semver (`v0.2.0-alpha`).
- Version bump automation handled by `bump‑my‑version` in the engine repo and `standard‑version` in the front‑end repo.

---

## 12. Licensing

- The fork inherits **GPL‑3.0** → any distributed derivative must publish source.
- If proprietary UI desired, keep engine in GPL repo, call via localhost API.
- Document third‑party assets (AFL logos, player names) for copyright reasons.

### 12.1 Asset & IP Management

- Club logos and AFL trademarks are **placeholders only** in development; replace with user‑supplied SVGs before public release or secure licensing from the AFL.
- Player names in the default seed use public‑domain dummy data; a script `tools/redact_real_names.py` can scrub private datasets.
- All third‑party JS/CSS libs are tracked with `license‑checker` and documented in `THIRD_PARTY.md`.

---

## 13. Deployment & Distribution

| Target | Tooling | Notes |
|--------|---------|-------|
| Desktop | PyInstaller | Bundled EXE/app for testers |
| Web     | Pyodide + PWA | Compile engine to WASM, host on Netlify |
| Mobile  | BeeWare | Experimental; wrap Textual/React front‑end |

### 13.1 Security & Privacy

- All API routes require JWT auth; tokens expire after 1 h.
- Passwords hashed with Argon2id via `passlib`.
- Postgres is accessed through Env‑var secrets (`DATABASE_URL`); never commit `.env` files.
- Front‑end enforces HTTPS and CSP headers via `next‑secure‑headers`.
- Periodic `bandit` scan in CI for Python and `npm audit` for JS deps.

---

## 14. Game‑Specific Feature Backlog

1. **Training & Development** – weekly XP allocation sliders, visible progression graph.
2. **Injuries & Suspensions** – probability model, UI badge, list‑manager decisions.
3. **Draft & Trade Period** – NAB AFL Draft with hidden potentials, trade confirmations.
4. **Financial Model** – soft cap, membership revenue, sponsorship multipliers.
5. **Historical Stats Import** – allow users to start in past seasons (e.g., 1990).
6. **Data Export** – CSV/JSON dumps for community analysis.

---

## 15. Milestone Timeline (First 8 Weeks)

| Week | Deliverable |
|------|-------------|
| 1 | Repo bootstrapped; AFL domain models |
| 2 | Basic match engine returns final scores |
| 3 | Per‑player stats & ladder calculation |
| 4 | Promotion/relegation workflow |
| 5 | Data import script & real 2025 rosters |
| 6 | Textual UI prototype |
| 7 | Training & attribute progression |
| 8 | Alpha release on GitHub + PyInstaller builds |

---

## 16. Next Steps

1. **Create feature branches** for each section above.
2. Prioritise a thin playable loop before polishing maths.
3. Schedule fortnightly play‑tests with friends for feedback.
4. Document findings in `docs/` and keep CHANGELOG updated.

---

*Happy coding, and may your rebuild deliver a dynasty!*  
