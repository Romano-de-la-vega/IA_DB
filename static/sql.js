const themeBtn = document.getElementById('toggle-theme');
const settingsBtn = document.getElementById('settings-btn');
const modal = document.getElementById('settings-modal');
const closeSettings = document.getElementById('close-settings');
const settingsForm = document.getElementById('settings-form');
const testBtn = document.getElementById('test-conn');
const testResult = document.getElementById('test-result');
const queryForm = document.getElementById('query-form');
const responseBox = document.getElementById('response');
const answerSection = document.getElementById('answer');

// Theme toggle
(function initTheme() {
  const root = document.documentElement;
  const saved = localStorage.getItem('theme') || 'light';
  root.setAttribute('data-theme', saved);
  themeBtn.textContent = saved === 'dark' ? '☀️ Mode clair' : '🌙 Mode sombre';
  themeBtn.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    themeBtn.textContent = next === 'dark' ? '☀️ Mode clair' : '🌙 Mode sombre';
  });
})();

settingsBtn.addEventListener('click', () => {
  modal.style.display = 'block';
});
closeSettings.addEventListener('click', () => {
  modal.style.display = 'none';
});

settingsForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(settingsForm));
  const res = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (res.ok) {
    modal.style.display = 'none';
  } else {
    alert('Erreur de configuration');
  }
});

testBtn.addEventListener('click', async () => {
  const data = Object.fromEntries(new FormData(settingsForm));
  const res = await fetch('/api/config/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  testResult.textContent = res.ok ? 'Connexion OK' : 'Échec de connexion';
});

queryForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = document.getElementById('question').value.trim();
  if (!question) return;
  responseBox.textContent = 'Patientez...';
  answerSection.hidden = false;
  const res = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  if (res.ok) {
    const data = await res.json();
    responseBox.textContent = data.answer || 'Pas de réponse';
  } else {
    responseBox.textContent = 'Erreur: ' + (await res.text());
  }
});
