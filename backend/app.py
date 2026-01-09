from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("backend/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://loginform-f0336-default-rtdb.firebaseio.com"
})

@app.route("/assign-task", methods=["POST"])
def assign_task():
    data = request.json
    title = data["title"]
    skill = data["requiredSkill"].lower()

    users = db.reference("users").get()
    chosen = None
    min_load = 1e9

    for uid, user in users.items():
        skills = user.get("skills", [])
        workload = user.get("workload", 0)

        if skill in skills and workload < min_load:
            chosen = uid
            min_load = workload

    task = {
        "title": title,
        "requiredSkill": skill,
        "assignedTo": chosen,
        "status": "Pending"
    }

    db.reference("tasks").push(task)

    if chosen:
        db.reference(f"users/{chosen}/workload").set(min_load + 1)

    return jsonify({
        "task": title,
        "assignedTo": chosen
    })

if __name__ == "__main__":
    app.run(debug=True)
