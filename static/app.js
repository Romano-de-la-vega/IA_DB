// ====== Sélecteurs ======
const themeBtn = document.getElementById("toggle-theme");
const settingsBtn = document.getElementById("toggle-settings");
const settingsCard = document.getElementById("settings");

const queryForm = document.getElementById("query-form");
const questionInput = document.getElementById("question");
const answerSection = document.getElementById("answer");
const resultPre = document.getElementById("result");
const testBtn = document.getElementById("test-conn");

// ====== Helpers ======
function getParams() {
  return {
    driver: document.getElementById("driver").value.trim(),
    host: document.getElementById("host").value.trim(),
    port: parseInt(document.getElementById("port").value, 10),
    database: document.getElementById("database").value.trim(),
    username: document.getElementById("username").value.trim(),
    password: document.getElementById("password").value,
    options: document.getElementById("options").value.trim(),
    api_key: document.getElementById("api_key").value.trim(),
  };
}

// ====== Thème ======
(function initTheme() {
  const root = document.documentElement;
  const saved = localStorage.getItem("theme") || "light";
  root.setAttribute("data-theme", saved);
  themeBtn.textContent = saved === "dark" ? "☀️ Mode clair" : "🌙 Mode sombre";

  themeBtn.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    themeBtn.textContent = next === "dark" ? "☀️ Mode clair" : "🌙 Mode sombre";
  });
})();

// ====== Paramètres ======
settingsBtn.addEventListener("click", () => {
  settingsCard.style.display = settingsCard.style.display === "none" ? "block" : "none";
});

testBtn.addEventListener("click", async () => {
  const params = getParams();
  try {
    const res = await fetch("/api/test-connection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(await res.text());
    alert("Connexion réussie");
  } catch (e) {
    alert("Échec de connexion: " + e.message);
  }
});

// ====== Requête ======
queryForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const params = getParams();
  const question = questionInput.value.trim();
  if (!question) {
    alert("Pose une question");
    return;
  }
  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...params, question }),
    });
    if (!res.ok) {
      resultPre.textContent = await res.text();
    } else {
      const data = await res.json();
      resultPre.textContent = data.answer || "";
    }
    answerSection.hidden = false;
  } catch (err) {
    resultPre.textContent = "Erreur: " + err.message;
    answerSection.hidden = false;
  }
});
