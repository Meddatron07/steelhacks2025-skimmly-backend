import { initializeApp } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-auth.js";
import { getFirestore, doc, setDoc } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-firestore.js";

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
const db = getFirestore(app);

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

document.getElementById('signUpButton').addEventListener('click', async () => {
    const firstName = document.getElementById('signUpFirstName').value.trim();
    const lastName = document.getElementById('signUpLastName').value.trim();
    const email = document.getElementById('signUpEmail').value.trim();
    const password = document.getElementById('signUpPassword').value;

    console.log('Sign up attempt:', { firstName, lastName, email, passwordLength: password.length });

    if (!firstName || !lastName || !email || !password) {
        showMessage("Please fill out all fields.");
        return;
    }

    if (password.length < 6) {
        showMessage("Password must be at least 6 characters long.");
        return;
    }
   
    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
       
        // Sync user with Flask backend (optional - don't block on this)
        const idToken = await user.getIdToken();

        try {
            const response = await fetch('https://steelhacks2025-skimmly-backend.onrender.com/api/firebase-sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${idToken}`
                },
                body: JSON.stringify({
                    firstName: firstName,
                    lastName: lastName
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('User synced with backend:', result);
                showMessage("Account created successfully!");
            } else {
                console.warn('Backend sync failed, but account created:', await response.text());
                showMessage("Account created successfully! (Note: Some features may be limited until backend is configured)");
            }
        } catch (error) {
            console.warn('Error syncing with backend, but account created:', error);
            showMessage("Account created successfully! (Note: Some features may be limited until backend is configured)");
        }
    } catch (error) {
        console.error("Error signing up:", error.code, error.message);
        if (error.code === 'auth/email-already-in-use') {
            showMessage("This email is already in use. Please sign in or use a different email.");
        } else if (error.code === 'auth/weak-password') {
            showMessage("Password is too weak. Please use a stronger password.");
        } else if (error.code === 'auth/invalid-email') {
            showMessage("The email address is not valid.");
        } else {
            showMessage(`Error: ${error.message || 'An error occurred. Please try again later.'}`);
        }
    }
});