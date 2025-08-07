# 🏈 AFL Manager

A browser-based Australian Football League simulation game with promotion and relegation between AFL and VFL tiers.

## 🎮 Quick Start

1. **Start the server:**
   ```bash
   cd backend
   ./start.sh
   ```

2. **Play in your browser:**
   Open http://localhost:8000

## ✨ Features

- **18 AFL Teams + 4 VFL Teams** with realistic player rosters
- **Live Ladder Standings** with percentage calculations  
- **Match Simulation** with AFL scoring (6pts goals, 1pt behinds)
- **Season Management** - 22 AFL rounds, 20 VFL rounds
- **Promotion/Relegation** between leagues
- **Modern Web Interface** - responsive design, works on mobile
- **Real-time Results** - simulate individual rounds or full seasons

## 🌐 Web Interface

The game runs entirely in your browser with:

- 📊 **AFL/VFL Ladders** - Color-coded positions, live standings
- ⚽ **Round Simulation** - Click to advance the season  
- 🏟️ **Club Browser** - View all teams and colors
- 📋 **Season Status** - Track progress across both leagues
- ⚡ **Full Season Mode** - Fast-forward to finals

## 🏗️ Technical Architecture

**Backend:**
- FastAPI with SQLite database
- RESTful API with OpenAPI documentation
- SQLModel ORM with Alembic migrations
- Match simulation engine

**Frontend:**
- Vanilla JavaScript (no frameworks needed)
- Modern CSS with responsive design
- Real-time API integration

## 📁 Project Structure

```
footy_game/
├── backend/               # FastAPI server
│   ├── app/              # Application code
│   │   ├── api/          # API endpoints
│   │   ├── db/           # Database models
│   │   ├── services/     # Game logic
│   │   └── main.py       # FastAPI app
│   ├── static/           # Web interface files
│   │   ├── index.html    # Main page
│   │   ├── styles.css    # UI styling
│   │   └── app.js        # Game functionality
│   ├── migrations/       # Database migrations  
│   ├── seed_data.py      # Initial data setup
│   ├── start.sh          # Quick start script
│   └── afl_manager.db    # SQLite database
├── docs/                 # Development documentation
└── README.md            # This file
```

## 🔧 Development

**Requirements:**
- Python 3.11+
- Poetry (installed automatically by start script)

**API Documentation:**
Visit http://localhost:8000/docs when server is running

**Database:**
- SQLite for easy development
- Switch to PostgreSQL for production (already configured)

## 🚀 Deployment

### Quick Deploy to Railway (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "AFL Manager ready for deployment"
   git push origin main
   ```

2. **Deploy to Railway:**
   - Go to [railway.app](https://railway.app)
   - "Deploy from GitHub repo" 
   - Select your AFL Manager repo
   - Railway auto-detects and deploys!

3. **Your game will be live at:** `https://your-app.railway.app`

### Alternative Platforms
- **Render** - Similar GitHub connection process
- **Fly.io** - Requires Docker setup  
- **DigitalOcean App Platform** - GitHub integration available

## 🎯 Current Status

**✅ Fully Working:**
- Complete AFL/VFL simulation
- Web-based interface
- Season progression and ladders
- Match results and standings

**🔮 Future Enhancements:**
- Player statistics and development
- Injury and suspension system  
- Draft and trade mechanics
- Historical season data
- User accounts and save games

## 🏆 Game Features

**Leagues:**
- AFL: 18 teams, 22 rounds
- VFL: 4 teams, 20 rounds  
- Promotion/relegation between tiers

**Simulation:**
- Realistic AFL scoring system
- Match results with goals/behinds
- Ladder with wins/losses/percentage
- Finals bracket generation

**Teams Include:**
- All 18 current AFL teams
- Sample VFL teams for relegation system
- Team colors and nicknames
- Generated player rosters

---

**Start playing now:** `cd backend && ./start.sh` then visit http://localhost:8000 🎮