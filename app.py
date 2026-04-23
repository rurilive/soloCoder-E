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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
