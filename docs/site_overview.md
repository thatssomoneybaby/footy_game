# AFL Manager – Site Overview

This document explains **why** the project exists and **what** the finished web product must deliver.  
It links out to the detailed backend, frontend, and game-logic plans.

---

## 1. Product Vision
An accessible, browser-based AFL management game where fans build dynasties, juggle finances, and experience promotion/relegation between AFL and VFL tiers.

## 2. Core Pillars
| Pillar | Success Metric |
|--------|---------------|
| **Instant Play** | First meaningful interaction ≤ 3 s on broadband, ≤ 8 s on 3G |
| **Depth** | 10+ seasons of progression without repetitive loops |
| **Fair & Transparent** | All probabilities and ratings exposed via tooltips / docs |
| **Responsive UX** | Smooth on desktop, tablet, mobile (≥ 95 Lighthouse PWA score) |

## 3. Big Milestones
1. **MVP** – static fixture, single-season play-through, no persistence.
2. **Beta** – full CRUD saves, roster management, draft, basic UI polish.
3. **v1.0** – multi-season loop, promotion/relegation, responsive design, auth.
4. **v2.0 Roadmap** – multiplayer leagues, cloud saves, mobile app wrappers.

### Linked Specs
| Area | Spec |
|------|------|
| Back-end & API | [`backend_plan.md`](./backend_plan.md) |
| Front-end & Styling | [`frontend_plan.md`](./frontend_plan.md) |
| Game Engine & Balance | [`game_logic_plan.md`](./game_logic_plan.md) |