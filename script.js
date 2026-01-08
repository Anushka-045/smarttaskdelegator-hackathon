
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.7.0/firebase-app.js";

import {
    getDatabase,
    ref,
    set,
    update,
    push,
    get,
    onValue
} from "https://www.gstatic.com/firebasejs/12.7.0/firebase-database.js";

import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.7.0/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyAgyMmefbJjeMBRK8lZ_MgkfgcsTwo2Q7M",
    authDomain: "loginform-f0336.firebaseapp.com",
    databaseURL: "https://loginform-f0336-default-rtdb.firebaseio.com",
    projectId: "loginform-f0336",
    storageBucket: "loginform-f0336.firebasestorage.app",
    messagingSenderId: "444250525738",
    appId: "1:444250525738:web:04580411603a5c37ef7353"
};

const app = initializeApp(firebaseConfig);
export const db = getDatabase(app);
export const auth = getAuth(app);


export function signup(username, email, password, phone) {

    createUserWithEmailAndPassword(auth, email, password)
    .then(res => {
        return set(ref(db, "users/" + res.user.uid), {
            username,
            email,
            phone,
            skills: [],
            workload: 0,
            role: "user"
        });
    })
    .then(() => {
        window.location.href = "index.html";
    })
    .catch(err => {

        // Account exists → login
        if (err.code === "auth/email-already-in-use") {
            signInWithEmailAndPassword(auth, email, password)
            .then(() => {
                window.location.href = "index.html";
            })
            .catch(e => alert(e.message));
        } else {
            alert(err.message);
        }
    });
}


export function logout() {
    signOut(auth).then(() => {
        window.location.href = "login.html";
    });
}


export function protectPage() {
    onAuthStateChanged(auth, user => {
        if (!user) window.location.href = "login.html";
    });
}

export function updateProfile(skills, workload) {
    const user = auth.currentUser;
    if (!user) return;

    update(ref(db, "users/" + user.uid), {
        skills: skills.split(",").map(s => s.trim()),
        workload: Number(workload)
    }).then(() => alert("Profile updated!"));
}

export async function createSmartTask(title, requiredSkill) {

    const usersSnap = await get(ref(db, "users"));

    let bestUser = null;
    let minLoad = Infinity;

    usersSnap.forEach(u => {
        const d = u.val();
        if (d.skills?.includes(requiredSkill) && d.workload < minLoad) {
            bestUser = u.key;
            minLoad = d.workload;
        }
    });

    await push(ref(db, "tasks"), {
        title,
        requiredSkill,
        assignedTo: bestUser || "unassigned",
        status: "Pending",
        createdAt: new Date().toISOString()
    });

    if (bestUser) {
        update(ref(db, "users/" + bestUser), {
            workload: minLoad + 1
        });
    }

    alert("✅ Task assigned!");
}


export function loadTasks(containerId) {
    const container = document.getElementById(containerId);

    onValue(ref(db, "tasks"), snap => {
        container.innerHTML = "";
        snap.forEach(t => {
            const task = t.val();
            container.innerHTML += `
                <div class="task-card">
                    <h3>${task.title}</h3>
                    <p>Skill: ${task.requiredSkill}</p>
                    <p>Status: ${task.status}</p>
                    <p>Assigned: ${task.assignedTo}</p>
                </div>
            `;
        });
    });
}

