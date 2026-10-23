from dotenv import load_dotenv
import os
import requests
import resend

load_dotenv(override=True)

resend.api_key = os.getenv("RESEND_API_KEY")
print("--> LOADED KEY PREFIX:", str(resend.api_key)[:6])
from bs4 import BeautifulSoup
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from helpers import login_required, error, validate
from werkzeug.security import check_password_hash, generate_password_hash

# Configure Application
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "EFGBVMU_LFZ_gps_mpdbm_qspkfdu")

db = SQL("sqlite:///quiz.db")

@app.route("/me", methods=["GET", "POST"])
@login_required
def me():
    if request.method == "POST":
        new_username = request.form.get("username")
        logo_url = request.form.get("logo_url")

        if new_username:
            existing = db.execute("SELECT id FROM users WHERE username = ? AND id != ?", new_username, session["user_id"])
            if existing:
                flash("Username is already taken.")
                return redirect("/me")
            db.execute("UPDATE users SET username = ? WHERE id = ?", new_username, session["user_id"])

        if logo_url:
            db.execute("UPDATE users SET logo_url = ? WHERE id = ?", logo_url, session["user_id"])

        flash("Profile updated successfully!")
        return redirect("/me")

    user = db.execute("SELECT id, username, logo_url, is_admin FROM users WHERE id = ?", session["user_id"])[0]
    my_quizzes = db.execute("SELECT id, title, description FROM quizzes WHERE user_id = ? ORDER BY id DESC", session["user_id"])

    return render_template("me.html", user=user, quizzes=my_quizzes)

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username, password, err = validate()
        if err:
            return error(err=err)
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if not user:
            return error(err="Invalid user")
        hashtag = user[0]["hash"]
        if not check_password_hash(hashtag, password):
            return error(err="Your password doesn't match")
        session["user_id"] = user[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        username, password, err = validate()
        if err:
            return error(err=err)
        user = db.execute("SELECT COUNT(*) FROM users WHERE username = ?", username)
        if user[0]["COUNT(*)"] > 0:
            return error(err="Sorry, but this username has been already taken.")
        hashed = generate_password_hash(password)
        user_id = db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", username, hashed)
        session["user_id"] = user_id
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/")
@login_required
def home():
    quizzes = db.execute("SELECT id, title, description FROM quizzes ORDER BY id DESC ")
    use = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    if not use:
        session.clear()
        return redirect("/login")

    user = use[0]["username"]
    return render_template("homepage.html", user=user, quizzes=quizzes)

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        quiz_number = db.execute("INSERT INTO quizzes(user_id, title, description) VALUES(?, ?, ?)", session["user_id"], title, description)

        return redirect(f"/add?quiz_id={quiz_number}")
    else:
        return render_template("create.html")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        quiz_id = request.form.get("quiz_id")
        question = request.form.get("question")
        correct_answer = request.form.get("answer")
        option = []
        for I in range(4):
            option.append(request.form.get(f"option{I}"))

        question_id = db.execute("INSERT INTO questions(quiz_id, question_text) VALUES(?, ?)", quiz_id, question)
        for opt in option:
            is_correct = 1 if opt == correct_answer else 0
            db.execute("INSERT INTO options(question_id, option_text, is_correct) VALUES(?, ?, ?)", question_id, opt, is_correct)

        count_data = db.execute("SELECT COUNT(*) AS total FROM questions WHERE quiz_id = ?", quiz_id)
        total_questions = count_data[0]["total"]

        action = request.form.get("action")

        if action == "finish":
            if total_questions < 5:
                remaining = 5 - total_questions
                flash(f"You need at least 5 questions. Please add {remaining} more!")
                return redirect(f"/add?quiz_id={quiz_id}")
            else:
                return redirect("/")

        return redirect(f"/add?quiz_id={quiz_id}")
    else:
        quiz_id = request.args.get("quiz_id")
        count_data = db.execute("SELECT COUNT(*) AS total FROM questions WHERE quiz_id = ?", quiz_id)
        total_questions = count_data[0]["total"]
        return render_template("add.html", quiz_id=quiz_id, total_questions=total_questions)

@app.route("/play/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def play(quiz_id):
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ?", quiz_id)
    if not quiz:
        flash("The quiz has been deleted/eradicated.")
        return redirect("/")

    if request.method == "POST":
        # Fetch question IDs and their types (defaulting to 'mcq' if null)
        questions = db.execute("SELECT id, COALESCE(question_type, 'mcq') AS question_type FROM questions WHERE quiz_id = ?", quiz_id)
        total = len(questions)
        score = 0

        for q in questions:
            user_input = request.form.get(f"question_{q['id']}", "").strip()

            if not user_input:
                continue

            if q["question_type"] == "text":
                # Free-text answer: compare case-insensitively with the correct answer string
                correct_row = db.execute(
                    "SELECT option_text FROM options WHERE question_id = ? AND is_correct = 1 LIMIT 1",
                    q["id"]
                )
                if correct_row and user_input.lower() == correct_row[0]["option_text"].strip().lower():
                    score += 1

            else:
                # MCQ: user_input contains the selected option ID
                correct = db.execute(
                    "SELECT is_correct FROM options WHERE id = ? AND question_id = ?",
                    user_input, q["id"]
                )
                if correct and correct[0]["is_correct"] == 1:
                    score += 1

        # Record attempt
        db.execute(
            "INSERT INTO scores (user_id, quiz_id, score, total, timestamp) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            session["user_id"], quiz_id, score, total
        )

        # Aggregate scorecard metrics
        stats = db.execute("""
            SELECT
                COUNT(id) AS total_attempts,
                ROUND(AVG(score), 1) AS avg_score,
                MAX(score) AS max_score
            FROM scores
            WHERE quiz_id = ?
        """, quiz_id)[0]

        top_scores = db.execute("""
            SELECT users.username, users.logo_url, scores.score, scores.total
            FROM scores
            JOIN users ON scores.user_id = users.id
            WHERE scores.quiz_id = ?
            ORDER BY scores.score DESC, scores.timestamp ASC
            LIMIT 5
        """, quiz_id)

        user_percentage = round((score / total) * 100) if total > 0 else 0
        avg_score_val = stats["avg_score"] or 0
        avg_percentage = round((avg_score_val / total) * 100) if total > 0 else 0

        return render_template(
            "result.html",
            quiz=quiz[0],
            score=score,
            total=total,
            user_percentage=user_percentage,
            stats=stats,
            avg_percentage=avg_percentage,
            top_scores=top_scores
        )

    else:
        # GET: Fetch question details along with question_type
        questions = db.execute(
            "SELECT id, question_text, COALESCE(question_type, 'mcq') AS question_type FROM questions WHERE quiz_id = ?",
            quiz_id
        )
        for q in questions:
            if q["question_type"] == "mcq":
                q["options"] = db.execute(
                    "SELECT id, option_text FROM options WHERE question_id = ?",
                    q["id"]
                )

        return render_template("play.html", quiz=quiz[0], questions=questions)

@app.route("/play")
@login_required
def play_index():
    user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    quizzes = db.execute("SELECT id, title, description FROM quizzes ORDER BY id DESC")
    return render_template("homepage.html", user=user[0]["username"], quizzes=quizzes)

@app.route("/scoreboard/<int:quiz_id>")
@login_required
def scoreboard(quiz_id):
    quiz = db.execute("SELECT id, title FROM quizzes WHERE id = ?", quiz_id)
    if not quiz:
        flash("Quiz not found.")
        return redirect("/")

    leaderboard = db.execute("""
        SELECT users.username, users.logo_url, scores.score, scores.total, scores.timestamp
        FROM scores
        JOIN users ON scores.user_id = users.id
        WHERE scores.quiz_id = ?
        ORDER BY scores.score DESC, scores.timestamp ASC
        LIMIT 10
    """, quiz_id)

    return render_template("scoreboard.html", quiz=quiz[0], leaderboard=leaderboard)

@app.route("/question/<int:question_id>/delete", methods=["POST"])
@login_required
def delete_question(question_id):
    # Find the question and its parent quiz
    question = db.execute("SELECT * FROM questions WHERE id = ?", question_id)
    if not question:
        flash("Question not found.")
        return redirect("/")

    quiz_id = question[0]["quiz_id"]

    # Check current question count before deleting
    current_count = db.execute("SELECT COUNT(*) AS total FROM questions WHERE quiz_id = ?", quiz_id)[0]["total"]

    if current_count <= 5:
        flash("Error: A quiz must have at least 5 questions. Cannot delete.")
        return redirect(f"/quiz/{quiz_id}/edit")

    # Safe to delete
    db.execute("DELETE FROM questions WHERE id = ?", question_id)
    flash("Question deleted successfully.")
    return redirect(f"/quiz/{quiz_id}/edit")

@app.route("/quiz/<int:quiz_id>/add_question", methods=["POST"])
@login_required
def add_question(quiz_id):
    question_text = request.form.get("question")
    # Get options and correct answer fields from your form...

    if not question_text:
        flash("Question text cannot be empty.")
        return redirect(f"/quiz/{quiz_id}/edit")

    db.execute(
        "INSERT INTO questions (quiz_id, question_text) VALUES (?, ?)",
        quiz_id, question_text
    )
    flash("New question added!")
    return redirect(f"/quiz/{quiz_id}/edit")

@app.route("/leave", methods=["GET", "POST"])
@login_required
def leave():
    if request.method == "POST":
        confirmation = request.form.get("confirmation")
        password = request.form.get("password")

        if confirmation != "DELETE" or not password:
            flash("Type DELETE and enter your password to confirm.")
            return redirect("/leave")

        user = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])[0]
        if not check_password_hash(user["hash"], password):
            flash("Incorrect password.")
            return redirect("/leave")

        db.execute("DELETE FROM users WHERE id = ?", session["user_id"])
        session.clear()
        flash("Your account and all associated data have been permanently deleted.")
        return redirect("/login")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

@app.route("/contact", methods=["GET", "POST"])
@login_required
def contact():
    # 1. First, fetch the admin or first user
    admin_row = db.execute("SELECT id FROM users WHERE is_admin = 1 LIMIT 1")
    if not admin_row:
        admin_row = db.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1")

    if not admin_row:
        return "No admin or users found in database", 500

    # 2. Define DEVELOPER_ID here in the main function scope
    DEVELOPER_ID = admin_row[0]["id"]

    # 3. Handle POST
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message:
            recipient_id = int(request.form.get("recipient_id", DEVELOPER_ID))
            db.execute("""
                INSERT INTO messages (sender_id, recipient_id, message_text)
                VALUES (?, ?, ?)
            """, session["user_id"], recipient_id, message)
        return redirect("/contact")

    # 4. Handle GET (Fetching messages)
    user_id = session["user_id"]
    messages = db.execute("""
        SELECT messages.*, users.username, users.logo_url
        FROM messages
        JOIN users ON messages.sender_id = users.id
        WHERE (sender_id = ? AND recipient_id = ?)
           OR (sender_id = ? AND recipient_id = ?)
        ORDER BY created_at ASC
    """, user_id, DEVELOPER_ID, DEVELOPER_ID, user_id)

    return render_template("contact.html", messages=messages, developer_id=DEVELOPER_ID)

@app.route("/delete_quiz/<int:quiz_id>", methods=["POST"])
@login_required
def delete_quiz(quiz_id):
    user = db.execute("SELECT is_admin FROM users WHERE id = ?", session["user_id"])
    quiz = db.execute("SELECT user_id FROM quizzes WHERE id = ?", quiz_id)

    if not quiz:
        flash("Quiz not found.")
        return redirect("/")

    if user[0]["is_admin"] == 1 or quiz[0]["user_id"] == session["user_id"]:
        db.execute("DELETE FROM quizzes WHERE id = ?", quiz_id)
        flash("Quiz deleted successfully.")
    else:
        flash("You do not have permission to delete this quiz.")

    return redirect("/")

@app.route("/logout", methods=["GET","POST"])
@login_required
def logout():
    session.clear()
    flash("You have logged out.")
    return redirect("/")

@app.route("/quiz/<int:quiz_id>/edit", methods=["GET", "POST"])
@login_required
def edit_quiz(quiz_id):
    # Check if quiz exists and belongs to the current user
    quiz = db.execute("SELECT * FROM quizzes WHERE id = ?", quiz_id)
    if not quiz or quiz[0]["user_id"] != session["user_id"]:
        flash("You do not have permission to edit this quiz.")
        return redirect("/")

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        if not title:
            flash("Quiz title cannot be blank.")
            return redirect(f"/quiz/{quiz_id}/edit")

        # Update the quiz details in the database
        db.execute(
            "UPDATE quizzes SET title = ?, description = ? WHERE id = ?",
            title, description, quiz_id
        )
        flash("Quiz updated successfully!")
        return redirect("/")

    return render_template("edit_quiz.html", quiz=quiz[0])
