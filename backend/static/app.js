// AFL Manager - Team Manager Edition JavaScript

const API_BASE = '/api/v1';
let selectedTeam = null;
let selectedTeamLeague = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    console.log('AFL Manager Team Edition loaded');
    
    // Check if user has a saved team
    const savedTeam = localStorage.getItem('selectedTeam');
    if (savedTeam) {
        try {
            const teamData = JSON.parse(savedTeam);
            selectedTeam = teamData;
            selectedTeamLeague = teamData.tier === 0 ? 'afl' : 'vfl';
            showDashboard();
        } catch (error) {
            console.error('Error loading saved team:', error);
            showTeamSelection();
        }
    } else {
        showTeamSelection();
    }
    
    // Test API connection
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            console.log('API Health Check:', data);
        })
        .catch(error => {
            console.error('API connection failed:', error);
        });
});

// Screen Management
function showTeamSelection() {
    document.getElementById('team-selection').classList.remove('hidden');
    document.getElementById('team-dashboard').classList.add('hidden');
    
    // Hide team grid initially
    document.getElementById('team-grid').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('team-selection').classList.add('hidden');
    document.getElementById('team-dashboard').classList.remove('hidden');
    
    // Update team info in header
    document.getElementById('team-name').textContent = selectedTeam.name;
    document.getElementById('team-league').textContent = selectedTeam.tier === 0 ? 'AFL' : 'VFL';
    
    // Load dashboard content
    loadDashboardContent();
}

// Team Selection Functions
async function showTeams(league) {
    try {
        showLoading();
        const clubsData = await apiRequest('/clubs');
        
        if (!clubsData.clubs) {
            showError('Could not load teams');
            return;
        }
        
        const teams = clubsData.clubs.filter(club => 
            league === 'afl' ? club.tier === 0 : club.tier === 1
        );
        
        displayTeamGrid(teams, league);
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showError(`Failed to load teams: ${error.message}`);
    }
}

function displayTeamGrid(teams, league) {
    const teamGrid = document.getElementById('team-grid');
    teamGrid.innerHTML = '';
    
    teams.forEach(team => {
        const teamCard = document.createElement('div');
        teamCard.className = 'team-card';
        teamCard.onclick = () => selectTeam(team, league);
        
        teamCard.innerHTML = `
            <div class="team-colors">
                <div class="color-dot" style="background-color: ${team.primary_colour}"></div>
                ${team.secondary_colour ? `<div class="color-dot" style="background-color: ${team.secondary_colour}"></div>` : ''}
            </div>
            <h3>${team.name}</h3>
            <p>${team.nickname}</p>
        `;
        
        teamGrid.appendChild(teamCard);
    });
    
    teamGrid.classList.remove('hidden');
}

function selectTeam(team, league) {
    selectedTeam = team;
    selectedTeamLeague = league;
    
    // Save to localStorage
    localStorage.setItem('selectedTeam', JSON.stringify(team));
    
    showDashboard();
}

function changeTeam() {
    selectedTeam = null;
    selectedTeamLeague = null;
    localStorage.removeItem('selectedTeam');
    showTeamSelection();
}

// Dashboard Content Loading
async function loadDashboardContent() {
    try {
        await Promise.all([
            loadLadderTile(),
            loadNextMatchTile(),
            loadRosterTile(),
            loadSeasonProgressTile()
        ]);
    } catch (error) {
        console.error('Error loading dashboard content:', error);
    }
}

async function loadLadderTile() {
    try {
        // Get active seasons
        const seasonsData = await apiRequest('/management/seasons/active');
        const relevantSeasons = seasonsData.active_seasons.filter(s => s.tier === selectedTeam.tier);
        
        if (relevantSeasons.length === 0) {
            document.getElementById('ladder-content').innerHTML = '<p>No active season found</p>';
            return;
        }
        
        const seasonId = relevantSeasons[0].season_id;
        const ladderData = await apiRequest(`/seasons/${seasonId}/ladder`);
        
        if (!ladderData.ladder) {
            document.getElementById('ladder-content').innerHTML = '<p>No ladder data available</p>';
            return;
        }
        
        displayLadderTile(ladderData.ladder);
        
    } catch (error) {
        document.getElementById('ladder-content').innerHTML = '<p class="error">Failed to load ladder</p>';
    }
}

function displayLadderTile(ladder) {
    const userTeamPos = ladder.findIndex(team => team.club_name === selectedTeam.name) + 1;
    
    // Show top 5 teams plus user team if not in top 5
    let displayTeams = ladder.slice(0, 5);
    
    if (userTeamPos > 5) {
        displayTeams.push(ladder[userTeamPos - 1]);
    }
    
    let html = '<div class="ladder-mini"><table>';
    html += '<tr><th>Pos</th><th>Team</th><th>W-L</th><th>Pts</th></tr>';
    
    displayTeams.forEach((team, index) => {
        const actualPos = userTeamPos > 5 && index === 5 ? userTeamPos : index + 1;
        const isUserTeam = team.club_name === selectedTeam.name;
        const rowClass = isUserTeam ? 'user-team' : '';
        
        html += `
            <tr class="${rowClass}">
                <td>${actualPos}</td>
                <td>${team.club_name}</td>
                <td>${team.wins}-${team.losses}</td>
                <td>${team.ladder_points}</td>
            </tr>
        `;
    });
    
    html += '</table></div>';
    document.getElementById('ladder-content').innerHTML = html;
}

async function loadNextMatchTile() {
    try {
        // Get active seasons
        const seasonsData = await apiRequest('/management/seasons/active');
        const relevantSeasons = seasonsData.active_seasons.filter(s => s.tier === selectedTeam.tier);
        
        if (relevantSeasons.length === 0) {
            document.getElementById('next-match-content').innerHTML = '<p>No active season found</p>';
            return;
        }
        
        const seasonId = relevantSeasons[0].season_id;
        const currentRound = relevantSeasons[0].current_round;
        
        // Get fixtures for current round
        const fixturesData = await apiRequest(`/seasons/${seasonId}/fixtures?round=${currentRound}`);
        
        if (!fixturesData.fixtures) {
            document.getElementById('next-match-content').innerHTML = '<p>No fixtures available</p>';
            return;
        }
        
        // Find user's team fixture
        const userFixture = fixturesData.fixtures.find(fixture => 
            fixture.home_club.name === selectedTeam.name || fixture.away_club.name === selectedTeam.name
        );
        
        if (userFixture) {
            displayNextMatchTile(userFixture, currentRound);
        } else {
            document.getElementById('next-match-content').innerHTML = '<p>No upcoming matches found</p>';
        }
        
    } catch (error) {
        document.getElementById('next-match-content').innerHTML = '<p class="error">Failed to load match info</p>';
    }
}

function displayNextMatchTile(fixture, round) {
    const isHome = fixture.home_club.name === selectedTeam.name;
    const opponent = isHome ? fixture.away_club.name : fixture.home_club.name;
    const venue = isHome ? 'Home' : 'Away';
    
    const html = `
        <div class="next-match">
            <div class="match-teams">
                ${selectedTeam.name} vs ${opponent}
            </div>
            <div class="match-details">
                Round ${round} • ${venue}
            </div>
        </div>
    `;
    
    document.getElementById('next-match-content').innerHTML = html;
}

async function loadRosterTile() {
    try {
        const playersData = await apiRequest(`/players?club_id=${selectedTeam.id}`);
        
        if (!playersData.players) {
            document.getElementById('roster-content').innerHTML = '<p>No roster data available</p>';
            return;
        }
        
        displayRosterTile(playersData.players);
        
    } catch (error) {
        document.getElementById('roster-content').innerHTML = '<p class="error">Failed to load roster</p>';
    }
}

function displayRosterTile(players) {
    // Group players by position
    const positions = {
        'Forwards': ['KPF', 'SMALL_FWD'],
        'Midfield': ['MID'],
        'Defence': ['HALF_BACK', 'KP_BACK'],
        'Ruck': ['RUCK'],
        'Utility': ['UTILITY']
    };
    
    let html = '<div class="roster-mini">';
    
    Object.entries(positions).forEach(([groupName, positionCodes]) => {
        const groupPlayers = players.filter(p => positionCodes.includes(p.position));
        
        if (groupPlayers.length > 0) {
            html += `
                <div class="position-group">
                    <h4>${groupName} (${groupPlayers.length})</h4>
                    <div class="player-list">
                        ${groupPlayers.slice(0, 3).map(p => 
                            `<span class="player-tag">${p.name}</span>`
                        ).join('')}
                        ${groupPlayers.length > 3 ? `<span class="player-tag">+${groupPlayers.length - 3} more</span>` : ''}
                    </div>
                </div>
            `;
        }
    });
    
    html += '</div>';
    document.getElementById('roster-content').innerHTML = html;
}

async function loadSeasonProgressTile() {
    try {
        const seasonsData = await apiRequest('/management/seasons/active');
        const relevantSeasons = seasonsData.active_seasons.filter(s => s.tier === selectedTeam.tier);
        
        if (relevantSeasons.length === 0) {
            document.getElementById('season-progress-content').innerHTML = '<p>No active season found</p>';
            return;
        }
        
        const season = relevantSeasons[0];
        displaySeasonProgressTile(season);
        
    } catch (error) {
        document.getElementById('season-progress-content').innerHTML = '<p class="error">Failed to load season info</p>';
    }
}

function displaySeasonProgressTile(season) {
    const progress = Math.round((season.current_round / season.total_rounds) * 100);
    
    const html = `
        <div class="season-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            <div class="progress-text">
                Round ${season.current_round} of ${season.total_rounds}
                <br>
                ${progress}% Complete
            </div>
        </div>
    `;
    
    document.getElementById('season-progress-content').innerHTML = html;
}

// Action Functions
async function simulateNextMatch() {
    try {
        showLoading();
        
        // Get current season info
        const seasonsData = await apiRequest('/management/seasons/active');
        const relevantSeasons = seasonsData.active_seasons.filter(s => s.tier === selectedTeam.tier);
        
        if (relevantSeasons.length === 0) {
            showError('No active season found');
            return;
        }
        
        const seasonId = relevantSeasons[0].season_id;
        const currentRound = relevantSeasons[0].current_round;
        
        // Simulate the round
        const result = await apiRequest('/matches/simulate-round', 'POST', {
            season_id: seasonId,
            round: currentRound
        });
        
        hideLoading();
        
        if (result.matches_played) {
            showSuccess(`Round ${currentRound} simulated! Your team's result has been updated.`);
            
            // Refresh dashboard content
            setTimeout(() => {
                loadDashboardContent();
            }, 2000);
        } else {
            showError('No matches to simulate');
        }
        
    } catch (error) {
        hideLoading();
        showError(`Failed to simulate match: ${error.message}`);
    }
}

async function viewFullLadder() {
    try {
        const seasonsData = await apiRequest('/management/seasons/active');
        const relevantSeasons = seasonsData.active_seasons.filter(s => s.tier === selectedTeam.tier);
        
        if (relevantSeasons.length === 0) {
            showError('No active season found');
            return;
        }
        
        const seasonId = relevantSeasons[0].season_id;
        const ladderData = await apiRequest(`/seasons/${seasonId}/ladder`);
        
        if (!ladderData.ladder) {
            showError('No ladder data available');
            return;
        }
        
        displayFullLadder(ladderData.ladder);
        
    } catch (error) {
        showError(`Failed to load full ladder: ${error.message}`);
    }
}

function displayFullLadder(ladder) {
    const leagueName = selectedTeam.tier === 0 ? 'AFL' : 'VFL';
    
    let html = `
        <div class="full-ladder">
            <h2>${leagueName} Ladder</h2>
            <table class="ladder-table">
                <thead>
                    <tr>
                        <th>Pos</th>
                        <th>Team</th>
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
        const isUserTeam = team.club_name === selectedTeam.name;
        const rowClass = isUserTeam ? 'user-team' : '';
        
        html += `
            <tr class="${rowClass}">
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
    
    html += `
                </tbody>
            </table>
            <button onclick="loadDashboardContent()" class="tile-btn">Back to Dashboard</button>
        </div>
    `;
    
    // Replace dashboard with full ladder view
    document.querySelector('.dashboard-tiles').innerHTML = html;
}

async function viewFullRoster() {
    try {
        const playersData = await apiRequest(`/players?club_id=${selectedTeam.id}`);
        
        if (!playersData.players) {
            showError('No roster data available');
            return;
        }
        
        displayFullRoster(playersData.players);
        
    } catch (error) {
        showError(`Failed to load full roster: ${error.message}`);
    }
}

function displayFullRoster(players) {
    let html = `
        <div class="full-roster">
            <h2>${selectedTeam.name} Roster</h2>
            <table class="roster-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Position</th>
                        <th>Age</th>
                        <th>Overall</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Sort players by overall rating (average of key stats)
    players.sort((a, b) => {
        const overallA = Math.round((a.kicking + a.handball + a.marking + a.speed + a.endurance) / 5);
        const overallB = Math.round((b.kicking + b.handball + b.marking + b.speed + b.endurance) / 5);
        return overallB - overallA;
    });
    
    players.forEach(player => {
        const overall = Math.round((player.kicking + player.handball + player.marking + player.speed + player.endurance) / 5);
        
        html += `
            <tr>
                <td><strong>${player.name}</strong></td>
                <td>${player.position}</td>
                <td>${player.age}</td>
                <td>${overall}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
            <button onclick="loadDashboardContent()" class="tile-btn">Back to Dashboard</button>
        </div>
    `;
    
    // Replace dashboard with full roster view
    document.querySelector('.dashboard-tiles').innerHTML = html;
}

async function simulateToEndOfSeason() {
    if (!confirm('This will simulate all remaining rounds of the season. Continue?')) {
        return;
    }
    
    try {
        showLoading();
        
        const seasonsData = await apiRequest('/management/seasons/active');
        const relevantSeasons = seasonsData.active_seasons.filter(s => s.tier === selectedTeam.tier);
        
        if (relevantSeasons.length === 0) {
            showError('No active season found');
            return;
        }
        
        const season = relevantSeasons[0];
        
        // Simulate all remaining rounds
        for (let round = season.current_round; round <= season.total_rounds; round++) {
            await apiRequest('/matches/simulate-round', 'POST', {
                season_id: season.season_id,
                round: round
            });
        }
        
        hideLoading();
        showSuccess('Season simulation complete! Check the final ladder standings.');
        
        // Refresh dashboard
        setTimeout(() => {
            loadDashboardContent();
        }, 2000);
        
    } catch (error) {
        hideLoading();
        showError(`Failed to simulate season: ${error.message}`);
    }
}

// Game Management
async function resetGame() {
    const confirmMessage = `🔄 Reset Game

This will:
• Delete all current season progress
• Reset all teams to fresh state  
• Create new AFL/VFL seasons
• You'll need to pick a new team

Are you sure you want to start over?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        showLoading();
        const result = await apiRequest('/management/reset-game', 'POST');
        
        if (result.status === 'success') {
            // Clear saved team
            localStorage.removeItem('selectedTeam');
            selectedTeam = null;
            selectedTeamLeague = null;
            
            hideLoading();
            showSuccess('🎉 Game Reset Complete! Please select a new team.');
            
            // Return to team selection
            setTimeout(() => {
                showTeamSelection();
            }, 2000);
        } else {
            hideLoading();
            showError('Failed to reset game');
        }
        
    } catch (error) {
        hideLoading();
        showError(`Failed to reset game: ${error.message}`);
    }
}

// Utility Functions
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<h3>❌ Error</h3><p>${message}</p>`;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        document.body.removeChild(errorDiv);
    }, 5000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `<h3>✅ Success</h3><p>${message}</p>`;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        document.body.removeChild(successDiv);
    }, 5000);
}

async function apiRequest(endpoint, method = 'GET', data = null) {
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
    }
}