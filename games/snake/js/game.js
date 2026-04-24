const FOOD_EMOJIS = {
    fruits: ['🍎', '🍊', '🍋', '🍇', '🍓', '🍑', '🍒', '🥝', '🍌', '🍉', '🫐', '🍈'],
    candies: ['🍬', '🍭', '🍫', '🧁', '🍩', '🍪', '🎂', '🍰', '🍨', '🍦', '🍧', '🍮'],
    animals: ['🐰', '🐭', '🐹', '🐀', '🐨', '🐼', '🐻', '🐱', '🐶', '🦊', '🐸', '🐵'],
    random: ['🍎', '🍊', '🍇', '🍓', '🍬', '🍭', '🍫', '🧁', '🍩', '🍪', '🎂', '🍰', '🐰', '🐭', '⭐', '💎', '🌟']
};

const DIRECTIONS = {
    UP: { x: 0, y: -1 },
    DOWN: { x: 0, y: 1 },
    LEFT: { x: -1, y: 0 },
    RIGHT: { x: 1, y: 0 }
};

const OPPOSITE_DIRECTIONS = {
    'UP': 'DOWN',
    'DOWN': 'UP',
    'LEFT': 'RIGHT',
    'RIGHT': 'LEFT'
};

class SnakeGame {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.settingsPanel = document.getElementById('settings-panel');
        this.gamePanel = document.getElementById('game-panel');
        this.gameoverPanel = document.getElementById('gameover-panel');
        this.pauseOverlay = document.getElementById('pause-overlay');
        
        this.scoreEl = document.getElementById('score');
        this.lengthEl = document.getElementById('length');
        this.speedDisplayEl = document.getElementById('speed-display');
        this.finalScoreEl = document.getElementById('final-score');
        this.finalLengthEl = document.getElementById('final-length');
        
        this.gridSizeSelect = document.getElementById('grid-size');
        this.speedSelect = document.getElementById('speed');
        this.snakeColorSelect = document.getElementById('snake-color');
        this.foodTypeSelect = document.getElementById('food-type');
        
        this.startBtn = document.getElementById('start-btn');
        this.playAgainBtn = document.getElementById('play-again-btn');
        this.backSettingsBtn = document.getElementById('back-settings-btn');
        
        this.initGame();
        this.bindEvents();
    }
    
    initGame() {
        this.gridSize = 20;
        this.cellSize = 25;
        this.baseSpeed = 150;
        this.speedMultiplier = 1;
        this.snakeColor = '#10b981';
        this.foodType = 'random';
        
        this.snake = [];
        this.direction = 'RIGHT';
        this.nextDirection = 'RIGHT';
        this.food = null;
        this.foodEmoji = '🍎';
        this.score = 0;
        this.isRunning = false;
        this.isPaused = false;
        this.gameLoop = null;
        this.eatCount = 0;
    }
    
    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startGame());
        this.playAgainBtn.addEventListener('click', () => this.startGame());
        this.backSettingsBtn.addEventListener('click', () => this.showSettings());
        
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }
    
    startGame() {
        this.gridSize = parseInt(this.gridSizeSelect.value);
        this.baseSpeed = parseInt(this.speedSelect.value);
        this.snakeColor = this.snakeColorSelect.value;
        this.foodType = this.foodTypeSelect.value;
        
        this.cellSize = Math.max(15, Math.min(30, 500 / this.gridSize));
        this.canvas.width = this.gridSize * this.cellSize;
        this.canvas.height = this.gridSize * this.cellSize;
        
        this.score = 0;
        this.speedMultiplier = 1;
        this.eatCount = 0;
        this.isRunning = true;
        this.isPaused = false;
        
        const startX = Math.floor(this.gridSize / 4);
        const startY = Math.floor(this.gridSize / 2);
        
        this.snake = [
            { x: startX, y: startY },
            { x: startX - 1, y: startY },
            { x: startX - 2, y: startY }
        ];
        
        this.direction = 'RIGHT';
        this.nextDirection = 'RIGHT';
        
        this.spawnFood();
        this.updateUI();
        this.showGamePanel();
        
        if (this.gameLoop) {
            clearInterval(this.gameLoop);
        }
        
        this.gameLoop = setInterval(() => this.update(), this.getCurrentSpeed());
    }
    
    getCurrentSpeed() {
        return Math.max(40, this.baseSpeed / this.speedMultiplier);
    }
    
    spawnFood() {
        const foodEmojis = FOOD_EMOJIS[this.foodType] || FOOD_EMOJIS.random;
        
        let x, y;
        let onSnake = true;
        
        while (onSnake) {
            x = Math.floor(Math.random() * this.gridSize);
            y = Math.floor(Math.random() * this.gridSize);
            onSnake = this.snake.some(segment => segment.x === x && segment.y === y);
        }
        
        this.food = { x, y };
        this.foodEmoji = foodEmojis[Math.floor(Math.random() * foodEmojis.length)];
    }
    
    handleKeyDown(e) {
        if (!this.isRunning) return;
        
        const key = e.key;
        
        if (key === ' ' || key === 'p' || key === 'P') {
            e.preventDefault();
            this.togglePause();
            return;
        }
        
        if (key === 'r' || key === 'R') {
            this.startGame();
            return;
        }
        
        if (this.isPaused) return;
        
        switch (key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                if (this.direction !== 'DOWN') {
                    this.nextDirection = 'UP';
                }
                e.preventDefault();
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                if (this.direction !== 'UP') {
                    this.nextDirection = 'DOWN';
                }
                e.preventDefault();
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                if (this.direction !== 'RIGHT') {
                    this.nextDirection = 'LEFT';
                }
                e.preventDefault();
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                if (this.direction !== 'LEFT') {
                    this.nextDirection = 'RIGHT';
                }
                e.preventDefault();
                break;
        }
    }
    
    togglePause() {
        this.isPaused = !this.isPaused;
        this.pauseOverlay.style.display = this.isPaused ? 'flex' : 'none';
    }
    
    update() {
        if (this.isPaused) return;
        
        this.direction = this.nextDirection;
        
        const head = this.snake[0];
        const dir = DIRECTIONS[this.direction];
        
        const newHead = {
            x: head.x + dir.x,
            y: head.y + dir.y
        };
        
        if (this.checkCollision(newHead)) {
            this.gameOver();
            return;
        }
        
        this.snake.unshift(newHead);
        
        if (newHead.x === this.food.x && newHead.y === this.food.y) {
            this.eatFood();
        } else {
            this.snake.pop();
        }
        
        this.updateUI();
        this.render();
    }
    
    checkCollision(head) {
        if (head.x < 0 || head.x >= this.gridSize || head.y < 0 || head.y >= this.gridSize) {
            return true;
        }
        
        return this.snake.some(segment => segment.x === head.x && segment.y === head.y);
    }
    
    eatFood() {
        this.score += 10;
        this.eatCount++;
        
        if (this.eatCount % 5 === 0) {
            this.speedMultiplier = Math.min(3, this.speedMultiplier + 0.2);
            
            if (this.gameLoop) {
                clearInterval(this.gameLoop);
                this.gameLoop = setInterval(() => this.update(), this.getCurrentSpeed());
            }
        }
        
        this.spawnFood();
    }
    
    updateUI() {
        this.scoreEl.textContent = this.score;
        this.lengthEl.textContent = this.snake.length;
        this.speedDisplayEl.textContent = `x${this.speedMultiplier.toFixed(1)}`;
    }
    
    render() {
        const ctx = this.ctx;
        const cellSize = this.cellSize;
        
        ctx.fillStyle = '#f0fdf4';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        ctx.strokeStyle = '#d1fae5';
        ctx.lineWidth = 0.5;
        
        for (let i = 0; i <= this.gridSize; i++) {
            ctx.beginPath();
            ctx.moveTo(i * cellSize, 0);
            ctx.lineTo(i * cellSize, this.canvas.height);
            ctx.stroke();
            
            ctx.beginPath();
            ctx.moveTo(0, i * cellSize);
            ctx.lineTo(this.canvas.width, i * cellSize);
            ctx.stroke();
        }
        
        this.snake.forEach((segment, index) => {
            const isHead = index === 0;
            const isTail = index === this.snake.length - 1;
            
            const x = segment.x * cellSize;
            const y = segment.y * cellSize;
            const padding = 2;
            const radius = isHead ? cellSize * 0.3 : cellSize * 0.25;
            
            const alpha = 1 - (index * 0.03);
            const darkerColor = this.darkenColor(this.snakeColor, index * 5);
            
            ctx.fillStyle = darkerColor;
            ctx.globalAlpha = Math.max(0.4, alpha);
            
            this.roundRect(ctx, x + padding, y + padding, cellSize - padding * 2, cellSize - padding * 2, radius);
            ctx.fill();
            
            if (isHead) {
                ctx.globalAlpha = 1;
                
                const eyeSize = cellSize * 0.15;
                const eyeOffset = cellSize * 0.2;
                
                ctx.fillStyle = '#ffffff';
                
                let eye1X, eye1Y, eye2X, eye2Y;
                
                switch (this.direction) {
                    case 'UP':
                        eye1X = x + cellSize * 0.3;
                        eye1Y = y + cellSize * 0.25;
                        eye2X = x + cellSize * 0.7;
                        eye2Y = y + cellSize * 0.25;
                        break;
                    case 'DOWN':
                        eye1X = x + cellSize * 0.3;
                        eye1Y = y + cellSize * 0.55;
                        eye2X = x + cellSize * 0.7;
                        eye2Y = y + cellSize * 0.55;
                        break;
                    case 'LEFT':
                        eye1X = x + cellSize * 0.25;
                        eye1Y = y + cellSize * 0.3;
                        eye2X = x + cellSize * 0.25;
                        eye2Y = y + cellSize * 0.7;
                        break;
                    case 'RIGHT':
                        eye1X = x + cellSize * 0.6;
                        eye1Y = y + cellSize * 0.3;
                        eye2X = x + cellSize * 0.6;
                        eye2Y = y + cellSize * 0.7;
                        break;
                }
                
                ctx.beginPath();
                ctx.arc(eye1X, eye1Y, eyeSize, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.beginPath();
                ctx.arc(eye2X, eye2Y, eyeSize, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.fillStyle = '#1f2937';
                const pupilSize = eyeSize * 0.6;
                
                ctx.beginPath();
                ctx.arc(eye1X, eye1Y, pupilSize, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.beginPath();
                ctx.arc(eye2X, eye2Y, pupilSize, 0, Math.PI * 2);
                ctx.fill();
            }
        });
        
        ctx.globalAlpha = 1;
        
        if (this.food) {
            const fx = this.food.x * cellSize;
            const fy = this.food.y * cellSize;
            
            ctx.fillStyle = '#fef3c7';
            this.roundRect(ctx, fx + 2, fy + 2, cellSize - 4, cellSize - 4, cellSize * 0.2);
            ctx.fill();
            
            ctx.font = `${cellSize * 0.8}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(this.foodEmoji, fx + cellSize / 2, fy + cellSize / 2);
        }
    }
    
    roundRect(ctx, x, y, width, height, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }
    
    darkenColor(hex, amount) {
        const num = parseInt(hex.slice(1), 16);
        const r = Math.max(0, (num >> 16) - amount);
        const g = Math.max(0, ((num >> 8) & 0x00FF) - amount);
        const b = Math.max(0, (num & 0x0000FF) - amount);
        
        return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1)}`;
    }
    
    gameOver() {
        this.isRunning = false;
        
        if (this.gameLoop) {
            clearInterval(this.gameLoop);
            this.gameLoop = null;
        }
        
        if (window.submitGameScore && this.score > 0) {
            window.submitGameScore(this.score);
        }
        
        this.finalScoreEl.textContent = this.score;
        this.finalLengthEl.textContent = this.snake.length;
        
        this.showGameoverPanel();
    }
    
    showSettings() {
        this.settingsPanel.style.display = 'block';
        this.gamePanel.style.display = 'none';
        this.gameoverPanel.style.display = 'none';
    }
    
    showGamePanel() {
        this.settingsPanel.style.display = 'none';
        this.gamePanel.style.display = 'block';
        this.gameoverPanel.style.display = 'none';
    }
    
    showGameoverPanel() {
        this.settingsPanel.style.display = 'none';
        this.gamePanel.style.display = 'none';
        this.gameoverPanel.style.display = 'flex';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SnakeGame();
});
