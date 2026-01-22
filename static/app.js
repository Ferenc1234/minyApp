// Global state
let apiToken = null;
let currentUser = null;
let currentGame = null;
const API_BASE = '/api';

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    handleReferralLanding();

    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
        apiToken = token;
        showGameScreen();
        loadUserProfile();
    } else {
        showAuthScreen();
    }

    // Live update grid preview when settings change (before game starts)
    const gridSizeSelect = document.getElementById('grid-size');
    const minesInput = document.getElementById('mines-count');
    const betInput = document.getElementById('bet-amount');

    const settingsHandler = () => {
        handleSettingsChange();
    };

    if (gridSizeSelect) {
        gridSizeSelect.addEventListener('change', settingsHandler);
    }
    if (minesInput) {
        minesInput.addEventListener('change', settingsHandler);
    }
    if (betInput) {
        betInput.addEventListener('change', settingsHandler);
    }

    // Initial UI state
    setSettingsState(false);
    renderMineGrid();
});

function handleReferralLanding() {
    const params = new URLSearchParams(window.location.search);
    const refCode = params.get('ref');

    if (refCode) {
        localStorage.setItem('referral_code', refCode);
        fetch(`${API_BASE}/referrals/track?code=${encodeURIComponent(refCode)}`)
            .catch(() => {});
    }
}

// Helper to extract meaningful error messages from API responses
async function getErrorMessage(response, fallbackMessage) {
    let message = fallbackMessage;
    try {
        const data = await response.json();

        if (typeof data.detail === 'string') {
            message = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
            const first = data.detail[0];
            if (typeof first === 'string') {
                message = first;
            } else if (first && typeof first.msg === 'string') {
                message = first.msg;
            }
        } else if (typeof data.message === 'string') {
            message = data.message;
        }
    } catch (e) {
        // If parsing fails, fall back to the provided message
    }

    return message;
}

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
            const message = await getErrorMessage(response, 'Login failed');
            throw new Error(message);
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
    const password = document.getElementById('register-password').value;
    const errorDiv = document.getElementById('register-error');
    const referralCode = localStorage.getItem('referral_code');
    
    if (!username || !password) {
        showError(errorDiv, 'Please fill in username and password');
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
            body: JSON.stringify({
                username,
                password,
                referral_code: referralCode || null
            })
        });
        
        if (!response.ok) {
            const message = await getErrorMessage(response, 'Registration failed');
            throw new Error(message);
        }
        
        const data = await response.json();
        apiToken = data.access_token;
        currentUser = data.user;
        
        localStorage.setItem('token', apiToken);
        localStorage.removeItem('referral_code');
        
        showGameScreen();
        updateUserDisplay();
        loadUserProfile();
        
    } catch (error) {
        showError(errorDiv, error.message);
    }
}

function toggleAddMoney() {
    const actions = document.getElementById('add-money-actions');
    if (!actions) return;
    actions.classList.toggle('open');
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
    document.getElementById('register-password').value = '';
    
    showAuthScreen();
}

// Game Functions
async function handlePrimaryGameAction() {
    if (currentGame && currentGame.status === 'active') {
        await claimPrize();
    } else {
        await startGame();
    }
}

async function startGame() {
    const betAmount = parseFloat(document.getElementById('bet-amount').value);
    const gridSize = parseInt(document.getElementById('grid-size').value);
    const minesCount = parseInt(document.getElementById('mines-count').value);
    const errorDiv = document.getElementById('setup-error');
    
    // Ensure we have an up-to-date user profile (especially after page refresh)
    if (!currentUser) {
        await loadUserProfile();
    }

    if (!currentUser) {
        showError(errorDiv, 'Please log in again to start a game.');
        return;
    }

    if (isNaN(betAmount) || betAmount <= 0) {
        showError(errorDiv, 'Please enter a valid bet amount.');
        return;
    }

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
            const message = await getErrorMessage(response, 'Failed to create game');
            throw new Error(message);
        }
        
        currentGame = await response.json();

        // Refresh user profile so balance reflects the placed bet
        await loadUserProfile();

        // Lock settings and switch primary button to claim mode
        setSettingsState(true);

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
            const message = await getErrorMessage(response, 'Click failed');
            throw new Error(message);
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
            // Game ended: unlock settings and keep board visible/frozen
            setSettingsState(false);
            renderMineGrid();
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
            const message = await getErrorMessage(response, 'Failed to claim prize');
            throw new Error(message);
        }
        
        const result = await response.json();
        
        // Update game state
        currentGame.status = result.status;
        currentGame.prize_amount = result.prize_amount;
        
        // Update user balance
        await loadUserProfile();

        // Game ended: unlock settings and keep board visible/frozen
        setSettingsState(false);
        renderMineGrid();

        showGameMessage(result.message);
        
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
    // Prepare preview state: no active game, grid greyed out, settings enabled
    currentGame = null;
    hideAllSections();
    document.getElementById('play-screen').classList.add('active');
    document.getElementById('setup-error').classList.remove('show');
    setSettingsState(false);
    const gridDiv = document.getElementById('mine-grid');
    if (gridDiv) {
        gridDiv.classList.add('disabled');
    }
    renderMineGrid();
}

function showPlayScreen() {
    hideAllSections();
    document.getElementById('play-screen').classList.add('active');
    const gridDiv = document.getElementById('mine-grid');
    if (gridDiv) {
        gridDiv.classList.remove('disabled');
    }
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

        // Append casino stats as a special row at the bottom
        try {
            const casinoResp = await fetch(`${API_BASE}/casino/stats`, {
                headers: getAuthHeaders()
            });
            if (casinoResp.ok) {
                const casino = await casinoResp.json();
                const row = tbody.insertRow();
                row.classList.add('casino-row');
                row.innerHTML = `
                    <td>-</td>
                    <td>Casino (House)</td>
                    <td>-</td>
                    <td>$${casino.total_wagered.toFixed(2)}</td>
                    <td>$${casino.total_won.toFixed(2)}</td>
                    <td>${casino.casino_edge_percent}% edge</td>
                    <td>$${casino.casino_profit.toFixed(2)}</td>
                `;
            }
        } catch (e) {
            console.error('Casino stats error:', e);
        }

        document.getElementById('leaderboard-screen').classList.remove('hidden');
        
    } catch (error) {
        console.error('Leaderboard error:', error);
        alert('Failed to load leaderboard');
    }
}

function renderMineGrid() {
    const gridDiv = document.getElementById('mine-grid');
    if (!gridDiv) return;
    gridDiv.innerHTML = '';

    // Use current game size when active, otherwise preview based on selected grid size
    const selectedSize = parseInt(document.getElementById('grid-size').value) || 3;
    const gridSize = currentGame ? currentGame.grid_size : selectedSize;

    const classes = ['mine-grid', `grid-${gridSize}`];
    if (!currentGame || (currentGame && currentGame.status !== 'active')) {
        classes.push('disabled');
    }
    gridDiv.className = classes.join(' ');

    for (let row = 0; row < gridSize; row++) {
        for (let col = 0; col < gridSize; col++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            
            if (currentGame) {
                const cellKey = `${row},${col}`;
                const isRevealed = currentGame.revealed_cells[cellKey] !== undefined;
                const status = currentGame.status;

                if (status === 'active') {
                    // Standard in-play behavior: only show revealed cells, others clickable
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
                } else {
                    // Game finished: reveal full board based on revealed_cells
                    if (isRevealed) {
                        cell.classList.add('revealed');
                        if (currentGame.revealed_cells[cellKey]) {
                            cell.classList.add('mine');
                            cell.textContent = '💣';
                        } else {
                            cell.classList.add('safe');
                            cell.textContent = '✓';
                        }
                    }
                }
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
    const balanceDisplay = document.getElementById('balance-display');
    if (balanceDisplay) {
        balanceDisplay.textContent = currentUser.balance.toFixed(2);
    }
    const balanceMain = document.getElementById('balance-main');
    if (balanceMain) {
        balanceMain.textContent = currentUser.balance.toFixed(2);
    }
}

async function createReferralLink() {
    const statusEl = document.getElementById('affiliate-link-status');
    const inputEl = document.getElementById('affiliate-link-input');

    if (!apiToken) {
        if (statusEl) statusEl.textContent = 'Please log in to generate a link.';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/referrals/create`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            const message = await getErrorMessage(response, 'Failed to create referral link');
            throw new Error(message);
        }

        const data = await response.json();
        if (inputEl) {
            inputEl.value = data.url;
        }
        if (data.url && navigator.clipboard) {
            try {
                await navigator.clipboard.writeText(data.url);
                if (statusEl) {
                    statusEl.textContent = 'Link copied. You get $500 per registration.';
                }
            } catch (error) {
                if (statusEl) {
                    statusEl.textContent = 'Link ready. Copy it to share and earn $500 per registration.';
                }
            }
        } else if (statusEl) {
            statusEl.textContent = 'Link ready. Copy it to share and earn $500 per registration.';
        }
    } catch (error) {
        if (statusEl) statusEl.textContent = error.message;
    }
}

function copyAffiliateLink() {
    const inputEl = document.getElementById('affiliate-link-input');
    const statusEl = document.getElementById('affiliate-link-status');
    if (!inputEl || !inputEl.value) {
        if (statusEl) statusEl.textContent = 'Generate a link first.';
        return;
    }

    inputEl.select();
    inputEl.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(inputEl.value).then(() => {
        if (statusEl) statusEl.textContent = 'Link copied. You get $500 per registration.';
    }).catch(() => {
        if (statusEl) statusEl.textContent = 'Copy failed. Please copy manually.';
    });
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

function setSettingsState(isActiveGame) {
    const betInput = document.getElementById('bet-amount');
    const gridSizeSelect = document.getElementById('grid-size');
    const minesInput = document.getElementById('mines-count');
    const primaryButton = document.getElementById('primary-game-button');

    if (!betInput || !gridSizeSelect || !minesInput || !primaryButton) return;

    betInput.disabled = isActiveGame;
    gridSizeSelect.disabled = isActiveGame;
    minesInput.disabled = isActiveGame;

    primaryButton.textContent = isActiveGame ? 'Claim Prize' : 'Start Game';
}

function handleSettingsChange() {
    // If the previous game has finished, clear it and show a fresh preview
    if (currentGame && currentGame.status !== 'active') {
        currentGame = null;
        showGameMessage('');
    }

    const gridDiv = document.getElementById('mine-grid');
    if (gridDiv && !currentGame) {
        gridDiv.classList.add('disabled');
    }

    renderMineGrid();
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
