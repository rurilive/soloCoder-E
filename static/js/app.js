document.addEventListener('DOMContentLoaded', function() {
    const grid = document.getElementById('sudoku-grid');
    const cells = grid.querySelectorAll('.sudoku-cell');
    const numberButtons = document.querySelectorAll('.number-btn');
    const messageContainer = document.getElementById('message-container');
    const newGameBtn = document.getElementById('new-game-btn');
    const validateBtn = document.getElementById('validate-btn');
    const hintBtn = document.getElementById('hint-btn');
    const resetBtn = document.getElementById('reset-btn');
    const difficultySelect = document.getElementById('difficulty');

    let selectedCell = null;

    cells.forEach(cell => {
        cell.addEventListener('click', function() {
            if (this.hasAttribute('readonly')) {
                return;
            }
            cells.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
            selectedCell = this;
        });

        cell.addEventListener('input', function() {
            const value = this.value;
            if (value === '' || (value >= '1' && value <= '9')) {
                clearErrors();
            } else {
                this.value = '';
            }
        });

        cell.addEventListener('keydown', function(e) {
            const row = parseInt(this.dataset.row);
            const col = parseInt(this.dataset.col);

            switch(e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    if (row > 0) {
                        cells[(row - 1) * 9 + col].click();
                    }
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    if (row < 8) {
                        cells[(row + 1) * 9 + col].click();
                    }
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    if (col > 0) {
                        cells[row * 9 + (col - 1)].click();
                    }
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    if (col < 8) {
                        cells[row * 9 + (col + 1)].click();
                    }
                    break;
                case 'Backspace':
                case 'Delete':
                    e.preventDefault();
                    if (!this.hasAttribute('readonly')) {
                        this.value = '';
                        clearErrors();
                    }
                    break;
            }
        });
    });

    numberButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            if (selectedCell && !selectedCell.hasAttribute('readonly')) {
                const value = this.dataset.value;
                selectedCell.value = value;
                clearErrors();
            }
        });
    });

    newGameBtn.addEventListener('click', function() {
        const difficulty = difficultySelect.value;
        const formData = new FormData();
        formData.append('difficulty', difficulty);

        fetch('/new', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateGrid(data.grid, data.initial_grid);
                showMessage('新游戏已开始！', 'success');
            }
        })
        .catch(error => {
            showMessage('创建新游戏失败', 'error');
            console.error('Error:', error);
        });
    });

    validateBtn.addEventListener('click', function() {
        const userGrid = getCurrentGrid();
        
        fetch('/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ grid: userGrid })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                clearErrors();
                
                if (data.errors.length > 0) {
                    data.errors.forEach(error => {
                        const cellIndex = error.row * 9 + error.col;
                        cells[cellIndex].classList.add('error');
                    });
                    showMessage(data.message, 'error');
                } else if (data.is_correct) {
                    showMessage(data.message, 'success');
                } else {
                    showMessage(data.message, 'info');
                }
            }
        })
        .catch(error => {
            showMessage('验证失败', 'error');
            console.error('Error:', error);
        });
    });

    hintBtn.addEventListener('click', function() {
        const userGrid = getCurrentGrid();
        
        fetch('/hint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ grid: userGrid })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const { row, col, value } = data.hint;
                const cellIndex = row * 9 + col;
                cells[cellIndex].value = value;
                cells[cellIndex].classList.add('hint');
                showMessage(`提示：在第 ${row + 1} 行第 ${col + 1} 列填入 ${value}`, 'warning');
            } else {
                showMessage(data.message, 'info');
            }
        })
        .catch(error => {
            showMessage('获取提示失败', 'error');
            console.error('Error:', error);
        });
    });

    resetBtn.addEventListener('click', function() {
        fetch('/reset', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateGrid(data.grid, data.initial_grid);
                showMessage('游戏已重置', 'info');
            }
        })
        .catch(error => {
            showMessage('重置失败', 'error');
            console.error('Error:', error);
        });
    });

    function getCurrentGrid() {
        const grid = [];
        for (let i = 0; i < 9; i++) {
            const row = [];
            for (let j = 0; j < 9; j++) {
                const cell = cells[i * 9 + j];
                row.push(cell.value === '' ? 0 : parseInt(cell.value));
            }
            grid.push(row);
        }
        return grid;
    }

    function updateGrid(grid, initialGrid) {
        cells.forEach((cell, index) => {
            const row = Math.floor(index / 9);
            const col = index % 9;
            
            cell.classList.remove('initial', 'error', 'hint', 'selected');
            cell.removeAttribute('readonly');
            
            if (initialGrid[row][col] !== 0) {
                cell.value = initialGrid[row][col];
                cell.classList.add('initial');
                cell.setAttribute('readonly', 'readonly');
            } else {
                cell.value = grid[row][col] !== 0 ? grid[row][col] : '';
            }
        });
        selectedCell = null;
    }

    function clearErrors() {
        cells.forEach(cell => {
            cell.classList.remove('error', 'hint');
        });
        messageContainer.className = 'message-container';
        messageContainer.textContent = '';
    }

    function showMessage(message, type) {
        messageContainer.className = `message-container ${type}`;
        messageContainer.textContent = message;
    }
});
