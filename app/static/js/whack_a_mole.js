let gameActive = false;
let score = 0;
let timeLeft = 30;
let gameInterval = null;
let moleTimeout = null;

const scoreEl = document.getElementById('score');
const timeEl = document.getElementById('time');
const startBtn = document.getElementById('start-btn');
const restartBtn = document.getElementById('restart-btn');
const gameBoardEl = document.getElementById('game-board');
const gameOverEl = document.getElementById('game-over');
const finalScoreEl = document.getElementById('final-score');
const submitScoreBtn = document.getElementById('submit-score-btn');

const holes = document.querySelectorAll('.hole');

startBtn.addEventListener('click', startGame);
restartBtn.addEventListener('click', resetGame);

function startGame() {
    gameActive = true;
    score = 0;
    timeLeft = 30;
    
    scoreEl.textContent = '0';
    timeEl.textContent = '30';
    startBtn.style.display = 'none';
    gameOverEl.style.display = 'none';
    
    setupGame();
    
    gameInterval = setInterval(() => {
        timeLeft--;
        timeEl.textContent = timeLeft;
        
        if (timeLeft <= 0) {
            endGame();
        }
    }, 1000);
}

function setupGame() {
    holes.forEach((hole, index) => {
        hole.addEventListener('click', () => {
            if (!gameActive) return;
            
            const mole = hole.querySelector('.mole');
            if (mole.classList.contains('up')) {
                mole.classList.remove('up');
                score += 10;
                scoreEl.textContent = score;
                
                hole.classList.add('hit');
                setTimeout(() => {
                    hole.classList.remove('hit');
                }, 200);
            }
        });
    });
    
    showRandomMole();
}

function showRandomMole() {
    if (!gameActive) return;
    
    holes.forEach(hole => {
        const mole = hole.querySelector('.mole');
        mole.classList.remove('up');
    });
    
    const randomHole = holes[Math.floor(Math.random() * holes.length)];
    const mole = randomHole.querySelector('.mole');
    
    mole.classList.add('up');
    
    moleTimeout = setTimeout(() => {
        mole.classList.remove('up');
        if (gameActive) {
            showRandomMole();
        }
    }, 800 + Math.random() * 400);
}

function endGame() {
    gameActive = false;
    clearInterval(gameInterval);
    
    if (moleTimeout) {
        clearTimeout(moleTimeout);
    }
    
    holes.forEach(hole => {
        const mole = hole.querySelector('.mole');
        mole.classList.remove('up');
    });
    
    finalScoreEl.textContent = score;
    gameOverEl.style.display = 'block';
    restartBtn.style.display = 'inline-block';
}

function resetGame() {
    gameOverEl.style.display = 'none';
    restartBtn.style.display = 'none';
    startBtn.style.display = 'inline-block';
}

submitScoreBtn.addEventListener('click', async () => {
    const gameSlug = 'whack-a-mole';
    
    try {
        const response = await fetch('/games/submit-score', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                game_slug: gameSlug,
                score: score
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            submitScoreBtn.textContent = 'Score Submitted!';
            submitScoreBtn.disabled = true;
            submitScoreBtn.classList.remove('btn-primary');
            submitScoreBtn.classList.add('btn-secondary');
        }
    } catch (error) {
        console.error('Error submitting score:', error);
        submitScoreBtn.textContent = 'Failed to submit';
    }
});
