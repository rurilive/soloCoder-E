import random
from enum import Enum


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


DIFFICULTY_SETTINGS = {
    Difficulty.EASY: {"cells_to_remove": 30, "min_clues": 45},
    Difficulty.MEDIUM: {"cells_to_remove": 40, "min_clues": 35},
    Difficulty.HARD: {"cells_to_remove": 50, "min_clues": 25},
    Difficulty.EXPERT: {"cells_to_remove": 58, "min_clues": 17},
}


class Sudoku:
    def __init__(self):
        self.grid = [[0 for _ in range(9)] for _ in range(9)]
        self.solution = None
        self.initial_grid = None

    def generate(self, difficulty: Difficulty = Difficulty.MEDIUM):
        self._fill_grid()
        self.solution = [row.copy() for row in self.grid]
        settings = DIFFICULTY_SETTINGS[difficulty]
        self._remove_cells(settings["cells_to_remove"], settings["min_clues"])
        self.initial_grid = [row.copy() for row in self.grid]
        return self.grid

    def _fill_grid(self):
        numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        for i in range(9):
            for j in range(9):
                if self.grid[i][j] == 0:
                    random.shuffle(numbers)
                    for num in numbers:
                        if self._is_valid_move(i, j, num):
                            self.grid[i][j] = num
                            if self._fill_grid():
                                return True
                            self.grid[i][j] = 0
                    return False
        return True

    def _remove_cells(self, cells_to_remove, min_clues):
        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)
        removed = 0
        clues_remaining = 81

        for i, j in cells:
            if removed >= cells_to_remove or clues_remaining <= min_clues:
                break

            if self.grid[i][j] != 0:
                original_value = self.grid[i][j]
                self.grid[i][j] = 0

                temp_grid = [row.copy() for row in self.grid]
                solutions = self._count_solutions(temp_grid)

                if solutions == 1:
                    removed += 1
                    clues_remaining -= 1
                else:
                    self.grid[i][j] = original_value

    def _count_solutions(self, grid, limit=2):
        count = 0
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 0:
                    for num in range(1, 10):
                        if self._is_valid_move_grid(grid, i, j, num):
                            grid[i][j] = num
                            count += self._count_solutions(grid, limit)
                            if count >= limit:
                                grid[i][j] = 0
                                return count
                            grid[i][j] = 0
                    return count
        return count + 1

    def _is_valid_move(self, row, col, num):
        if num in self.grid[row]:
            return False
        if num in [self.grid[i][col] for i in range(9)]:
            return False
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if self.grid[start_row + i][start_col + j] == num:
                    return False
        return True

    def _is_valid_move_grid(self, grid, row, col, num):
        if num in grid[row]:
            return False
        if num in [grid[i][col] for i in range(9)]:
            return False
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if grid[start_row + i][start_col + j] == num:
                    return False
        return True

    def validate(self, user_grid):
        errors = []
        for i in range(9):
            for j in range(9):
                if user_grid[i][j] == 0:
                    continue
                if user_grid[i][j] < 1 or user_grid[i][j] > 9:
                    errors.append({"row": i, "col": j, "type": "invalid_value"})
                    continue
                if not self._is_valid_move_grid(user_grid, i, j, user_grid[i][j]):
                    errors.append({"row": i, "col": j, "type": "conflict"})

        is_complete = all(
            user_grid[i][j] != 0 for i in range(9) for j in range(9)
        )
        is_correct = len(errors) == 0 and is_complete

        if is_complete:
            for i in range(9):
                for j in range(9):
                    if user_grid[i][j] != self.solution[i][j]:
                        errors.append({"row": i, "col": j, "type": "wrong_answer"})
            is_correct = len(errors) == 0

        return {
            "is_correct": is_correct,
            "is_complete": is_complete,
            "errors": errors,
            "message": self._get_validate_message(is_correct, is_complete, errors),
        }

    def _get_validate_message(self, is_correct, is_complete, errors):
        if is_correct:
            return "恭喜！答案正确！"
        if not is_complete:
            if len(errors) > 0:
                return f"还有 {len(errors)} 个错误，且数独未完成。"
            return "数独未完成，请继续填写。"
        return f"数独已完成，但有 {len(errors)} 个错误。"

    def get_hint(self, user_grid):
        empty_cells = [
            (i, j) for i in range(9) for j in range(9) if user_grid[i][j] == 0
        ]
        if not empty_cells:
            return None

        i, j = random.choice(empty_cells)
        return {"row": i, "col": j, "value": self.solution[i][j]}

    def is_initial_cell(self, row, col):
        return self.initial_grid is not None and self.initial_grid[row][col] != 0
