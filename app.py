import os
import json
from flask import Flask, request, jsonify, render_template_string
from google import genai
from google.genai import types

app = Flask(__name__)

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    return genai.Client(api_key=api_key)

SYSTEM_PROMPT = """You are BLURO, an evidence-based scientific research AI assistant.
Respond ONLY in valid JSON with the exact keys below (no markdown blocks, no extra text):
{
  "direct_answer": "Clear, direct, accurate scientific answer in 2-4 sentences.",
  "evidence": [
    "Key scientific evidence point 1 with concrete data/mechanism",
    "Key scientific evidence point 2 with empirical findings"
  ],
  "sources": [
    "Verified institution, peer-reviewed journal, or space agency (e.g., NASA, Nature, ESA, CERN)"
  ],
  "confidence": "98% (High Empirical Consensus)"
}
Use the same language as the user's question (English or Bengali)."""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>BLURO</title>
<style>
  :root {
    --bg: #0a0a0c;
    --surface: #141418;
    --surface-hover: #1c1c22;
    --border: #26262e;
    --text: #f4f4f6;
    --muted: #8e8e9a;
    --accent: #0052FF;
    --accent-glow: rgba(0, 82, 255, 0.45);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    height: 100dvh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* Top Navigation Pill - No Logo */
  .top-bar {
    padding: 14px 16px 10px;
    display: flex;
    justify-content: center;
    background: var(--bg);
    z-index: 10;
  }
  .tab-pill {
    display: flex;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 4px;
    width: 100%;
    max-width: 340px;
  }
  .tab-btn {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--muted);
    font-size: 14px;
    font-weight: 600;
    padding: 8px 14px;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.25s ease;
  }
  .tab-btn.active {
    background: #23232b;
    color: var(--text);
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  }

  /* Views */
  .view {
    flex: 1;
    overflow-y: auto;
    display: none;
    flex-direction: column;
    padding: 16px;
  }
  .view.active { display: flex; }

  /* Hero Empty State */
  .hero {
    margin: auto;
    text-align: center;
    padding: 20px;
  }
  .hero h1 {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 3px;
    color: var(--text);
  }
  .hero p {
    margin-top: 8px;
    font-size: 13px;
    color: var(--muted);
  }

  /* Chat Messages */
  .chat-feed {
    display: flex;
    flex-direction: column;
    gap: 18px;
    max-width: 720px;
    width: 100%;
    margin: 0 auto;
    padding-bottom: 16px;
  }
  .msg-user {
    align-self: flex-end;
    background: var(--accent);
    color: #fff;
    padding: 11px 16px;
    border-radius: 20px 20px 4px 20px;
    font-size: 15px;
    line-height: 1.45;
    max-width: 82%;
    word-wrap: break-word;
  }

  /* Custom BLURO Thinking Pulse Animation */
  .thinking-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 4px;
  }
  .bluro-orb {
    width: 13px;
    height: 13px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 0 0 var(--accent-glow);
    animation: bluroPulse 1.3s infinite ease-in-out;
  }
  @keyframes bluroPulse {
    0% { transform: scale(0.85); box-shadow: 0 0 0 0 rgba(0, 82, 255, 0.7); }
    50% { transform: scale(1.25); box-shadow: 0 0 0 10px rgba(0, 82, 255, 0); }
    100% { transform: scale(0.85); box-shadow: 0 0 0 0 rgba(0, 82, 255, 0); }
  }
  .thinking-label {
    font-size: 13px;
    color: var(--muted);
    letter-spacing: 0.3px;
    animation: fadeText 1.3s infinite ease-in-out;
  }
  @keyframes fadeText {
    0%, 100% { opacity: 0.45; }
    50% { opacity: 1; }
  }

  /* AI Answer Card */
  .ai-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px;
    animation: slideUp 0.3s ease;
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .badge-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  .bluro-tag {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #5b93ff;
  }
  .conf-badge {
    font-size: 11px;
    background: rgba(0, 82, 255, 0.15);
    color: #7aa8ff;
    padding: 3px 9px;
    border-radius: 999px;
    border: 1px solid rgba(0, 82, 255, 0.3);
  }
  .direct-text {
    font-size: 15px;
    line-height: 1.6;
    color: var(--text);
  }
  .evidence-toggle {
    margin-top: 12px;
    background: var(--surface-hover);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 10px;
    cursor: pointer;
    width: 100%;
    text-align: left;
    display: flex;
    justify-content: space-between;
  }
  .evidence-box {
    display: none;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid var(--border);
    font-size: 13.5px;
    line-height: 1.55;
    color: #d2d2dc;
  }
  .evidence-box.open { display: block; }
  .evidence-box ul { padding-left: 18px; margin-bottom: 10px; }
  .evidence-box li { margin-bottom: 6px; }
  .sources-list {
    font-size: 12px;
    color: var(--muted);
    background: #0f0f13;
    padding: 8px 10px;
    border-radius: 8px;
  }

  /* Science Library */
  .lib-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
    max-width: 720px;
    width: 100%;
    margin: 0 auto;
    padding-bottom: 24px;
  }
  .lib-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px;
    cursor: pointer;
    transition: border-color 0.2s;
  }
  .lib-card:active { border-color: var(--accent); }
  .lib-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
  .lib-sub { font-size: 13px; color: var(--muted); }

  /* Bottom Input Bar */
  .input-dock {
    padding: 10px 14px 16px;
    background: var(--bg);
    border-top: 1px solid #18181f;
  }
  .input-box {
    max-width: 720px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 6px 8px 6px 18px;
  }
  .input-box input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-size: 15px;
  }
  .input-box input::placeholder { color: var(--muted); }
  .send-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    background: var(--accent);
    color: #fff;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .send-btn:disabled { opacity: 0.4; }
</style>
</head>
<body>

  <div class="top-bar">
    <div class="tab-pill">
      <button class="tab-btn active" id="btnChat" onclick="switchTab('chat')">Chat</button>
      <button class="tab-btn" id="btnLib" onclick="switchTab('lib')">Science Library</button>
    </div>
  </div>

  <!-- Chat View -->
  <div class="view active" id="viewChat">
    <div class="hero" id="heroScreen">
      <h1>BLURO</h1>
      <p>Evidence-Based Science Research</p>
    </div>
    <div class="chat-feed" id="chatFeed"></div>
  </div>

  <!-- Science Library View -->
  <div class="view" id="viewLib">
    <div class="lib-grid" id="libGrid"></div>
  </div>

  <!-- Input Bar -->
  <div class="input-dock" id="inputDock">
    <div class="input-box">
      <input type="text" id="qInput" placeholder="ask bluro" autocomplete="off" onkeypress="if(event.key==='Enter') sendQuery()">
      <button class="send-btn" id="sendBtn" onclick="sendQuery()">↑</button>
    </div>
  </div>

<script>
const CATEGORIES = [
  { name: "Space & Universe", desc: "Black holes, dark matter, JWST & cosmology", prompt: "Explain how Sagittarius A* supermassive black hole shapes the Milky Way galaxy with scientific evidence." },
  { name: "Physics", desc: "Relativity, quantum mechanics & spacetime", prompt: "Explain Einstein's 4D Minkowski spacetime and time dilation near massive objects with experimental proof." },
  { name: "Chemistry", desc: "Elements, molecular reactions & astrochemistry", prompt: "How are heavy elements like gold and iron forged in neutron star collisions and supernovae?" },
  { name: "Biology", desc: "Evolution, genetics & extremophile life", prompt: "How do extremophiles survive deep-sea hydrothermal vents and what does it mean for astrobiology?" },
  { name: "Earth & Climate", desc: "Atmosphere, magnetosphere & geology", prompt: "How does Earth's magnetic field protect our atmosphere from solar wind stripping?" },
  { name: "Animals", desc: "Wildlife ecology, predator biology & behavior", prompt: "Explain the bite force, bone-crushing adaptation, and ecological role of spotted hyenas and African lions." },
  { name: "Astronomy", desc: "Exoplanets, solar system & observational science", prompt: "How do astronomers detect exoplanet atmospheres using transit spectroscopy?" }
];

const libGrid = document.getElementById('libGrid');
CATEGORIES.forEach(cat => {
  const card = document.createElement('div');
  card.className = 'lib-card';
  card.innerHTML = `<div class="lib-title">${cat.name}</div><div class="lib-sub">${cat.desc}</div>`;
  card.onclick = () => {
    switchTab('chat');
    document.getElementById('qInput').value = cat.prompt;
    sendQuery();
  };
  libGrid.appendChild(card);
});

function switchTab(tab) {
  document.getElementById('btnChat').classList.toggle('active', tab === 'chat');
  document.getElementById('btnLib').classList.toggle('active', tab === 'lib');
  document.getElementById('viewChat').classList.toggle('active', tab === 'chat');
  document.getElementById('viewLib').classList.toggle('active', tab === 'lib');
  document.getElementById('inputDock').style.display = tab === 'chat' ? 'block' : 'none';
}

async function sendQuery() {
  const input = document.getElementById('qInput');
  const question = input.value.trim();
  if (!question) return;

  const hero = document.getElementById('heroScreen');
  if (hero) hero.style.display = 'none';

  const feed = document.getElementById('chatFeed');
  const viewChat = document.getElementById('viewChat');

  const userDiv = document.createElement('div');
  userDiv.className = 'msg-user';
  userDiv.textContent = question;
  feed.appendChild(userDiv);

  input.value = '';
  document.getElementById('sendBtn').disabled = true;

  const thinkDiv = document.createElement('div');
  thinkDiv.className = 'thinking-wrap';
  thinkDiv.innerHTML = `<div class="bluro-orb"></div><span class="thinking-label">Researching evidence...</span>`;
  feed.appendChild(thinkDiv);
  viewChat.scrollTop = viewChat.scrollHeight;

  try {
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const data = await res.json();
    thinkDiv.remove();

    const card = document.createElement('div');
    card.className = 'ai-card';
    const evId = 'ev_' + Date.now();
    const evList = (data.evidence || []).map(e => `<li>${e}</li>`).join('');
    const srcText = (data.sources || []).join(' • ');

    card.innerHTML = `
      <div class="badge-row">
        <span class="bluro-tag">BLURO</span>
        <span class="conf-badge">${data.confidence || 'Verified Science'}</span>
      </div>
      <div class="direct-text">${data.direct_answer || data.error || 'No response generated.'}</div>
      ${evList ? `
        <button class="evidence-toggle" onclick="document.getElementById('${evId}').classList.toggle('open')">
          <span>Show Evidence & Sources</span><span>▾</span>
        </button>
        <div class="evidence-box" id="${evId}">
          <ul>${evList}</ul>
          <div class="sources-list"><strong>Sources:</strong> ${srcText}</div>
        </div>
      ` : ''}
    `;
    feed.appendChild(card);
  } catch (err) {
    thinkDiv.remove();
    const errDiv = document.createElement('div');
    errDiv.className = 'ai-card';
    errDiv.innerHTML = `<div class="direct-text">Connection error. Please try again.</div>`;
    feed.appendChild(errDiv);
  }

  document.getElementById('sendBtn').disabled = false;
  viewChat.scrollTop = viewChat.scrollHeight;
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400
    try:
        client = get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        result = json.loads(response.text)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "direct_answer": f"Research error: {str(e)}",
            "evidence": [],
            "sources": [],
            "confidence": "Error"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
