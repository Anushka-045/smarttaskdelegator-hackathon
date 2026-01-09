from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("backend/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://loginform-f0336-default-rtdb.firebaseio.com"
})

@app.route("/assign-task", methods=["POST"])
def assign_task():
    data = request.json or {}

    title = data.get("title")
    required_skill = data.get("requiredSkill")

    if not title or not required_skill:
        return jsonify({"error": "Title and requiredSkill are required"}), 400

    required_skill = required_skill.strip().lower()

    users = db.reference("users").get() or {}

    best_user = None
    best_username = None
    min_workload = float("inf")

    for uid, user in users.items():
        skills = user.get("skills", [])
        workload = user.get("workload", 0)
        username = user.get("username", "")

        if not isinstance(skills, list):
            continue

        skills = [s.strip().lower() for s in skills]

        if required_skill not in skills:
            continue

        if workload >= 5:
            continue

        if workload < min_workload:
            best_user = uid
            best_username = username
            min_workload = workload

    task_data = {
        "title": title,
        "requiredSkill": required_skill,
        "assignedTo": best_user,
        "assignedUsername": best_username,
        "status": "Pending" if best_user else "Unassigned",
        "createdAt": datetime.now().isoformat()
    }

    task_ref = db.reference("tasks").push(task_data)

    if best_user:
        db.reference(f"users/{best_user}/workload").set(min_workload + 1)

    return jsonify({
        "taskId": task_ref.key,
        "assignedTo": best_user,
        "assignedUsername": best_username,
        "status": task_data["status"]
    })

@app.route("/my-tasks/<uid>")
def my_tasks(uid):
    tasks = db.reference("tasks").get() or {}
    user_tasks = []

    for task_id, task in tasks.items():
        if task.get("assignedTo") == uid:
            task["id"] = task_id
            user_tasks.append(task)

    return jsonify(user_tasks)

@app.route("/update-task", methods=["POST"])
def update_task():
    data = request.json or {}
    task_id = data.get("taskId")
    new_status = data.get("status")

    if not task_id or not new_status:
        return jsonify({"error": "taskId and status required"}), 400

    task_ref = db.reference(f"tasks/{task_id}")
    task = task_ref.get()

    if not task:
        return jsonify({"error": "Task not found"}), 404

    task_ref.update({"status": new_status})

    if new_status.lower() == "completed":
        uid = task.get("assignedTo")
        if uid:
            user_ref = db.reference(f"users/{uid}")
            workload = user_ref.child("workload").get() or 0
            user_ref.child("workload").set(max(workload - 1, 0))

    return jsonify({"message": "Task updated successfully"})

@app.route("/tasks")
def all_tasks():
    return jsonify(db.reference("tasks").get() or {})

@app.route("/tasks/status/<status>")
def tasks_by_status(status):
    tasks = db.reference("tasks").get() or {}
    return jsonify([
        task for task in tasks.values()
        if task.get("status") == status
    ])

if __name__ == "__main__":
    app.run(debug=True)

