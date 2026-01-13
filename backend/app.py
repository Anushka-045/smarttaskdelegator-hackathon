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

@app.route("/add-user", methods=["POST"])
def add_user():
    data = request.json
    db.reference(f"teams/{data['teamId']}/users").push({
        "username": data["username"],
        "skills": [s.strip().lower() for s in data["skills"].split(",")],
        "date": data["date"],
        "free_from": data["from"],
        "free_to": data["to"],
        "workload": 0,
        "max_load": data["maxLoad"],
        "active": True
    })
    return jsonify({"message": "User added"})

@app.route("/assign-task", methods=["POST"])
def assign_task():
    data = request.json
    users = db.reference(f"teams/{data['teamId']}/users").get()
    best=None; best_id=None; min_load=999

    for uid,u in (users or {}).items():
        if data["requiredSkill"] not in u["skills"]: continue
        if u["workload"]>=u["max_load"]: continue
        if u["workload"]<min_load:
            min_load=u["workload"]
            best=u["username"]
            best_id=uid

    if not best_id:
        return jsonify({"assignedUsername":None})

    db.reference(f"teams/{data['teamId']}/tasks").push({
        "title":data["title"],
        "assignedUsername":best,
        "status":"Pending"
    })

    db.reference(f"teams/{data['teamId']}/users/{best_id}/workload").set(min_load+1)

    return jsonify({"assignedUsername":best,"status":"Pending"})

if __name__=="__main__":
    app.run(debug=True)