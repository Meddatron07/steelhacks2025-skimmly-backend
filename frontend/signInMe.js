import { initializeApp } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, onAuthStateChanged, sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-auth.js";

// This is your Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyDQ6xASmHq4vyvDqXiOQq7PabBOj_WOmDc",
    authDomain: "skimmly-c09f7.firebaseapp.com",
    projectId: "skimmly-c09f7",
    storageBucket: "skimmly-c09f7.firebasestorage.app",
    messagingSenderId: "154158134317",
    appId: "1:154158134317:web:751e47b3f9c65c98b2f4a4",
    measurementId: "G-RZ1VLVC5JC"
};

// Initialize Firebase with your config
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

function showMessage(message) {
    const messageElement = document.getElementById('modalMessage');
    if (messageElement) {
        messageElement.textContent = message;
        document.getElementById('messageModal').style.display = 'flex';
    }
}

onAuthStateChanged(auth, (user) => {
    if (user) {
        window.location.href = "profile.html";
    }
});

document.getElementById('signInButton').addEventListener('click', async () => {
    const email = document.getElementById('signInEmail').value;
    const password = document.getElementById('signInPassword').value;
   
    try {
        await signInWithEmailAndPassword(auth, email, password);
        showMessage("Login successful!");
    } catch (error) {
        console.error("Error signing in:", error.code, error.message);
        if (error.code === 'auth/invalid-credential') {
             showMessage("Invalid email or password. Please try again.");
        } else {
            showMessage("An error occurred. Please try again later.");
        }
    }
});