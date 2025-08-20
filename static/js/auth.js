/**
 * 제물포GO 인증 시스템
 * 백엔드 Flask API와 연동하는 클라이언트사이드 인증 스크립트
 */

// 유틸리티 함수: API 요청
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include', // 세션 쿠키 포함
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || '요청 실패');
        }
        
        return result;
    } catch (error) {
        console.error('API 요청 오류:', error);
        throw error;
    }
}

// 로그인 처리
window.logIn = async function() {
    const email = document.getElementById('login-email')?.value || '';
    const password = document.getElementById('login-password')?.value || '';

    if (!email || !password) {
        alert('이메일과 비밀번호를 모두 입력하세요.');
        return;
    }

    try {
        const result = await apiRequest('/api/login', 'POST', {
            email: email,
            password: password
        });

        if (result.success) {
            alert('로그인 성공! 메인 페이지로 이동합니다.');
            window.location.href = '/main';
        }
    } catch (error) {
        alert(`로그인 실패: ${error.message}`);
    }
}

// 회원가입 처리
window.signUp = async function() {
    const email = document.getElementById('signup-email')?.value || '';
    const password = document.getElementById('signup-password')?.value || '';
    const confirmPassword = document.getElementById('confirm-password')?.value || '';

    if (!email || !password || !confirmPassword) {
        alert('모든 필드를 입력하세요.');
        return;
    }

    if (password !== confirmPassword) {
        alert('비밀번호가 일치하지 않습니다.');
        return;
    }

    if (password.length < 6) {
        alert('비밀번호는 6자 이상이어야 합니다.');
        return;
    }

    try {
        const result = await apiRequest('/api/signup', 'POST', {
            email: email,
            password: password,
            confirm_password: confirmPassword
        });

        if (result.success) {
            alert('회원가입 성공! 메인 페이지로 이동합니다.');
            window.location.href = '/main';
        }
    } catch (error) {
        alert(`회원가입 실패: ${error.message}`);
    }
}

// 로그아웃 처리
window.logOut = async function() {
    try {
        const result = await apiRequest('/api/logout', 'POST');
        
        if (result.success) {
            alert('로그아웃 되었습니다.');
            window.location.href = '/';
        }
    } catch (error) {
        console.error('로그아웃 오류:', error);
        alert(`로그아웃 실패: ${error.message}`);
        // 실패하더라도 홈으로 이동
        window.location.href = '/';
    }
}

// 세션 상태 확인
window.checkSession = async function() {
    try {
        const result = await apiRequest('/api/session-check');
        return result;
    } catch (error) {
        console.error('세션 확인 오류:', error);
        return { logged_in: false };
    }
}

// 페이지 로드 시 세션 확인
window.checkAuth = function() {
    // 세션 체크는 백엔드에서 자동으로 처리됨
    // 필요시 여기서 추가 클라이언트 사이드 로직 구현
    console.log('인증 상태 확인 중...');
}

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
});
