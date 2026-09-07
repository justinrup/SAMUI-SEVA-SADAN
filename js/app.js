import { initializeApp } from "https://www.gstatic.com/firebasejs/12.2.1/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  signOut
} from "https://www.gstatic.com/firebasejs/12.2.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyDeJryLHlGc9Mx_kpo1IhmqnLC5EVYGBvM",
  authDomain: "samui-seva-sadan.firebaseapp.com",
  projectId: "samui-seva-sadan",
  storageBucket: "samui-seva-sadan.firebasestorage.app",
  messagingSenderId: "358488171058",
  appId: "1:358488171058:web:8be9c94e38f6618049522b",
  measurementId: "G-ML4BQ4QVLB"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const loginForm = document.getElementById("adminLoginForm");

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const message = document.getElementById("loginMessage");

    message.textContent = "Login হচ্ছে...";

    try {
      await signInWithEmailAndPassword(auth, email, password);

      message.textContent = "Login সফল হয়েছে।";

      setTimeout(() => {
        window.location.href = "admin-dashboard.html";
      }, 800);

    } catch (error) {
      message.textContent = "Email অথবা Password ভুল হয়েছে।";
      console.error(error);
    }
  });
}

window.adminLogout = async function () {
  await signOut(auth);
  window.location.href = "admin.html";
};

function searchPatient() {
  const input = document.getElementById("searchInput");
  const result = document.getElementById("searchResult");

  if (!input || !result) return;

  const value = input.value.trim();

  if (value === "") {
    result.textContent =
      "Please enter Patient Name, SL No., Room No. or Patient ID.";
    return;
  }

  result.textContent =
    "Search system is ready. Patient database will be connected in the next step.";
}

window.searchPatient = searchPatient;

import { getFirestore, collection, getDocs, query, where } from "https://www.gstatic.com/firebasejs/12.2.1/firebase-firestore.js";

const db = getFirestore(app);

async function loadPublishedDoctors() {
  const doctorList = document.getElementById("doctorList");
  if (!doctorList) return;

  try {
    const q = query(
      collection(db, "doctors"),
      where("published", "==", true)
    );

    const snapshot = await getDocs(q);

    if (snapshot.empty) {
      doctorList.innerHTML = "<p>No published doctors available.</p>";
      return;
    }

    doctorList.innerHTML = "";

    snapshot.forEach((docSnap) => {
      const d = docSnap.data();

      const card = document.createElement("div");
      card.className = "doctor-public-card";

      card.innerHTML = `
        <div class="doctor-icon">👨‍⚕️</div>
        <h3>${d.name || ""}</h3>
        <p><strong>Hospital:</strong> ${d.hospitalName || ""}</p>
        <p><strong>Specialist:</strong> ${d.specialist || ""}</p>
        <p><strong>Qualification:</strong> ${d.qualification || ""}</p>
        <p><strong>Time:</strong> ${d.doctorTime || ""}</p>
      `;

      doctorList.appendChild(card);
    });

  } catch (error) {
    console.error("Doctor loading error:", error);
    doctorList.innerHTML = "<p>Doctor information could not be loaded.</p>";
  }
}

loadPublishedDoctors();
