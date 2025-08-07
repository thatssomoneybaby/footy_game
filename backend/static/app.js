// AFL Manager Web Interface JavaScript

const API_BASE = '/api/v1';

// Utility functions
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="error-message">
            <h2>❌ Error</h2>
            <p>${message}</p>
        </div>
    `;
}

function showSuccess(message) {
    const mainContent = document.getElementById('main-content');
    const currentContent = mainContent.innerHTML;
    mainContent.innerHTML = `
        <div class="success-message">
            <h2>✅ Success</h2>
            <p>${message}</p>
        </div>
    ` + currentContent;
}

async function apiRequest(endpoint, method = 'GET', data = null) {
    showLoading();
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(API_BASE + endpoint, options);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// Main functions
async function showAFLLadder() {
    try {
        // Get active seasons
        const seasonsData = await apiRequest('/management/seasons/active');
        const aflSeasons = seasonsData.active_seasons.filter(s => s.tier === 0);
        
        if (aflSeasons.length === 0) {
            showError('No active AFL season found');
            return;
        }
        
        const seasonId = aflSeasons[0].season_id;
        const ladderData = await apiRequest(`/seasons/${seasonId}/ladder`);
        
        if (!ladderData.ladder) {
            showError('No ladder data available');
            return;
        }
        
        displayLadder(ladderData.ladder, 'AFL', aflSeasons[0]);
    } catch (error) {
        showError(`Failed to load AFL ladder: ${error.message}`);
    }
}

async function showVFLLadder() {
    try {
        // Get active seasons
        const seasonsData = await apiRequest('/management/seasons/active');
        const vflSeasons = seasonsData.active_seasons.filter(s => s.tier === 1);
        
        if (vflSeasons.length === 0) {
            showError('No active VFL season found');
            return;
        }
        
        const seasonId = vflSeasons[0].season_id;
        const ladderData = await apiRequest(`/seasons/${seasonId}/ladder`);
        
        if (!ladderData.ladder) {
            showError('No ladder data available');
            return;
        }
        
        displayLadder(ladderData.ladder, 'VFL', vflSeasons[0]);
    } catch (error) {
        showError(`Failed to load VFL ladder: ${error.message}`);
    }
}

function displayLadder(ladder, leagueName, seasonInfo) {
    const mainContent = document.getElementById('main-content');
    
    let tableHtml = `
        <div class="ladder-section">
            <h2>🏆 ${leagueName} Ladder - Season ${seasonInfo.year}</h2>
            <p>Round ${seasonInfo.current_round} of ${seasonInfo.total_rounds}</p>
            
            <table class="ladder-table">
                <thead>
                    <tr>
                        <th>Pos</th>
                        <th>Club</th>
                        <th>W</th>
                        <th>L</th>
                        <th>D</th>
                        <th>Pts</th>
                        <th>%</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    ladder.forEach((team, index) => {
        tableHtml += `
            <tr>
                <td>${index + 1}</td>
                <td><strong>${team.club_name}</strong></td>
                <td>${team.wins}</td>
                <td>${team.losses}</td>
                <td>${team.draws}</td>
                <td>${team.ladder_points}</td>
                <td>${team.percentage.toFixed(1)}%</td>
            </tr>
        `;
    });
    
    tableHtml += `
                </tbody>
            </table>
            
            <div style="margin-top: 20px;">
                <button onclick="simulate${leagueName}Round()" class="sim-btn">
                    ⚽ Simulate Next ${leagueName} Round
                </button>
            </div>
        </div>
    `;
    
    mainContent.innerHTML = tableHtml;
}

async function simulateAFLRound() {
    try {
        // Get active AFL season
        const seasonsData = await apiRequest('/management/seasons/active');
        const aflSeasons = seasonsData.active_seasons.filter(s => s.tier === 0);
        
        if (aflSeasons.length === 0) {
            showError('No active AFL season found');
            return;
        }
        
        const seasonId = aflSeasons[0].season_id;
        const currentRound = aflSeasons[0].current_round;
        
        const result = await apiRequest('/matches/simulate-round', 'POST', {
            season_id: seasonId,
            round: currentRound
        });
        
        if (result.matches_played) {
            displaySimulationResults(result, 'AFL', currentRound);
        } else {
            showError('No matches to simulate');
        }
    } catch (error) {
        showError(`Failed to simulate AFL round: ${error.message}`);
    }
}

async function simulateVFLRound() {
    try {
        // Get active VFL season
        const seasonsData = await apiRequest('/management/seasons/active');
        const vflSeasons = seasonsData.active_seasons.filter(s => s.tier === 1);
        
        if (vflSeasons.length === 0) {
            showError('No active VFL season found');
            return;
        }
        
        const seasonId = vflSeasons[0].season_id;
        const currentRound = vflSeasons[0].current_round;
        
        const result = await apiRequest('/matches/simulate-round', 'POST', {
            season_id: seasonId,
            round: currentRound
        });
        
        if (result.matches_played) {
            displaySimulationResults(result, 'VFL', currentRound);
        } else {
            showError('No matches to simulate');
        }
    } catch (error) {
        showError(`Failed to simulate VFL round: ${error.message}`);
    }
}

function displaySimulationResults(result, leagueName, roundNumber) {
    const mainContent = document.getElementById('main-content');
    
    let resultsHtml = `
        <div class="simulation-results">
            <h2>⚽ ${leagueName} Round ${roundNumber} Results</h2>
            <p>✅ Simulated ${result.matches_played} matches</p>
            
            <div class="match-results">
    `;
    
    if (result.results && result.results.length > 0) {
        result.results.forEach(match => {
            const winner = match.home_score > match.away_score ? match.home_club :
                         match.away_score > match.home_score ? match.away_club : 'Draw';
            
            resultsHtml += `
                <div class="match-result">
                    <div class="teams">${match.home_club} vs ${match.away_club}</div>
                    <div class="score">${match.home_score} - ${match.away_score}</div>
                    <div class="winner">${winner === 'Draw' ? 'Draw' : 'Winner: ' + winner}</div>
                </div>
            `;
        });
    }
    
    resultsHtml += `
            </div>
            
            <div style="margin-top: 30px;">
                <button onclick="show${leagueName}Ladder()" class="action-btn">
                    📊 View Updated ${leagueName} Ladder
                </button>
                <button onclick="simulate${leagueName}Round()" class="sim-btn">
                    ⚽ Simulate Next Round
                </button>
            </div>
        </div>
    `;
    
    mainContent.innerHTML = resultsHtml;
}

async function showClubs() {
    try {
        const clubsData = await apiRequest('/clubs');
        
        if (!clubsData.clubs) {
            showError('No clubs data available');
            return;
        }
        
        const aflClubs = clubsData.clubs.filter(c => c.tier === 0);
        const vflClubs = clubsData.clubs.filter(c => c.tier === 1);
        
        const mainContent = document.getElementById('main-content');
        
        let clubsHtml = `
            <div class="clubs-section">
                <h2>🏟️ AFL & VFL Clubs</h2>
                
                <h3 style="margin-top: 30px; color: #1e3c72;">AFL Clubs (${aflClubs.length})</h3>
                <table class="clubs-table">
                    <thead>
                        <tr>
                            <th>Club Name</th>
                            <th>Nickname</th>
                            <th>Primary Colour</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        aflClubs.forEach(club => {
            clubsHtml += `
                <tr>
                    <td><strong>${club.name}</strong></td>
                    <td>${club.nickname}</td>
                    <td>
                        <span style="background-color: ${club.primary_colour}; color: white; padding: 2px 8px; border-radius: 4px;">
                            ${club.primary_colour}
                        </span>
                    </td>
                </tr>
            `;
        });
        
        clubsHtml += `
                    </tbody>
                </table>
                
                <h3 style="margin-top: 30px; color: #1e3c72;">VFL Clubs (${vflClubs.length})</h3>
                <table class="clubs-table">
                    <thead>
                        <tr>
                            <th>Club Name</th>
                            <th>Nickname</th>
                            <th>Primary Colour</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        vflClubs.forEach(club => {
            clubsHtml += `
                <tr>
                    <td><strong>${club.name}</strong></td>
                    <td>${club.nickname}</td>
                    <td>
                        <span style="background-color: ${club.primary_colour}; color: white; padding: 2px 8px; border-radius: 4px;">
                            ${club.primary_colour}
                        </span>
                    </td>
                </tr>
            `;
        });
        
        clubsHtml += `
                    </tbody>
                </table>
            </div>
        `;
        
        mainContent.innerHTML = clubsHtml;
    } catch (error) {
        showError(`Failed to load clubs: ${error.message}`);
    }
}

async function showSeasonStatus() {
    try {
        const seasonsData = await apiRequest('/management/seasons/active');
        
        if (!seasonsData.active_seasons || seasonsData.active_seasons.length === 0) {
            showError('No active seasons found');
            return;
        }
        
        const mainContent = document.getElementById('main-content');
        
        let statusHtml = `
            <div class="season-status">
                <h2>📋 Season Status</h2>
                <div class="season-cards">
        `;
        
        seasonsData.active_seasons.forEach(season => {
            const leagueName = season.tier === 0 ? 'AFL' : 'VFL';
            const progress = Math.round((season.current_round / season.total_rounds) * 100);
            
            statusHtml += `
                <div class="season-card">
                    <h3>${leagueName} Season ${season.year}</h3>
                    <p>Round ${season.current_round} of ${season.total_rounds}</p>
                    <p>${progress}% Complete</p>
                    <div style="margin-top: 15px;">
                        <button onclick="show${leagueName}Ladder()" class="sim-btn">View Ladder</button>
                        <button onclick="simulate${leagueName}Round()" class="sim-btn">Simulate Round</button>
                    </div>
                </div>
            `;
        });
        
        statusHtml += `
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <button onclick="simulateFullSeason()" class="action-btn" 
                            style="background: linear-gradient(135deg, #5f27cd, #341f97);">
                        ⚡ Simulate Remaining Rounds
                    </button>
                </div>
            </div>
        `;
        
        mainContent.innerHTML = statusHtml;
    } catch (error) {
        showError(`Failed to load season status: ${error.message}`);
    }
}

async function simulateFullSeason() {
    if (!confirm('This will simulate all remaining rounds for both AFL and VFL seasons. Continue?')) {
        return;
    }
    
    try {
        const seasonsData = await apiRequest('/management/seasons/active');
        
        for (const season of seasonsData.active_seasons) {
            const leagueName = season.tier === 0 ? 'AFL' : 'VFL';
            
            // Simulate remaining rounds
            for (let round = season.current_round; round <= season.total_rounds; round++) {
                await apiRequest('/matches/simulate-round', 'POST', {
                    season_id: season.season_id,
                    round: round
                });
            }
        }
        
        showSuccess('🏆 Full season simulation complete! Check the ladders to see final standings.');
        
        // Show updated season status
        setTimeout(() => {
            showSeasonStatus();
        }, 2000);
        
    } catch (error) {
        showError(`Failed to simulate full season: ${error.message}`);
    }
}

async function resetGame() {
    const confirmMessage = `🔄 Reset Game
    
This will:
• Delete all current season progress
• Reset all teams to fresh state  
• Create new AFL/VFL seasons
• Generate new player rosters

Are you sure you want to start over?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        showLoading();
        const result = await apiRequest('/management/reset-game', 'POST');
        
        if (result.status === 'success') {
            const mainContent = document.getElementById('main-content');
            mainContent.innerHTML = `
                <div class="success-message">
                    <h2>🎉 Game Reset Complete!</h2>
                    <p>${result.message}</p>
                    <p>Fresh AFL and VFL seasons are ready to play.</p>
                    
                    <div style="margin-top: 20px;">
                        <button onclick="showAFLLadder()" class="action-btn">
                            📊 View New AFL Ladder
                        </button>
                        <button onclick="showSeasonStatus()" class="action-btn">
                            📋 Check Season Status
                        </button>
                    </div>
                </div>
            `;
        } else {
            showError('Failed to reset game');
        }
        
    } catch (error) {
        showError(`Failed to reset game: ${error.message}`);
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    console.log('AFL Manager Web Interface loaded');
    
    // Test API connection
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            console.log('API Health Check:', data);
        })
        .catch(error => {
            console.error('API connection failed:', error);
            showError('Could not connect to AFL Manager API. Please make sure the server is running.');
        });
});