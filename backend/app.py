from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://loginform-f0336-default-rtdb.firebaseio.com"
})


def time_to_minutes(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


@app.route("/add-user", methods=["POST"])
def add_user():
    data = request.json

    team_id = data.get("teamId")
    username = data.get("username")
    skills_raw = data.get("skills")
    date = data.get("date")
    free_from = data.get("from")
    free_to = data.get("to")
    max_load = int(data.get("maxLoad", 0))

    if not all([team_id, username, skills_raw, date, free_from, free_to, max_load]):
        return jsonify({"message": "Invalid user data"}), 400

    skills = [s.strip().lower() for s in skills_raw.split(",") if s.strip()]

    db.reference(f"teams/{team_id}/users").push({
        "username": username,
        "skills": skills,
        "date": date,
        "free_from": free_from,
        "free_to": free_to,
        "workload": 0,
        "max_load": max_load,
        "active": True
    })

    return jsonify({"message": "User added"})


@app.route("/assign-task", methods=["POST"])
def assign_task():
    data = request.json

    team_id = data.get("teamId")
    title = data.get("title")
    required_skill = data.get("requiredSkill", "").lower()
    task_date = data.get("date")
    task_from = data.get("from")
    task_to = data.get("to")

    if not all([team_id, title, required_skill, task_date, task_from, task_to]):
        return jsonify({"assignedUsername": None, "status": "Failed"}), 400

    task_from_min = time_to_minutes(task_from)
    task_to_min = time_to_minutes(task_to)

    users = db.reference(f"teams/{team_id}/users").get()

    best_user_id = None
    best_username = None
    min_workload = float("inf")

    if users:
        for uid, user in users.items():
            if not user.get("active"):
                continue

            if required_skill not in user.get("skills", []):
                continue

            if user.get("date") != task_date:
                continue

            user_from = time_to_minutes(user.get("free_from"))
            user_to = time_to_minutes(user.get("free_to"))

            if not (user_from <= task_from_min and user_to >= task_to_min):
                continue

            workload = user.get("workload", 0)
            max_load = user.get("max_load", 0)

            if workload >= max_load:
                continue

            if workload < min_workload:
                min_workload = workload
                best_user_id = uid
                best_username = user.get("username")

    db.reference(f"teams/{team_id}/tasks").push({
        "title": title,
        "requiredSkill": required_skill,
        "date": task_date,
        "from": task_from,
        "to": task_to,
        "assignedTo": best_user_id,
        "assignedUsername": best_username,
        "status": "Pending"
    })

    if best_user_id:
        db.reference(
            f"teams/{team_id}/users/{best_user_id}/workload"
        ).set(min_workload + 1)

    return jsonify({
        "assignedUsername": best_username,
        "status": "Pending"
    })


if __name__ == "__main__":
    app.run(debug=True)
