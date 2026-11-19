import os
from flask import Flask, render_template_string, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# সার্ভারের Environment Variable থেকে নিরাপদে API Key নেবে
API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY) if API_KEY else None

SYSTEM_INSTRUCTION = """
You are Bluro, an elite AI Science & Space Research Assistant.
Deliver direct, fascinating, evidence-based scientific answers with crystal-clear structure.
Use bullet points for key insights, cite real scientific consensus or missions (NASA, JWST, peer-reviewed biology), and end every response with:
📊 Confidence Score: [XX]% — [Consensus Level]
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#090b10">
    <title>Bluro AI</title>
    <style>
        :root {
            --bg-main: #090b10;
            --bg-card: #121620;
            --bg-input: #161b26;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.25);
            --text-primary: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #1e293b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background-color: var(--bg-main); color: var(--text-primary); display: flex; flex-direction: column; height: 100dvh; overflow: hidden; }
        
        /* Header */
        header { background: rgba(9, 11, 16, 0.85); backdrop-filter: blur(12px); padding: 14px 18px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; z-index: 10; }
        .brand { display: flex; align-items: center; gap: 10px; }
        .logo-orb { width: 26px; height: 26px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, #7dd3fc, #0284c7); box-shadow: 0 0 12px var(--accent-glow); animation: pulseOrb 3s infinite ease-in-out; }
        @keyframes pulseOrb { 0%, 100% { transform: scale(1); box-shadow: 0 0 12px var(--accent-glow); } 50% { transform: scale(1.08); box-shadow: 0 0 20px rgba(56, 189, 248, 0.5); } }
        header h1 { font-size: 19px; font-weight: 700; letter-spacing: 0.6px; background: linear-gradient(90deg, #fff, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .new-chat-btn { background: var(--bg-card); border: 1px solid var(--border); color: var(--text-primary); padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .new-chat-btn:active { transform: scale(0.95); background: #1e293b; }

        /* Chat Container */
        #chat-box { flex: 1; overflow-y: auto; padding: 18px 16px; display: flex; flex-direction: column; gap: 16px; scroll-behavior: smooth; }
        
        /* Welcome Screen */
        .welcome { margin: auto; text-align: center; max-width: 360px; animation: fadeIn 0.6s ease-out; }
        .welcome-orb { width: 58px; height: 58px; margin: 0 auto 16px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, #38bdf8, #1d4ed8, #090b10); box-shadow: 0 0 30px var(--accent-glow); }
        .welcome h2 { font-size: 24px; font-weight: 700; margin-bottom: 8px; color: #fff; }
        .welcome p { font-size: 14px; color: var(--text-muted); line-height: 1.5; margin-bottom: 22px; }
        .chips { display: flex; flex-direction: column; gap: 10px; }
        .chip { background: var(--bg-card); border: 1px solid var(--border); padding: 12px 14px; border-radius: 14px; font-size: 13px; color: #cbd5e1; text-align: left; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 10px; }
        .chip:active { transform: scale(0.98); border-color: var(--accent); background: #161d2b; }

        /* Messages */
        .msg { max-width: 88%; padding: 13px 16px; border-radius: 18px; line-height: 1.55; font-size: 15px; word-wrap: break-word; white-space: pre-wrap; animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
        @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .user-msg { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; align-self: flex-end; border-bottom-right-radius: 4px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25); }
        .ai-msg { background: var(--bg-card); color: var(--text-primary); align-self: flex-start; border: 1px solid var(--border); border-bottom-left-radius: 4px; }
        
        /* Typing Loader */
        .typing-dots { display: inline-flex; gap: 5px; padding: 4px 2px; }
        .typing-dots span { width: 7px; height: 7px; background: var(--accent); border-radius: 50%; animation: bounce 1.2s infinite ease-in-out; }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1.1); opacity: 1; } }

        /* Input Bar */
        #input-wrapper { padding: 10px 14px 16px; background: linear-gradient(to top, var(--bg-main) 80%, transparent); }
        #input-area { background: var(--bg-input); border: 1px solid var(--border); border-radius: 26px; padding: 6px 6px 6px 16px; display: flex; align-items: center; gap: 8px; transition: border-color 0.2s; }
        #input-area:focus-within { border-color: var(--accent); box-shadow: 0 0 15px rgba(56, 189, 248, 0.12); }
        input { flex: 1; background: transparent; border: none; color: #fff; font-size: 15px; outline: none; padding: 8px 0; }
        input::placeholder { color: #64748b; }
        button#send-btn { background: var(--accent); color: #090b10; border: none; width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; cursor: pointer; transition: transform 0.15s; flex-shrink: 0; }
        button#send-btn:active { transform: scale(0.9); }
        button#send-btn:disabled { background: #334155; color: #64748b; }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="logo-orb"></div>
            <h1>Bluro</h1>
        </div>
        <button class="new-chat-btn" onclick="resetChat()">+ New Chat</button>
    </header>

    <div id="chat-box">
        <div class="welcome" id="welcome-screen">
            <div class="welcome-orb"></div>
            <h2>Ask Bluro</h2>
            <p>Deep-space astrophysics, wildlife science & verified cosmic intelligence.</p>
            <div class="chips">
                <div class="chip" onclick="quickAsk('What happens inside the event horizon of Sagittarius A*?')">🌌 Inside Sagittarius A* black hole</div>
                <div class="chip" onclick="quickAsk('Why do solar winds strip away Venus atmosphere?')">🪐 How solar winds strip Venus</div>
                <div class="chip" onclick="quickAsk('How strong is a spotted hyena bite force compared to a lion?')">🦁 Spotted hyena vs lion bite force</div>
            </div>
        </div>
    </div>

    <div id="input-wrapper">
        <div id="input-area">
            <input type="text" id="user-input" placeholder="Ask anything about science..." autocomplete="off">
            <button id="send-btn" onclick="sendMessage()">➤</button>
        </div>
    </div>

    <script>
        const chatBox = document.getElementById('chat-box');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');

        userInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") sendMessage();
        });

        function quickAsk(question) {
            userInput.value = question;
            sendMessage();
        }

        function resetChat() {
            location.reload();
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;

            const welcome = document.getElementById('welcome-screen');
            if (welcome) welcome.style.display = 'none';

            appendMessage(text, 'user-msg');
            userInput.value = '';
            sendBtn.disabled = true;

            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'msg ai-msg';
            loadingDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
            chatBox.appendChild(loadingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: text })
                });
                const data = await res.json();
                loadingDiv.innerText = data.reply || data.error || 'No response received.';
            } catch (err) {
                loadingDiv.innerText = 'Network error. Please check your connection.';
            }
            sendBtn.disabled = false;
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function appendMessage(text, className) {
            const div = document.createElement('div');
            div.className = 'msg ' + className;
            div.innerText = text;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
            return div;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/ask', methods=['POST'])
def ask():
    if not client:
        return jsonify({'error': 'Server API Key not configured yet.'}), 500
    data = request.get_json()
    prompt = data.get('prompt', '')
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3
            )
        )
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
  
