import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { 
    getAuth, 
    createUserWithEmailAndPassword, 
    signInWithEmailAndPassword, 
    signOut, 
    onAuthStateChanged 
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";


const firebaseConfig = {
    apiKey: process.env.FIREBASE_API_KEY || "YOUR_FIREBASE_API_KEY",
    authDomain: "jemulpogo-1-95533.firebaseapp.com",
    projectId: "jemulpogo-1-95533",
    storageBucket: "jemulpogo-1-95533.firebasestorage.app",
    messagingSenderId: "1007917237833",
    appId: process.env.FIREBASE_APP_ID || "YOUR_FIREBASE_APP_ID",
    measurementId: "G-FL3911N8M3"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

window.signUp = function() {
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;

    if (!email || !password) {
        alert('이메일과 비밀번호를 모두 입력하세요.');
        return;
    }

    createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            alert("회원가입 성공! 로그인 페이지로 이동합니다.");
            window.location.href = "login.html";
        })
        .catch((error) => {
            alert(`회원가입 실패: ${error.message}`);
        });
}

window.logIn = function() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    if (!email || !password) {
        alert('이메일과 비밀번호를 모두 입력하세요.');
        return;
    }

    signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            alert("로그인 성공! 메인 페이지로 이동합니다.");
            window.location.href = "main.html";
        })
        .catch((error) => {
            alert(`로그인 실패: ${error.message}`);
        });
}

window.logOut = function() {
    signOut(auth).then(() => {
        alert("로그아웃 되었습니다.");
        window.location.href = "index.html";
    }).catch((error) => {
        alert(`로그아웃 실패: ${error.message}`);
    });
}

onAuthStateChanged(auth, (user) => {
    if (user) {
        console.log(`${user.email} 님, 환영합니다.`);
    } else {
        console.log('로그아웃 상태입니다.');
    }
});
