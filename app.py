import os, json, base64
from flask import Flask, request, jsonify, render_template_string, Response
from google import genai
from google.genai import types

app = Flask(__name__)

SYSTEM_PROMPT = """You are BLURO, an objective AI science research assistant.
Answer scientific questions with direct evidence, verified sources, and clear confidence metrics.
Never mention Gemini, Google, or any underlying AI provider. You are strictly BLURO.
Always respond in valid JSON with this exact schema:
{
  "direct_answer": "Clear, rigorous, evidence-based scientific answer",
  "evidence": ["Key scientific evidence point 1", "Key scientific evidence point 2"],
  "sources": ["Peer-reviewed journal, mission, or institution 1", "Source 2"],
  "confidence": "High (Peer-Reviewed Consensus)"
}"""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="115" fill="#0052FF"/>
  <circle cx="256" cy="256" r="130" fill="none" stroke="#ffffff" stroke-width="32"/>
  <circle cx="256" cy="256" r="44" fill="#ffffff"/>
</svg>"""

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#08080a">
<link rel="manifest" href="/manifest.json">
<title>BLURO</title>
<style>
:root{--bg:#08080a;--card:#121318;--bdr:#22242c;--txt:#f3f4f6;--mut:#9ca3af;--acc:#0052FF;--ubg:#0052FF;--utxt:#ffffff}
[data-theme="light"]{--bg:#f8fafc;--card:#ffffff;--bdr:#e2e8f0;--txt:#0f172a;--mut:#64748b;--acc:#0052FF;--ubg:#0052FF;--utxt:#ffffff}
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
body{background:var(--bg);color:var(--txt);height:100dvh;display:flex;flex-direction:column;overflow:hidden}
header{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-bottom:1px solid var(--bdr);gap:8px}
.ibtn{background:var(--card);border:1px solid var(--bdr);color:var(--txt);width:38px;height:38px;border-radius:12px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:18px;flex-shrink:0}
.mbtn{background:var(--card);border:1px solid var(--bdr);color:var(--txt);padding:7px 12px;border-radius:14px;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:5px}
.tabs{display:flex;background:var(--card);border:1px solid var(--bdr);border-radius:14px;padding:3px}
.tab{padding:6px 13px;border-radius:11px;font-size:13px;font-weight:600;color:var(--mut);cursor:pointer;border:none;background:transparent}
.tab.active{background:var(--bdr);color:var(--txt)}
main{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:14px}
.hero{margin:auto;text-align:center;max-width:340px;padding:20px}
.hero h1{font-size:26px;font-weight:700;margin-bottom:8px;letter-spacing:-0.5px}
.hero p{font-size:14px;color:var(--mut);line-height:1.5}
.u-msg{align-self:flex-end;background:var(--ubg);color:var(--utxt);padding:11px 15px;border-radius:18px 18px 4px 18px;max-width:82%;font-size:15px;line-height:1.45;word-wrap:break-word}
.card{background:var(--card);border:1px solid var(--bdr);border-radius:18px;padding:15px;max-width:92%;display:flex;flex-direction:column;gap:10px}
.brow{display:flex;align-items:center;justify-content:space-between}
.btag{font-size:11px;font-weight:800;letter-spacing:0.8px;color:#3b82f6}
.cbadge{font-size:11px;padding:3px 9px;border-radius:99px;background:rgba(59,130,246,0.15);color:#60a5fa;font-weight:600}
.dtxt{font-size:15px;line-height:1.55}
.etog{background:transparent;border:1px solid var(--bdr);color:var(--mut);padding:6px 10px;border-radius:10px;font-size:12px;cursor:pointer;align-self:flex-start}
.ebox{display:none;flex-direction:column;gap:8px;padding-top:8px;border-top:1px solid var(--bdr);font-size:13px;color:var(--mut)}
.ebox.open{display:flex}
.ebox ul{padding-left:18px;display:flex;flex-direction:column;gap:4px}
.srcs{font-size:12px;color:var(--txt)}
.thk{display:flex;align-items:center;gap:10px;padding:12px 15px;background:var(--card);border:1px solid var(--bdr);border-radius:16px;align-self:flex-start}
.orb{width:12px;height:12px;border-radius:50%;background:var(--acc);animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{transform:scale(0.8);opacity:0.5}50%{transform:scale(1.2);opacity:1}}
footer{padding:10px 14px 14px;background:var(--bg);border-top:1px solid var(--bdr)}
.ibox{display:flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--bdr);border-radius:24px;padding:6px 8px}
.cbtn{width:34px;height:34px;border-radius:50%;border:none;background:transparent;color:#ffffff;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:20px;flex-shrink:0}
[data-theme="light"] .cbtn{color:#0f172a}
#qin{flex:1;background:transparent;border:none;outline:none;color:var(--txt);font-size:15px;padding:6px 4px}
#sbtn{width:36px;height:36px;border-radius:50%;border:none;background:var(--acc);color:#fff;font-size:16px;font-weight:700;cursor:pointer;flex-shrink:0}
.lib-grid{display:grid;grid-template-columns:1fr;gap:12px}
.lcard{background:var(--card);border:1px solid var(--bdr);border-radius:16px;padding:15px;cursor:pointer}
.lcard h3{font-size:16px;margin-bottom:5px}
.lcard p{font-size:13px;color:var(--mut);line-height:1.4}
.drawer{position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:50;display:none}
.drawer.open{display:flex}
.dpanel{width:280px;background:var(--card);height:100%;padding:16px;display:flex;flex-direction:column;gap:12px;border-right:1px solid var(--bdr)}
.citem{padding:10px;border-radius:10px;border:1px solid var(--bdr);font-size:13px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pop{position:fixed;bottom:72px;left:16px;background:var(--card);border:1px solid var(--bdr);border-radius:14px;padding:6px;display:none;flex-direction:column;gap:4px;z-index:40}
.pop.open{display:flex}
.pitem{padding:9px 14px;border:none;background:transparent;color:var(--txt);text-align:left;font-size:14px;border-radius:10px;cursor:pointer}
.mpop{position:fixed;top:58px;left:56px;background:var(--card);border:1px solid var(--bdr);border-radius:14px;padding:8px;display:none;flex-direction:column;gap:4px;z-index:40;width:210px}
.mpop.open{display:flex}
#imgTag{font-size:12px;color:#60a5fa;padding:0 12px 6px;display:none}
</style>
</head>
<body>
<header>
  <button class="ibtn" onclick="toggleDrawer()">☰</button>
  <button class="mbtn" onclick="toggleModelPop()"><span id="mLabel">Bluro 3.8</span> ⌄</button>
  <div class="tabs">
    <button class="tab active" id="tChat" onclick="switchTab('chat')">Chat</button>
    <button class="tab" id="tLib" onclick="switchTab('lib')">Science Library</button>
  </div>
  <button class="ibtn" onclick="newChat()">✎</button>
</header>

<div class="mpop" id="mPop">
  <button class="pitem" onclick="setModel('Bluro 3.8')"><strong>Bluro 3.8</strong><br><small style="color:var(--mut)">High-speed science engine</small></button>
  <button class="pitem" onclick="setModel('Bluro Pro')"><strong>Bluro Pro</strong><br><small style="color:var(--mut)">Deep astrophysics reasoning</small></button>
</div>

<main id="vChat">
  <div class="hero" id="hero">
    <h1>Ask BLURO</h1>
    <p>Evidence-backed answers in astrophysics, cosmology, biology, and physics.</p>
  </div>
  <div id="feed" style="display:flex;flex-direction:column;gap:14px"></div>
</main>

<main id="vLib" style="display:none">
  <div class="lib-grid">
    <div class="lcard" onclick="qAsk('What happens inside a black hole event horizon according to general relativity?')">
      <h3>Black Holes & Event Horizons</h3>
      <p>Spacetime curvature, Schwarzschild radius, and Hawking radiation.</p>
    </div>
    <div class="lcard" onclick="qAsk('How does James Webb Space Telescope detect exoplanet atmospheres?')">
      <h3>JWST & Exoplanet Spectroscopy</h3>
      <p>Transmission spectroscopy and biosignature molecules.</p>
    </div>
    <div class="lcard" onclick="qAsk('What is the scientific evidence for dark matter and dark energy?')">
      <h3>Dark Matter & Dark Energy</h3>
      <p>Galaxy rotation curves, gravitational lensing, and cosmic expansion.</p>
    </div>
    <div class="lcard" onclick="qAsk('How does quantum entanglement work without violating relativity?')">
      <h3>Quantum Mechanics & Relativity</h3>
      <p>Non-local correlations and the no-communication theorem.</p>
    </div>
  </div>
</main>

<div id="imgTag">Image attached</div>
<footer>
  <div class="ibox">
    <button class="cbtn" onclick="togglePlus()">+</button>
    <input id="qin" placeholder="ask bluro" onkeydown="if(event.key==='Enter')send()">
    <button class="cbtn" onclick="startVoice()">
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
    </button>
    <button id="sbtn" onclick="sendOrStop()">↑</button>
  </div>
</footer>

<div class="pop" id="plusPop">
  <button class="pitem" onclick="document.getElementById('galInp').click();togglePlus()">Photos</button>
  <button class="pitem" onclick="document.getElementById('camInp').click();togglePlus()">Camera</button>
</div>
<input type="file" id="galInp" accept="image/*" style="display:none" onchange="handleImg(this)">
<input type="file" id="camInp" accept="image/*" capture="environment" style="display:none" onchange="handleImg(this)">

<div class="drawer" id="drawer" onclick="if(event.target===this)toggleDrawer()">
  <div class="dpanel">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <strong>BLURO History</strong>
      <button class="ibtn" onclick="toggleTheme()">◐</button>
    </div>
    <button class="pitem" style="background:var(--acc);color:#fff;text-align:center;font-weight:600" onclick="newChat();toggleDrawer()">+ New Research Chat</button>
    <div id="hList" style="display:flex;flex-direction:column;gap:8px;overflow-y:auto;flex:1"></div>
  </div>
</div>

<script>
let chats=JSON.parse(localStorage.getItem('b_chats')||'[]'),cid=null,selImgB64='',selImgMime='image/jpeg',ctrl=null;
function toggleDrawer(){const d=document.getElementById('drawer');d.classList.toggle('open');renderHist();}
function togglePlus(){document.getElementById('plusPop').classList.toggle('open');}
function toggleModelPop(){document.getElementById('mPop').classList.toggle('open');}
function setModel(m){document.getElementById('mLabel').textContent=m;toggleModelPop();}
function toggleTheme(){const t=document.body.getAttribute('data-theme')==='light'?'dark':'light';document.body.setAttribute('data-theme',t);localStorage.setItem('b_theme',t);}
if(localStorage.getItem('b_theme')==='light')document.body.setAttribute('data-theme','light');

function switchTab(t){
  document.getElementById('vChat').style.display=t==='chat'?'flex':'none';
  document.getElementById('vLib').style.display=t==='lib'?'block':'none';
  document.getElementById('tChat').classList.toggle('active',t==='chat');
  document.getElementById('tLib').classList.toggle('active',t==='lib');
}

function newChat(){
  cid=null;document.getElementById('feed').innerHTML='';document.getElementById('hero').style.display='block';switchTab('chat');
}

function renderHist(){
  const h=document.getElementById('hList');h.innerHTML='';
  chats.forEach(c=>{
    const d=document.createElement('div');d.className='citem';d.textContent=c.t;
    d.onclick=()=>{cid=c.id;document.getElementById('hero').style.display='none';const f=document.getElementById('feed');f.innerHTML='';c.m.forEach(x=>x.r==='u'?addU(x.t):addAI(x.d));toggleDrawer();switchTab('chat');};
    h.appendChild(d);
  });
}

function handleImg(inp){
  const f=inp.files[0];if(!f)return;selImgMime=f.type||'image/jpeg';
  const r=new FileReader();r.onload=()=>{selImgB64=r.result.split(',')[1];const tag=document.getElementById('imgTag');tag.style.display='block';tag.textContent='Attached: '+f.name;};r.readAsDataURL(f);
}

function startVoice(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR)return alert('Voice not supported on this browser');
  const rec=new SR();rec.onresult=e=>{document.getElementById('qin').value=e.results[0][0].transcript;send();};rec.start();
}

function qAsk(t){switchTab('chat');document.getElementById('qin').value=t;send();}
function addU(t){const d=document.createElement('div');d.className='u-msg';d.textContent=t;document.getElementById('feed').appendChild(d);}
function addAI(data){
  const c=document.createElement('div');c.className='card';
  const id='e'+Math.random().toString(36).slice(2,8);
  const ev=(data.evidence||[]).map(x=>`<li>${x}</li>`).join('');
  const sr=(data.sources||[]).join(' • ');
  c.innerHTML=`<div class="brow"><span class="btag">BLURO</span><span class="cbadge">${data.confidence||'Verified'}</span></div>
  <div class="dtxt">${data.direct_answer||data.error||'No response'}</div>
  ${ev?`<button class="etog" onclick="document.getElementById('${id}').classList.toggle('open')">Evidence & Sources ⌄</button>
  <div class="ebox" id="${id}"><ul>${ev}</ul><div class="srcs"><strong>Sources:</strong> ${sr}</div></div>`:''}`;
  document.getElementById('feed').appendChild(c);
}

function sendOrStop(){if(ctrl){ctrl.abort();ctrl=null;return;}send();}
async function send(){
  const inp=document.getElementById('qin'),q=inp.value.trim();
  if(!q&&!selImgB64)return;
  const userTxt=q||(selImgB64?'[Image uploaded]':'');
  document.getElementById('hero').style.display='none';addU(userTxt);
  if(!cid){cid='c'+Date.now();chats.unshift({id:cid,t:userTxt.slice(0,40),m:[]});}
  const ac=chats.find(x=>x.id===cid);ac.m.push({r:'u',t:userTxt});localStorage.setItem('b_chats',JSON.stringify(chats));
  const b64=selImgB64,mime=selImgMime;
  selImgB64='';document.getElementById('imgTag').style.display='none';document.getElementById('galInp').value='';document.getElementById('camInp').value='';
  inp.value='';const sb=document.getElementById('sbtn');sb.textContent='■';
  const fd=document.getElementById('feed'),vc=document.getElementById('vChat');
  const th=document.createElement('div');th.className='thk';
  th.innerHTML='<div class="orb"></div><span style="font-size:13px;color:var(--mut)">Researching evidence...</span>';
  fd.appendChild(th);vc.scrollTop=vc.scrollHeight;
  ctrl=new AbortController();
  try{
    const res=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,image_base64:b64,image_mime:mime}),signal:ctrl.signal});
    const data=await res.json();th.remove();addAI(data);ac.m.push({r:'a',d:data});localStorage.setItem('b_chats',JSON.stringify(chats));
  }catch(e){th.remove();addAI({direct_answer:e.name==='AbortError'?'Generation stopped.':'Connection error.',evidence:[],sources:[],confidence:'Info'});}
  ctrl=null;sb.textContent='↑';vc.scrollTop=vc.scrollHeight;
}
</script>
</body>
</html>"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/icon.svg")
def icon():
    return Response(ICON_SVG, mimetype="image/svg+xml")

@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "BLURO",
        "short_name": "BLURO",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#08080a",
        "theme_color": "#0052FF",
        "icons": [{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"}]
    })

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json() or {}
    q = (data.get("question") or "").strip()
    img_b64 = data.get("image_base64") or ""
    img_mime = data.get("image_mime") or "image/jpeg"
    if not q and not img_b64:
        return jsonify({"error": "Empty"}), 400
    prompt_text = q if q else "Analyze this image scientifically with evidence and sources."
    contents = [prompt_text]
    if img_b64:
        img_bytes = base64.b64decode(img_b64)
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type=img_mime))
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    cfg = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.3
    )
    res = client.models.generate_content(model="gemini-3.8-flash", contents=contents, config=cfg)
    return jsonify(json.loads(res.text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
                   
