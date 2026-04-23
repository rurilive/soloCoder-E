from flask import Flask, render_template, request, jsonify, session
from sudoku import Sudoku, Difficulty

app = Flask(__name__)
app.secret_key = "sudoku-secret-key-2024"


def get_difficulty_from_string(difficulty_str):
    difficulty_map = {
        "easy": Difficulty.EASY,
        "medium": Difficulty.MEDIUM,
        "hard": Difficulty.HARD,
        "expert": Difficulty.EXPERT,
    }
    return difficulty_map.get(difficulty_str, Difficulty.MEDIUM)


@app.route("/")
def index():
    if "grid" not in session or "solution" not in session or "initial_grid" not in session:
        sudoku = Sudoku()
        sudoku.generate(Difficulty.MEDIUM)
        session["grid"] = sudoku.grid
        session["solution"] = sudoku.solution
        session["initial_grid"] = sudoku.initial_grid
        session["difficulty"] = "medium"

    return render_template(
        "index.html",
        grid=session["grid"],
        initial_grid=session["initial_grid"],
        difficulty=session["difficulty"],
    )


@app.route("/new", methods=["POST"])
def new_game():
    difficulty_str = request.form.get("difficulty", "medium")
    difficulty = get_difficulty_from_string(difficulty_str)

    sudoku = Sudoku()
    sudoku.generate(difficulty)

    session["grid"] = sudoku.grid
    session["solution"] = sudoku.solution
    session["initial_grid"] = sudoku.initial_grid
    session["difficulty"] = difficulty_str

    return jsonify(
        {
            "success": True,
            "grid": sudoku.grid,
            "initial_grid": sudoku.initial_grid,
            "difficulty": difficulty_str,
        }
    )


@app.route("/validate", methods=["POST"])
def validate():
    user_grid = request.json.get("grid")

    if not user_grid or "solution" not in session:
        return jsonify({"success": False, "message": "游戏状态无效"})

    sudoku = Sudoku()
    sudoku.grid = [row.copy() for row in session["grid"]]
    sudoku.solution = [row.copy() for row in session["solution"]]
    sudoku.initial_grid = [row.copy() for row in session["initial_grid"]]

    result = sudoku.validate(user_grid)

    return jsonify({"success": True, **result})


@app.route("/hint", methods=["POST"])
def get_hint():
    user_grid = request.json.get("grid")

    if not user_grid or "solution" not in session:
        return jsonify({"success": False, "message": "游戏状态无效"})

    sudoku = Sudoku()
    sudoku.grid = [row.copy() for row in session["grid"]]
    sudoku.solution = [row.copy() for row in session["solution"]]
    sudoku.initial_grid = [row.copy() for row in session["initial_grid"]]

    hint = sudoku.get_hint(user_grid)

    if hint is None:
        return jsonify({"success": False, "message": "数独已完成，无需提示"})

    return jsonify({"success": True, "hint": hint})


@app.route("/reset", methods=["POST"])
def reset():
    if "initial_grid" not in session:
        return jsonify({"success": False, "message": "游戏状态无效"})

    session["grid"] = [row.copy() for row in session["initial_grid"]]

    return jsonify(
        {
            "success": True,
            "grid": session["grid"],
            "initial_grid": session["initial_grid"],
        }
    )


@app.route("/export", methods=["POST"])
def export_grid():
    user_grid = request.json.get("grid")
    if not user_grid:
        user_grid = session.get("grid", [[0]*9 for _ in range(9)])
    
    export_data = {
        "current_grid": user_grid,
        "initial_grid": session.get("initial_grid"),
        "solution": session.get("solution"),
        "difficulty": session.get("difficulty"),
        "format": "9x9 array (0 = empty, 1-9 = filled)",
        "rows": [
            f"第{i+1}行: {user_grid[i]}" for i in range(9)
        ]
    }
    
    return jsonify({
        "success": True,
        "json_format": export_data,
        "copy_paste_format": {
            "grid": user_grid,
            "note": "将此数据复制给我检查，格式为 9x9 数组，0 表示空格"
        }
    })


@app.route("/debug/solution", methods=["GET"])
def debug_solution():
    if "solution" not in session:
        return jsonify({"success": False, "message": "没有活动的游戏"})
    
    solution = session.get("solution")
    initial = session.get("initial_grid")
    
    return jsonify({
        "success": True,
        "solution": solution,
        "initial_grid": initial,
        "solution_formatted": [
            f"第{i+1}行: {solution[i]}" for i in range(9)
        ],
        "initial_formatted": [
            f"第{i+1}行: {initial[i]}" for i in range(9)
        ]
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
