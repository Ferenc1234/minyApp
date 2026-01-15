// Global state
let apiToken = null;
let currentUser = null;
let currentGame = null;
const API_BASE = '/api';

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
        apiToken = token;
        showGameScreen();
        loadUserProfile();
    } else {
        showAuthScreen();
    }
});

// Auth Functions
async function handleLogin() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');
    
    if (!username || !password) {
        showError(errorDiv, 'Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Login failed');
        }
        
        const data = await response.json();
        apiToken = data.access_token;
        currentUser = data.user;
        
        localStorage.setItem('token', apiToken);
        
        showGameScreen();
        updateUserDisplay();
        loadUserProfile();
        
    } catch (error) {
        showError(errorDiv, error.message);
    }
}

async function handleRegister() {
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const errorDiv = document.getElementById('register-error');
    
    if (!username || !email || !password) {
        showError(errorDiv, 'Please fill in all fields');
        return;
    }
    
    if (password.length < 8) {
        showError(errorDiv, 'Password must be at least 8 characters');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Registration failed');
        }
        
        const data = await response.json();
        apiToken = data.access_token;
        currentUser = data.user;
        
        localStorage.setItem('token', apiToken);
        
        showGameScreen();
        updateUserDisplay();
        loadUserProfile();
        
    } catch (error) {
        showError(errorDiv, error.message);
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    apiToken = null;
    currentUser = null;
    currentGame = null;
    localStorage.removeItem('token');
    
    // Clear forms
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
    document.getElementById('register-username').value = '';
    document.getElementById('register-email').value = '';
    document.getElementById('register-password').value = '';
    
    showAuthScreen();
}

// Game Functions
async function startGame() {
    const betAmount = parseFloat(document.getElementById('bet-amount').value);
    const gridSize = parseInt(document.getElementById('grid-size').value);
    const minesCount = parseInt(document.getElementById('mines-count').value);
    const errorDiv = document.getElementById('setup-error');
    
    // Validation
    const totalCells = gridSize * gridSize;
    if (minesCount >= totalCells) {
        showError(errorDiv, `Too many mines for ${gridSize}x${gridSize} grid`);
        return;
    }
    
    if (betAmount > currentUser.balance) {
        showError(errorDiv, 'Insufficient balance');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/games/new`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                bet_amount: betAmount,
                grid_size: gridSize,
                mines_count: minesCount
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to create game');
        }
        
        currentGame = await response.json();
        showPlayScreen();
        renderMineGrid();
        updateGameInfo();
        
        errorDiv.classList.remove('show');
        
    } catch (error) {
        showError(errorDiv, error.message);
    }
}

async function clickCell(row, col) {
    if (!currentGame) return;
    
    try {
        const response = await fetch(`${API_BASE}/games/${currentGame.id}/click`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ row, col })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Click failed');
        }
        
        const result = await response.json();
        
        // Reload game state
        const gameResponse = await fetch(`${API_BASE}/games/${currentGame.id}`, {
            headers: getAuthHeaders()
        });
        
        currentGame = await gameResponse.json();
        
        updateGameInfo();
        renderMineGrid();
        
        showGameMessage(result.message);
        
        if (result.status !== 'active') {
            showGameOver(result);
        }
        
    } catch (error) {
        console.error('Click error:', error);
        showGameMessage('Error: ' + error.message);
    }
}

async function claimPrize() {
    if (!currentGame) return;
    
    try {
        const response = await fetch(`${API_BASE}/games/${currentGame.id}/claim`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to claim prize');
        }
        
        const result = await response.json();
        
        // Update game state
        currentGame.status = result.status;
        currentGame.prize_amount = result.prize_amount;
        
        // Update user balance
        loadUserProfile();
        
        showGameMessage(result.message);
        setTimeout(() => {
            showGameOver(result);
        }, 1000);
        
    } catch (error) {
        console.error('Claim error:', error);
        showGameMessage('Error: ' + error.message);
    }
}

function cancelGame() {
    currentGame = null;
    showSetup();
}

// UI Functions
function switchAuthTab(tab) {
    // Remove active from all tabs
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(form => form.classList.remove('active'));
    
    // Add active to clicked tab
    event.target.classList.add('active');
    document.getElementById(tab + '-form').classList.add('active');
}

function showAuthScreen() {
    document.getElementById('auth-screen').classList.add('active');
    document.getElementById('game-screen').classList.remove('active');
}

function showGameScreen() {
    document.getElementById('auth-screen').classList.remove('active');
    document.getElementById('game-screen').classList.add('active');
    showSetup();
}

function showSetup() {
    hideAllSections();
    document.getElementById('setup-screen').classList.add('active');
    document.getElementById('setup-error').classList.remove('show');
}

function showPlayScreen() {
    hideAllSections();
    document.getElementById('play-screen').classList.add('active');
}

function showGameOver(result) {
    hideAllSections();
    document.getElementById('gameover-screen').classList.add('active');
    
    if (result.status === 'won') {
        document.getElementById('gameover-title').textContent = '🎉 You Won!';
    } else if (result.status === 'lost') {
        document.getElementById('gameover-title').textContent = '💥 Game Over!';
    } else {
        document.getElementById('gameover-title').textContent = 'Game Ended';
    }
    
    document.getElementById('gameover-message').textContent = result.message;
    document.getElementById('final-prize').textContent = result.prize_amount.toFixed(2);
}

function hideAllSections() {
    document.querySelectorAll('.game-section').forEach(section => {
        section.classList.remove('active');
    });
}

async function showStats() {
    try {
        const response = await fetch(`${API_BASE}/user/stats`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) throw new Error('Failed to load stats');
        
        const stats = await response.json();
        
        const statsHtml = `
            <p><strong>Username:</strong> <span>${stats.username}</span></p>
            <p><strong>Current Balance:</strong> <span>$${stats.balance.toFixed(2)}</span></p>
            <p><strong>Total Games:</strong> <span>${stats.total_games}</span></p>
            <p><strong>Games Won:</strong> <span>${stats.won_games}</span></p>
            <p><strong>Games Lost:</strong> <span>${stats.lost_games}</span></p>
            <p><strong>Win Rate:</strong> <span>${stats.win_rate}%</span></p>
            <p><strong>Total Wagered:</strong> <span>$${stats.total_wagered.toFixed(2)}</span></p>
            <p><strong>Total Won:</strong> <span>$${stats.total_won.toFixed(2)}</span></p>
            <p><strong>ROI:</strong> <span>${stats.roi > 0 ? '+' : ''}${stats.roi}%</span></p>
            <p><strong>Joined:</strong> <span>${new Date(stats.joined).toLocaleDateString()}</span></p>
        `;
        
        document.getElementById('stats-content').innerHTML = statsHtml;
        document.getElementById('stats-screen').classList.remove('hidden');
        
    } catch (error) {
        console.error('Stats error:', error);
        alert('Failed to load statistics');
    }
}

async function showLeaderboard() {
    try {
        const response = await fetch(`${API_BASE}/user/leaderboard`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) throw new Error('Failed to load leaderboard');
        
        const data = await response.json();
        
        const tbody = document.getElementById('leaderboard-body');
        tbody.innerHTML = '';
        
        data.users.forEach(user => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${user.rank}</td>
                <td>${user.username}</td>
                <td>${user.total_games}</td>
                <td>$${user.total_wagered.toFixed(2)}</td>
                <td>$${user.total_won.toFixed(2)}</td>
                <td>${user.win_rate}%</td>
                <td>$${user.balance.toFixed(2)}</td>
            `;
        });
        
        document.getElementById('leaderboard-screen').classList.remove('hidden');
        
    } catch (error) {
        console.error('Leaderboard error:', error);
        alert('Failed to load leaderboard');
    }
}

function renderMineGrid() {
    if (!currentGame) return;
    
    const gridDiv = document.getElementById('mine-grid');
    gridDiv.innerHTML = '';
    gridDiv.className = `mine-grid grid-${currentGame.grid_size}`;
    
    for (let row = 0; row < currentGame.grid_size; row++) {
        for (let col = 0; col < currentGame.grid_size; col++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            
            const cellKey = `${row},${col}`;
            const isRevealed = currentGame.revealed_cells[cellKey] !== undefined;
            
            if (isRevealed) {
                cell.classList.add('revealed');
                if (currentGame.revealed_cells[cellKey]) {
                    cell.classList.add('mine');
                    cell.textContent = '💣';
                } else {
                    cell.classList.add('safe');
                    cell.textContent = '✓';
                }
            } else {
                cell.onclick = () => clickCell(row, col);
            }
            
            gridDiv.appendChild(cell);
        }
    }
}

function updateGameInfo() {
    if (!currentGame) return;
    
    document.getElementById('current-bet').textContent = currentGame.bet_amount.toFixed(2);
    document.getElementById('current-multiplier').textContent = currentGame.current_multiplier;
    document.getElementById('current-prize').textContent = currentGame.prize_amount.toFixed(2);
}

function updateUserDisplay() {
    if (!currentUser) return;
    
    document.getElementById('username-display').textContent = currentUser.username;
    document.getElementById('balance-display').textContent = currentUser.balance.toFixed(2);
}

async function loadUserProfile() {
    try {
        const response = await fetch(`${API_BASE}/user/profile`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) throw new Error('Failed to load profile');
        
        currentUser = await response.json();
        updateUserDisplay();
        
    } catch (error) {
        console.error('Profile error:', error);
    }
}

function showGameMessage(message) {
    const messageDiv = document.getElementById('game-message');
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
}

function showError(element, message) {
    element.textContent = message;
    element.classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiToken}`
    };
}
