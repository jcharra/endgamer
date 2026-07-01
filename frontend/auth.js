const API_BASE = 'http://localhost:8001';

let mode = 'login';
let currentUser = null;

// Fetches the currently logged-in user from the backend, or null if nobody is logged in.
async function fetchMe() {
  const res = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' });
  const data = await res.json();
  return data.user;
}

// Updates the nav bar to show either the logged-in user's name + score + a
// logout button, or a login button, depending on whether `user` is present.
function renderUser(user) {
  currentUser = user;
  const usernameEl = document.getElementById('nav-username');
  const scoreEl = document.getElementById('nav-score');
  const logoutBtn = document.getElementById('nav-logout-btn');
  const loginBtn = document.getElementById('nav-login-btn');
  if (user) {
    usernameEl.textContent = user.name || user.email;
    usernameEl.style.display = '';
    scoreEl.textContent = `Score: ${user.score}`;
    scoreEl.style.display = '';
    logoutBtn.style.display = '';
    loginBtn.style.display = 'none';
  } else {
    usernameEl.style.display = 'none';
    scoreEl.style.display = 'none';
    logoutBtn.style.display = 'none';
    loginBtn.style.display = '';
  }
}

// Called by index.js whenever a checkmate win reports a new score, so the
// nav bar stays live without needing a full /auth/me round trip.
export function updateScore(score) {
  if (currentUser === null) return;
  currentUser = { ...currentUser, score };
  document.getElementById('nav-score').textContent = `Score: ${score}`;
}

function showModal() {
  document.getElementById('auth-modal').classList.add('visible');
}

function hideModal() {
  document.getElementById('auth-modal').classList.remove('visible');
  document.getElementById('auth-error').textContent = '';
  document.getElementById('auth-form').reset();
}

// Switches the modal between "login" and "signup" mode, toggling the name
// field and updating the tab/submit-button labels accordingly.
function setMode(newMode) {
  mode = newMode;
  document.querySelectorAll('#auth-tabs button').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });
  document.getElementById('auth-name').style.display = mode === 'signup' ? '' : 'none';
  document.getElementById('auth-submit-btn').textContent = mode === 'signup' ? 'Sign up' : 'Login';
  document.getElementById('auth-error').textContent = '';
}

document.getElementById('nav-login-btn').addEventListener('click', () => {
  setMode('login');
  showModal();
});

document.getElementById('auth-modal-close').addEventListener('click', hideModal);

document.querySelectorAll('#auth-tabs button').forEach((btn) => {
  btn.addEventListener('click', () => setMode(btn.dataset.mode));
});

document.getElementById('auth-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('auth-email').value;
  const password = document.getElementById('auth-password').value;
  const name = document.getElementById('auth-name').value;
  const endpoint = mode === 'signup' ? '/auth/register' : '/auth/login';
  const body = mode === 'signup' ? { email, password, name } : { email, password };

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.error) {
    document.getElementById('auth-error').textContent = data.error;
    return;
  }
  hideModal();
  renderUser(data.user);
});

document.getElementById('nav-logout-btn').addEventListener('click', async () => {
  await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' });
  renderUser(null);
});

document.getElementById('google-login-btn').addEventListener('click', () => {
  window.location.href = `${API_BASE}/auth/google/login`;
});

document.getElementById('apple-login-btn').addEventListener('click', async () => {
  const res = await fetch(`${API_BASE}/auth/apple/login`, { credentials: 'include' });
  const data = await res.json();
  document.getElementById('auth-error').textContent = data.error || 'Apple sign-in is unavailable.';
});

renderUser(await fetchMe());
