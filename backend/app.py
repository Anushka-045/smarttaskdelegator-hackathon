from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from flask_cors import CORS

# ---------------------------
# 🔥 FLASK INIT
# ---------------------------
app = Flask(__name__)
CORS(app)

# ---------------------------
# 🔐 FIREBASE INIT
# ---------------------------
cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://loginform-f0336-default-rtdb.firebaseio.com"
})


# ---------------------------
# 🏠 HOME ROUTE
# ---------------------------
@app.route("/")
def home():
    return "Backend is running 🚀"

# ---------------------------
# 👥 GET ALL USERS
# ---------------------------
@app.route("/users")
def get_users():
    users = db.reference("users").get()
    return jsonify(users)

# ---------------------------
# 🧠 SMART TASK ASSIGNMENT
# ---------------------------
@app.route("/assign-task", methods=["POST"])
def assign_task():
    data = request.json
    title = data.get("title")
    required_skill = data.get("requiredSkill")

    users = db.reference("users").get()

    best_user = None
    min_workload = float("inf")

    if users:
        for uid, user in users.items():
            skills = user.get("skills", [])
            workload = user.get("workload", 0)

            if required_skill in skills and workload < min_workload:
                best_user = uid
                min_workload = workload

    # ---------------------------
    # 📌 SAVE TASK
    # ---------------------------
    task_ref = db.reference("tasks").push({
        "title": title,
        "requiredSkill": required_skill,
        "assignedTo": best_user,
        "status": "Pending"
    })

    # ---------------------------
    # 🔄 UPDATE WORKLOAD
    # ---------------------------
    if best_user:
        db.reference(f"users/{best_user}/workload").set(min_workload + 1)

    return jsonify({
        "task": title,
        "assignedTo": best_user
    })

# ---------------------------
# 📋 GET TASKS FOR USER
# ---------------------------
@app.route("/my-tasks/<uid>")
def my_tasks(uid):
    tasks = db.reference("tasks").get()
    user_tasks = []

    if tasks:
        for task in tasks.values():
            if task.get("assignedTo") == uid:
                user_tasks.append(task)

    return jsonify(user_tasks)

# ---------------------------
# ▶ RUN SERVER
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)



