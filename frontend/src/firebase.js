import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Firebase Configuration
// Ensure you create a .env file in the frontend folder with these keys:
console.log("Firebase initialized successfully.");

const firebaseConfig = {
  apiKey: "AIzaSyDLDMXicIqQldzGuK-8E9QR4s6T9I0_DoI",
  authDomain: "myally-f6e6d.firebaseapp.com",
  projectId: "myally-f6e6d",
  storageBucket: "myally-f6e6d.firebasestorage.app",
  messagingSenderId: "233196735793",
  appId: "1:233196735793:web:bb386a5164f9edbe08f410"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
