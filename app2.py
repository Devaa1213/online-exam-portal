from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# In-memory exam storage
exams = {}

# File to store results
ANSWERS_FILE = "answers.json"

# Load existing answers
if os.path.exists(ANSWERS_FILE):
    with open(ANSWERS_FILE, "r") as f:
        results = json.load(f)
else:
    results = {}

# Save results to JSON file
def save_answers():
    with open(ANSWERS_FILE, "w") as f:
        json.dump(results, f, indent=2)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/select-mode')
def select_mode():
    return render_template("select_mode.html")

@app.route('/conduct-exam', methods=["GET", "POST"])
def conduct_exam():
    if request.method == "POST":
        session["exam_name"] = request.form["exam_name"]
        session["exam_type"] = request.form["exam_type"]
        return redirect(url_for('add_questions'))
    return render_template("conduct_exam.html")

@app.route('/add-questions', methods=["GET", "POST"])
def add_questions():
    exam_name = session.get("exam_name")
    exam_type = session.get("exam_type")

    if request.method == "POST":
        question = request.form["question"]

        if exam_name not in exams:
            exams[exam_name] = {"type": exam_type, "questions": []}

        if exam_type == "MCQ":
            options = [
                request.form["option1"],
                request.form["option2"],
                request.form["option3"],
                request.form["option4"]
            ]
            correct = request.form["correct"]
            exams[exam_name]["questions"].append({
                "question": question,
                "options": options,
                "correct": correct
            })
        else:
            exams[exam_name]["questions"].append({"question": question})

        if request.form.get("finish"):
            return f"Exam '{exam_name}' created with {len(exams[exam_name]['questions'])} questions."

    return render_template("add_questions.html", exam_name=exam_name, exam_type=exam_type)

@app.route('/attend-exam', methods=["GET", "POST"])
def attend_exam():
    if request.method == "POST":
        exam_name = request.form.get("exam_name")
        student_name = request.form.get("student_name", "anonymous")

        if exam_name in exams:
            session["student_exam"] = exam_name
            session["student_id"] = student_name
            return redirect(url_for('answer_exam'))
        else:
            return "Exam not found."
    return render_template("attend_exam.html")

@app.route('/answer-exam', methods=["GET", "POST"])
def answer_exam():
    exam_name = session.get("student_exam")
    if not exam_name or exam_name not in exams:
        return "Invalid exam."

    exam = exams[exam_name]
    questions = exam["questions"]

    if request.method == "POST":
        answers = []
        score = 0
        for i, question in enumerate(questions):
            ans = request.form.get(f"q{i}")
            answers.append(ans)

            # Scoring only if it's MCQ
            if "options" in question:
                if ans == question["correct"]:
                    score += 1

        student_id = session.get("student_id", "anonymous")
        if exam_name not in results:
            results[exam_name] = []

        results[exam_name].append({
            "student": student_id,
            "answers": answers,
            "score": score
        })

        save_answers()  # if using JSON file

        return render_template("submission.html", exam_name=exam_name, answers=answers, score=score)

    return render_template("answer_exam.html", exam=exam, exam_name=exam_name, questions=questions)



@app.route('/submit-exam', methods=["POST"])
def submit_exam():
    exam_name = request.form["exam_name"]
    exam = exams.get(exam_name)
    answers = []

    for idx, q in enumerate(exam["questions"]):
        ans = request.form.get(f"q{idx}")
        answers.append(ans)

    return render_template("submission.html", exam_name=exam_name, answers=answers)

if __name__ == '__main__':
    app.run(debug=True)
