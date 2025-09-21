import { initializeApp } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-app.js";
import { getFirestore, doc, getDoc, onSnapshot, updateDoc, setDoc } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-firestore.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyDQ6xASmHq4vyvDqXiOQq7PabBOj_WOmDc",
    authDomain: "skimmly-c09f7.firebaseapp.com",
    projectId: "skimmly-c09f7",
    storageBucket: "skimmly-c09f7.firebasestorage.app",
    messagingSenderId: "154158134317",
    appId: "1:154158134317:web:751e47b3f9c65c98b2f4a4",
    measurementId: "G-RZ1VLVC5JC"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const auth = getAuth(app);

const scoreDocRef = doc(db, 'app-data', 'scores');

onSnapshot(scoreDocRef, (docSnapshot) => {
    if (docSnapshot.exists()) {
        const data = docSnapshot.data();
        document.getElementById('score').textContent = data.totalScore;
    } else {
        setDoc(scoreDocRef, { totalScore: 0 });
    }
});

const cards = document.querySelectorAll('.card');
const signInButton = document.querySelector('.Sign-In-button');
const signUpButton = document.querySelector('.Sign-Up-button');

cards.forEach(card => {
    card.addEventListener('click', async () => {
        if (card.classList.contains('clicked')) {
            return;
        }

        const points = parseInt(card.dataset.points);

        try {
            const docSnap = await getDoc(scoreDocRef);
            const currentScore = docSnap.data().totalScore;

            await updateDoc(scoreDocRef, {
                totalScore: currentScore + points
            });

            card.classList.add('clicked');
        } catch (error) {
            console.error("Error updating score:", error);
        }
    });
});

if (signInButton) {
    signInButton.addEventListener('click', () => {
        window.location.href = "signIn.html";
    });
}

if (signUpButton) {
    signUpButton.addEventListener('click', () => {
        window.location.href = "signUp.html";
    });
}

// Authentication state management for landing page
onAuthStateChanged(auth, (user) => {
    const signInButton = document.querySelector('.Sign-In-button');
    const signUpButton = document.querySelector('.Sign-Up-button');
    const getStartedButton = document.querySelector('.Get-started-button');

    if (user) {
        // User is signed in, show sign out button and profile access
        if (signInButton) {
            signInButton.textContent = 'Profile';
            signInButton.onclick = () => window.location.href = 'profile.html';
        }
        if (signUpButton) {
            signUpButton.textContent = 'Sign Out';
            signUpButton.onclick = async () => {
                try {
                    await signOut(auth);
                    window.location.reload(); // Refresh to update UI
                } catch (error) {
                    console.error('Error signing out:', error);
                }
            };
        }
        if (getStartedButton) {
            getStartedButton.textContent = 'Go to Profile';
            getStartedButton.onclick = () => window.location.href = 'profile.html';
        }
    } else {
        // User is signed out, show default buttons
        if (signInButton) {
            signInButton.textContent = 'Sign In';
            signInButton.onclick = () => window.location.href = 'signIn.html';
        }
        if (signUpButton) {
            signUpButton.textContent = 'Sign Up';
            signUpButton.onclick = () => window.location.href = 'signUp.html';
        }
        if (getStartedButton) {
            getStartedButton.textContent = 'Get Started';
            getStartedButton.onclick = () => window.location.href = 'signUp.html';
        }
    }
});