const API = '';

// ─────────────────────────────────────────────
// Tab switching
// ─────────────────────────────────────────────

function switchTab(tab) {
    const loginForm    = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const tabLogin     = document.getElementById('tab-login');
    const tabReg       = document.getElementById('tab-register');
    const indicator    = document.getElementById('tab-indicator');

    hideBanner();

    if (tab === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        tabLogin.classList.add('active');
        tabReg.classList.remove('active');
        indicator.classList.remove('right');
    } else {
        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
        tabReg.classList.add('active');
        tabLogin.classList.remove('active');
        indicator.classList.add('right');
    }
}

// ─────────────────────────────────────────────
// Banner helpers
// ─────────────────────────────────────────────

function showBanner(message, type = 'error') {
    const banner = document.getElementById('banner');
    banner.textContent = message;
    banner.className = `banner ${type}`;
}

function hideBanner() {
    document.getElementById('banner').className = 'banner hidden';
}

// ─────────────────────────────────────────────
// Password visibility toggle
// ─────────────────────────────────────────────

function togglePw(inputId, btn) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '🙈';
    } else {
        input.type = 'password';
        btn.textContent = '👁';
    }
}

// ─────────────────────────────────────────────
// Spinner helpers
// ─────────────────────────────────────────────

function setLoading(btnId, spinnerId, loading) {
    const btn     = document.getElementById(btnId);
    const spinner = document.getElementById(spinnerId);
    const text    = btn.querySelector('.btn-text');

    btn.disabled = loading;
    spinner.classList.toggle('hidden', !loading);
    text.style.opacity = loading ? '0.6' : '1';
}

// ─────────────────────────────────────────────
// LOGIN
// ─────────────────────────────────────────────

async function handleLogin(event) {
    event.preventDefault();
    hideBanner();

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showBanner('Please fill in all fields.');
        return;
    }

    setLoading('login-btn', 'login-spinner', true);

    try {
        // /token uses application/x-www-form-urlencoded (OAuth2 standard)
        const body = new URLSearchParams({ username, password });

        const res = await fetch(`${API}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body.toString()
        });

        const data = await res.json();

        if (!res.ok) {
            showBanner(data.detail || 'Login failed. Check your credentials.');
            return;
        }

        // Store token and redirect
        localStorage.setItem('token', data.access_token);
        showBanner('Login successful! Redirecting…', 'success');

        setTimeout(() => {
            window.location.href = '../invoice/invoices.html';
        }, 800);

    } catch (err) {
        console.error(err);
        showBanner('Could not connect to the server. Is it running?');
    } finally {
        setLoading('login-btn', 'login-spinner', false);
    }
}

// ─────────────────────────────────────────────
// REGISTER
// ─────────────────────────────────────────────

async function handleRegister(event) {
    event.preventDefault();
    hideBanner();

    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirm  = document.getElementById('reg-confirm').value;

    if (!username || !password || !confirm) {
        showBanner('Please fill in all fields.');
        return;
    }

    if (password !== confirm) {
        showBanner('Passwords do not match.');
        return;
    }

    if (password.length < 6) {
        showBanner('Password must be at least 6 characters.');
        return;
    }

    setLoading('reg-btn', 'reg-spinner', true);

    try {
        const res = await fetch(`${API}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (!res.ok) {
            showBanner(data.detail || 'Registration failed.');
            return;
        }

        showBanner('Account created! Switching to login…', 'success');
        setTimeout(() => switchTab('login'), 1200);

    } catch (err) {
        console.error(err);
        showBanner('Could not connect to the server. Is it running?');
    } finally {
        setLoading('reg-btn', 'reg-spinner', false);
    }
}

// ─────────────────────────────────────────────
// If already logged in, skip the auth page
// ─────────────────────────────────────────────

(function checkAlreadyLoggedIn() {
    if (localStorage.getItem('token')) {
        window.location.href = '../invoice/invoices.html';
    }
})();
