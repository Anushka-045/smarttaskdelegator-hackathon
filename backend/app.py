from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://loginform-f0336-default-rtdb.firebaseio.com"
})


@app.route("/add-user", methods=["POST"])
def add_user():
    data = request.json
    username = data.get("username")
    skills = data.get("skills", [])

    user_ref = db.reference("users").push({
        "username": username,
        "skills": skills,
        "workload": 0,
        "active": True,
        "role": "team-member"
    })

    return jsonify({"message": f"{username} added to active team"})


@app.route("/assign-task", methods=["POST"])
def assign_task():
    data = request.json
    title = data.get("title")
    required_skill = data.get("requiredSkill", "").lower()

    users = db.reference("users").get()

    best_user = None
    best_username = None
    min_workload = float("inf")

    if users:
        for uid, user in users.items():
            if not user.get("active"):
                continue

            skills = user.get("skills", [])
            workload = user.get("workload", 0)

            if required_skill in skills and workload < min_workload:
                best_user = uid
                best_username = user.get("username")
                min_workload = workload

    task_ref = db.reference("tasks").push({
        "title": title,
        "requiredSkill": required_skill,
        "assignedTo": best_user,
        "assignedUsername": best_username,
        "status": "Pending"
    })

    if best_user:
        db.reference(f"users/{best_user}/workload").set(min_workload + 1)

    return jsonify({
        "task": title,
        "assignedUsername": best_username,
        "status": "Pending"
    })


@app.route("/my-tasks/<uid>")
def my_tasks(uid):
    tasks = db.reference("tasks").get()
    user_tasks = []

    if tasks:
        for tid, task in tasks.items():
            if task.get("assignedTo") == uid:
                task["id"] = tid
                user_tasks.append(task)

    return jsonify(user_tasks)


@app.route("/update-task", methods=["POST"])
def update_task():
    data = request.json
    task_id = data.get("taskId")
    new_status = data.get("status")

    task_ref = db.reference(f"tasks/{task_id}")
    task = task_ref.get()

    if not task:
        return jsonify({"message": "Task not found"}), 404

    task_ref.update({"status": new_status})

    if new_status == "Completed":
        uid = task.get("assignedTo")
        if uid:
            user_ref = db.reference(f"users/{uid}")
            workload = user_ref.child("workload").get() or 0
            user_ref.child("workload").set(max(workload - 1, 0))

    return jsonify({"message": "Task updated"})


if __name__ == "__main__":
    app.run(debug=True)
