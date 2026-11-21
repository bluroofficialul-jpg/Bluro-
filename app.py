import os, json, base64
from flask import Flask, request, jsonify, render_template_string, send_from_directory
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

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#0047CC">
<link rel="icon" type="image/png" href="/logo.png">
<link rel="apple-touch-icon" href="/logo.png">
<link rel="manifest" href="/manifest.json">
<title>BLURO</title>
<style>
:root{--bg:#050608;--surf:#0f1116;--card:#141720;--bdr:#222736;--txt:#f5f7fb;--mut:#8b93a7;--acc:#0047CC;--glow:rgba(0,71,204,0.22);--ubg:#181c28;--tile:#161a24}
[data-theme="light"]{--bg:#f4f7fc;--surf:#ffffff;--card:#ffffff;--bdr:#dbe3f0;--txt:#0b1220;--mut:#5c667d;--acc:#0047CC;--glow:rgba(0,71,204,0.12);--ubg:#eaf0ff;--tile:#f0f4fc}
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',Roboto,sans-serif;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--txt);height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#splash{position:fixed;inset:0;background:#0047CC;z-index:999;display:flex;align-items:center;justify-content:center;animation:splashOut 0.3s ease 0.7s forwards;pointer-events:none}
@keyframes splashOut{0%{opacity:1;visibility:visible}99%{opacity:0;visibility:visible}100%{opacity:0;visibility:hidden;display:none}}
.slogo{width:130px;height:130px;object-fit:contain}
header{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:var(--bg);border-bottom:1px solid var(--bdr);gap:8px}
.ibtn{background:var(--surf);border:1px solid var(--bdr);color:var(--txt);width:38px;height:38px;border-radius:12px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:17px;flex-shrink:0}
.mbtn{background:var(--surf);border:1px solid var(--bdr);color:var(--txt);padding:7px 13px;border-radius:12px;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:5px}
.tabs{display:flex;background:var(--surf);border:1px solid var(--bdr);border-radius:12px;padding:3px}
.tab{padding:5px 12px;border-radius:9px;font-size:12.5px;font-weight:600;color:var(--mut);cursor:pointer;border:none;background:transparent}
.tab.active{background:var(--acc);color:#fff}
main{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:14px}
.hero{margin:auto;width:100%;max-width:360px;padding:12px;display:flex;flex-direction:column;gap:10px}
.chip{background:var(--surf);border:1px solid var(--bdr);color:var(--txt);padding:13px 15px;border-radius:14px;font-size:13.5px;text-align:left;cursor:pointer;display:flex;align-items:center;gap:10px}
.u-wrap{align-self:flex-end;max-width:82%;display:flex;flex-direction:column;align-items:flex-end;gap:6px}
.u-img{max-width:210px;border-radius:14px;border:1px solid var(--bdr)}
.u-msg{background:var(--ubg);color:var(--txt);padding:11px 15px;border-radius:18px 18px 4px 18px;font-size:15px;line-height:1.45;word-wrap:break-word;border:1px solid var(--bdr)}
.ai-wrap{display:flex;flex-direction:column;gap:6px;max-width:94%}
.card{background:var(--card);border:1px solid var(--bdr);border-left:3px solid var(--acc);border-radius:16px;padding:15px;display:flex;flex-direction:column;gap:10px}
.brow{display:flex;align-items:center;justify-content:space-between}
.btag{font-size:11px;font-weight:800;letter-spacing:1px;color:#4d8dff}
.cbadge{font-size:11px;padding:3px 9px;border-radius:8px;background:var(--glow);color:#7aa8ff;font-weight:600;border:1px solid rgba(77,141,255,0.25)}
.dtxt{font-size:15px;line-height:1.58}
.etog{background:transparent;border:1px solid var(--bdr);color:var(--mut);padding:6px 11px;border-radius:9px;font-size:12px;cursor:pointer;align-self:flex-start}
.ebox{display:none;flex-direction:column;gap:8px;padding-top:8px;border-top:1px solid var(--bdr);font-size:13px;color:var(--mut)}
.ebox.open{display:flex}
.ebox ul{padding-left:18px;display:flex;flex-direction:column;gap:4px}
.srcs{font-size:12px;color:var(--txt)}
.actbar{display:flex;align-items:center;gap:6px;padding:2px 2px}
.abtn{background:var(--surf);border:1px solid var(--bdr);color:var(--mut);width:32px;height:32px;border-radius:9px;display:flex;align-items:center;justify-content:center;cursor:pointer}
.abtn.on{color:#4d8dff;border-color:#4d8dff;background:var(--glow)}
.thk{display:flex;align-items:center;gap:10px;padding:11px 15px;background:var(--surf);border:1px solid var(--bdr);border-radius:14px;align-self:flex-start}
.orb{width:11px;height:11px;border-radius:3px;background:var(--acc);animation:pulse 1.1s infinite}
@keyframes pulse{0%,100%{transform:rotate(0deg) scale(0.85);opacity:0.5}50%{transform:rotate(45deg) scale(1.15);opacity:1}}
footer{padding:8px 12px 14px;background:var(--bg)}
.composer{background:var(--surf);border:1px solid var(--bdr);border-radius:20px;padding:8px 10px;display:flex;flex-direction:column;gap:8px;box-shadow:0 4px 20px rgba(0,0,0,0.35)}
#prevWrap{display:none;padding:4px 4px 0}
.prevCard{position:relative;display:inline-block;border-radius:12px;overflow:hidden;border:1px solid var(--bdr);background:#000}
#prevImg{display:block;height:74px;width:auto;max-width:140px;object-fit:cover}
.prevClose{position:absolute;top:5px;right:5px;width:22px;height:22px;border-radius:7px;background:rgba(0,0,0,0.82);color:#fff;border:1px solid rgba(255,255,255,0.25);font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;cursor:pointer}
.ibox{display:flex;align-items:center;gap:6px}
.cbtn{width:36px;height:36px;border-radius:11px;border:none;background:transparent;color:#ffffff;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:21px;flex-shrink:0}
[data-theme="light"] .cbtn{color:#0b1220}
#qin{flex:1;background:transparent;border:none;outline:none;color:var(--txt);font-size:15.5px;padding:6px 4px}
#sbtn{width:36px;height:36px;border-radius:11px;border:none;background:var(--acc);color:#fff;font-size:16px;font-weight:700;cursor:pointer;flex-shrink:0;box-shadow:0 2px 10px var(--glow)}
.lib-grid{display:grid;grid-template-columns:1fr;gap:12px}
.lcard{background:var(--surf);border:1px solid var(--bdr);border-radius:14px;padding:15px;cursor:pointer}
.lcard h3{font-size:15.5px;margin-bottom:5px}
.lcard p{font-size:13px;color:var(--mut);line-height:1.4}
.drawer{position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:50;display:none}
.drawer.open{display:flex}
.dpanel{width:280px;background:var(--surf);height:100%;padding:16px;display:flex;flex-direction:column;gap:12px;border-right:1px solid var(--bdr)}
.citem{padding:10px;border-radius:11px;border:1px solid var(--bdr);font-size:13px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bsheet-bg{position:fixed;inset:0;background:rgba(2,4,10,0.72);backdrop-filter:blur(4px);z-index:60;display:none;align-items:flex-end}
.bsheet-bg.open{display:flex}
.bsheet{width:100%;background:var(--surf);border-top:1px solid rgba(77,141,255,0.3);border-radius:24px 24px 0 0;padding:12px 16px 26px;display:flex;flex-direction:column;gap:14px;box-shadow:0 -10px 35px rgba(0,71,204,0.18);animation:slideUp 0.2s ease}
@keyframes slideUp{from{transform:translateY(36px);opacity:0.4}to{transform:translateY(0);opacity:1}}
.bhead{display:flex;align-items:center;justify-content:space-between;padding:0 4px}
.btitle{font-size:11px;font-weight:800;letter-spacing:1.2px;color:#4d8dff;text-transform:uppercase}
.bhandle{width:34px;height:4px;border-radius:2px;background:var(--bdr)}
.btiles{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.btile{background:linear-gradient(145deg,var(--tile),rgba(0,71,204,0.08));border:1px solid var(--bdr);border-radius:16px;padding:18px 12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;color:var(--txt);cursor:pointer;font-size:13.5px;font-weight:600}
.btile-ico{width:40px;height:40px;border-radius:11px;background:var(--glow);border:1px solid rgba(77,141,255,0.3);color:#6ea3ff;display:flex;align-items:center;justify-content:center}
.blist{display:flex;flex-direction:column;gap:6px}
.brow-opt{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:13px;background:var(--tile);border:1px solid var(--bdr);color:var(--txt);text-align:left;cursor:pointer}
.brow-ico{width:34px;height:34px;border-radius:9px;background:rgba(255,255,255,0.04);color:#8faeff;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.brow-opt strong{display:block;font-size:14px;font-weight:600}
.brow-opt span{display:block;font-size:11.5px;color:var(--mut);margin-top:2px}
.mpop{position:fixed;top:58px;left:56px;background:var(--card);border:1px solid var(--bdr);border-radius:14px;padding:8px;display:none;flex-direction:column;gap:4px;z-index:40;width:215px;box-shadow:0 10px 25px rgba(0,0,0,0.5)}
.mpop.open{display:flex}
.pitem{padding:10px 14px;border:none;background:transparent;color:var(--txt);text-align:left;font-size:14px;border-radius:10px;cursor:pointer;display:flex;align-items:center;gap:10px}
#toast{position:fixed;bottom:84px;left:50%;transform:translateX(-50%);background:#1c2230;border:1px solid var(--bdr);color:#fff;padding:7px 14px;border-radius:10px;font-size:12.5px;opacity:0;pointer-events:none;transition:opacity 0.25s;z-index:80}
#toast.show{opacity:1}
</style>
</head>
<body>
<div id="splash"><img src="/logo.png" class="slogo" alt="BLURO"></div>
<div id="toast">Copied</div>
<header>
  <button type="button" class="ibtn" onclick="toggleDrawer()">☰</button>
  <button type="button" class="mbtn" onclick="toggleModelPop()"><span id="mLabel">Bluro 3.8</span> ⌄</button>
  <div class="tabs">
    <button type="button" class="tab active" id="tChat" onclick="switchTab('chat')">Chat</button>
    <button type="button" class="tab" id="tLib" onclick="switchTab('lib')">Science Library</button>
  </div>
  <button type="button" class="ibtn" onclick="newChat()">✎</button>
</header>
<div class="mpop" id="mPop">
  <button type="button" class="pitem" onclick="setModel('Bluro 3.8')"><div><strong>Bluro 3.8</strong><br><small style="color:var(--mut)">Fast science research engine</small></div></button>
  <button type="button" class="pitem" onclick="setModel('Bluro Pro')"><div><strong>Bluro Pro</strong><br><small style="color:var(--mut)">Deep astrophysics reasoning</small></div></button>
</div>
<main id="vChat">
  <div class="hero" id="hero">
    <div class="chip" onclick="qAsk('What happens inside a black hole event horizon?')">🌌 What happens inside a black hole event horizon?</div>
    <div class="chip" onclick="qAsk('How does James Webb Space Telescope detect exoplanet atmospheres?')">🔭 How does JWST detect exoplanet atmospheres?</div>
    <div class="chip" onclick="qAsk('How does quantum entanglement work without violating relativity?')">⚛️ Quantum entanglement & relativity</div>
  </div>
  <div id="feed" style="display:flex;flex-direction:column;gap:14px"></div>
</main>
<main id="vLib" style="display:none">
  <div class="lib-grid">
    <div class="lcard" onclick="qAsk('What happens inside a black hole event horizon according to general relativity?')"><h3>Black Holes & Event Horizons</h3><p>Spacetime curvature, Schwarzschild radius, and Hawking radiation.</p></div>
    <div class="lcard" onclick="qAsk('How does James Webb Space Telescope detect exoplanet atmospheres?')"><h3>JWST & Exoplanet Spectroscopy</h3><p>Transmission spectroscopy and biosignature molecules.</p></div>
    <div class="lcard" onclick="qAsk('What is the scientific evidence for dark matter and dark energy?')"><h3>Dark Matter & Dark Energy</h3><p>Galaxy rotation curves, gravitational lensing, and cosmic expansion.</p></div>
    <div class="lcard" onclick="qAsk('How does quantum entanglement work without violating relativity?')"><h3>Quantum Mechanics & Relativity</h3><p>Non-local correlations and the no-communication theorem.</p></div>
  </div>
</main>
<footer>
  <div class="composer">
    <div id="prevWrap"><div class="prevCard"><img id="prevImg" src="" alt="Preview"><button type="button" class="prevClose" onclick="clearImg()">✕</button></div></div>
    <div class="ibox">
      <button type="button" class="cbtn" onclick="togglePlus()">+</button>
      <input id="qin" placeholder="ask bluro" onkeydown="if(event.key==='Enter')send()">
      <button type="button" class="cbtn" onclick="startVoice()"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg></button>
      <button type="button" id="sbtn" onclick="sendOrStop()">↑</button>
    </div>
  </div>
</footer>
<div class="bsheet-bg" id="plusPop" onclick="if(event.target===this)togglePlus()">
  <div class="bsheet">
    <div class="bhead"><span class="btitle">BLURO INPUT LAB</span><div class="bhandle"></div><span style="width:70px"></span></div>
    <div class="btiles">
      <button type="button" class="btile" onclick="document.getElementById('galInp').click();togglePlus()">
        <div class="btile-ico"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="3"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg></div>
        <span>Photos</span>
      </button>
      <button type="button" class="btile" onclick="document.getElementById('camInp').click();togglePlus()">
        <div class="btile-ico"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg></div>
        <span>Camera</span>
      </button>
    </div>
    <div class="blist">
      <button type="button" class="brow-opt" onclick="togglePlus();document.getElementById('qin').value='Deep peer-reviewed analysis: ';document.getElementById('qin').focus()">
        <div class="brow-ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg></div>
        <div><strong>Deep Evidence Mode</strong><span>Peer-reviewed breakdown with citations</span></div>
      </button>
      <button type="button" class="brow-opt" onclick="togglePlus();document.getElementById('galInp').click()">
        <div class="brow-ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg></div>
        <div><strong>Specimen & Chart Scan</strong><span>Analyze sky photos, formulas, or lab graphs</span></div>
      </button>
    </div>
  </div>
</div>
<input type="file" id="galInp" accept="image/*" style="display:none" onchange="handleImg(this)">
<input type="file" id="camInp" accept="image/*" capture="environment" style="display:none" onchange="handleImg(this)">
<div class="drawer" id="drawer" onclick="if(event.target===this)toggleDrawer()">
  <div class="dpanel">
    <div style="display:flex;justify-content:space-between;align-items:center"><strong>BLURO</strong><button type="button" class="ibtn" onclick="toggleTheme()">◐</button></div>
    <button type="button" class="pitem" style="background:var(--acc);color:#fff;justify-content:center;font-weight:600" onclick="newChat();toggleDrawer()">+ New Research Chat</button>
    <div id="hList" style="display:flex;flex-direction:column;gap:8px;overflow-y:auto;flex:1"></div>
  </div>
</div>
<script>
var chats = [];
try { chats = JSON.parse(localStorage.getItem('b_chats') || '[]'); } catch (e) { chats = []; }
var cid = null, selImgB64 = '', selImgMime = 'image/jpeg', selDataUrl = '', ctrl = null, lastQ = '';

function toast(m) { var t = document.getElementById('toast'); t.textContent = m; t.classList.add('show'); setTimeout(function() { t.classList.remove('show'); }, 1800); }
function toggleDrawer() { document.getElementById('drawer').classList.toggle('open'); renderHist(); }
function togglePlus() { document.getElementById('plusPop').classList.toggle('open'); }
function toggleModelPop() { document.getElementById('mPop').classList.toggle('open'); }
function setModel(m) { document.getElementById('mLabel').textContent = m; document.getElementById('mPop').classList.remove('open'); }
function toggleTheme() { var t = document.body.getAttribute('data-theme') === 'light' ? 'dark' : 'light'; document.body.setAttribute('data-theme', t); try { localStorage.setItem('b_theme', t); } catch (e) {} }
try { if (localStorage.getItem('b_theme') === 'light') document.body.setAttribute('data-theme', 'light'); } catch (e) {}
function switchTab(t) { document.getElementById('vChat').style.display = t === 'chat' ? 'flex' : 'none'; document.getElementById('vLib').style.display = t === 'lib' ? 'block' : 'none'; document.getElementById('tChat').classList.toggle('active', t === 'chat'); document.getElementById('tLib').classList.toggle('active', t === 'lib'); }
function newChat() { cid = null; document.getElementById('feed').innerHTML = ''; document.getElementById('hero').style.display = 'flex'; clearImg(); switchTab('chat'); }
function renderHist() {
  var h = document.getElementById('hList'); h.innerHTML = '';
  chats.forEach(function(c) {
    var d = document.createElement('div'); d.className = 'citem'; d.textContent = c.t;
    d.onclick = function() { cid = c.id; document.getElementById('hero').style.display = 'none'; var f = document.getElementById('feed'); f.innerHTML = ''; c.m.forEach(function(x) { if (x.r === 'u') addU(x.t, x.img || ''); else addAI(x.d, x.q || ''); }); toggleDrawer(); switchTab('chat'); };
    h.appendChild(d);
  });
}
function handleImg(inp) { var f = inp.files[0]; if (!f) return; selImgMime = f.type || 'image/jpeg'; var r = new FileReader(); r.onload = function() { selDataUrl = r.result; selImgB64 = r.result.split(',')[1]; document.getElementById('prevImg').src = selDataUrl; document.getElementById('prevWrap').style.display = 'block'; }; r.readAsDataURL(f); }
function clearImg() { selImgB64 = ''; selDataUrl = ''; document.getElementById('prevWrap').style.display = 'none'; document.getElementById('prevImg').src = ''; document.getElementById('galInp').value = ''; document.getElementById('camInp').value = ''; }
function startVoice() { var SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (!SR) return alert('Voice not supported'); var rec = new SR(); rec.onresult = function(e) { document.getElementById('qin').value = e.results[0][0].transcript; send(); }; rec.start(); }
function qAsk(t) { switchTab('chat'); document.getElementById('qin').value = t; send(); }
function addU(t, imgUrl) { var w = document.createElement('div'); w.className = 'u-wrap'; if (imgUrl) { var im = document.createElement('img'); im.className = 'u-img'; im.src = imgUrl; w.appendChild(im); } if (t) { var d = document.createElement('div'); d.className = 'u-msg'; d.textContent = t; w.appendChild(d); } document.getElementById('feed').appendChild(w); }
function addAI(data, origQ) {
  var wrap = document.createElement('div'); wrap.className = 'ai-wrap';
  var c = document.createElement('div'); c.className = 'card';
  var id = 'e' + Math.random().toString(36).slice(2, 8);
  var ansTxt = data.direct_answer || data.error || 'No response';
  var evList = data.evidence || [], srList = data.sources || [];
  var ev = evList.map(function(x) { return '<li>' + x + '</li>'; }).join('');
  var sr = srList.join(' • ');
  var fullCopy = [ansTxt, evList.length ? '\nEvidence:\n- ' + evList.join('\n- ') : '', srList.length ? '\nSources: ' + sr : ''].join('');
  c.innerHTML = '<div class="brow"><span class="btag">BLURO</span><span class="cbadge">' + (data.confidence || 'Verified') + '</span></div><div class="dtxt">' + ansTxt + '</div>' + (ev ? '<button type="button" class="etog" onclick="document.getElementById(\'' + id + '\').classList.toggle(\'open\')">Evidence & Sources ⌄</button><div class="ebox" id="' + id + '"><ul>' + ev + '</ul><div class="srcs"><strong>Sources:</strong> ' + sr + '</div></div>' : '');
  var bar = document.createElement('div'); bar.className = 'actbar';
  var bLike = document.createElement('button'); bLike.type = 'button'; bLike.className = 'abtn'; bLike.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/></svg>'; bLike.onclick = function() { bLike.classList.toggle('on'); bDis.classList.remove('on'); toast('Feedback saved'); };
  var bDis = document.createElement('button'); bDis.type = 'button'; bDis.className = 'abtn'; bDis.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/></svg>'; bDis.onclick = function() { bDis.classList.toggle('on'); bLike.classList.remove('on'); toast('Feedback saved'); };
  var bReg = document.createElement('button'); bReg.type = 'button'; bReg.className = 'abtn'; bReg.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'; bReg.onclick = function() { if (origQ || lastQ) qAsk(origQ || lastQ); };
  var bShr = document.createElement('button'); bShr.type = 'button'; bShr.className = 'abtn'; bShr.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>'; bShr.onclick = function() { if (navigator.share) navigator.share({ title: 'BLURO', text: fullCopy }).catch(function(){}); else { navigator.clipboard.writeText(fullCopy); toast('Copied'); } };
  var bCpy = document.createElement('button'); bCpy.type = 'button'; bCpy.className = 'abtn'; bCpy.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>'; bCpy.onclick = function() { navigator.clipboard.writeText(fullCopy); toast('Copied'); };
  bar.append(bLike, bDis, bReg, bShr, bCpy); wrap.append(c, bar); document.getElementById('feed').appendChild(wrap);
}
function sendOrStop() { if (ctrl) { ctrl.abort(); ctrl = null; return; } send(); }
async function send() {
  var inp = document.getElementById('qin'), q = inp.value.trim();
  if (!q && !selImgB64) return;
  lastQ = q; var b64 = selImgB64, mime = selImgMime, imgUrl = selDataUrl;
  document.getElementById('hero').style.display = 'none'; addU(q, imgUrl);
  if (!cid) { cid = 'c' + Date.now(); chats.unshift({ id: cid, t: (q || 'Image').slice(0, 40), m: [] }); }
  var ac = chats.find(function(x) { return x.id === cid; }); ac.m.push({ r: 'u', t: q });
  try { localStorage.setItem('b_chats', JSON.stringify(chats)); } catch (e) {}
  clearImg(); inp.value = '';
  var sb = document.getElementById('sbtn'); sb.textContent = '■';
  var fd = document.getElementById('feed'), vc = document.getElementById('vChat');
  var th = document.createElement('div'); th.className = 'thk'; th.innerHTML = '<div class="orb"></div><span style="font-size:13px;color:var(--mut)">Researching evidence...</span>';
  fd.appendChild(th); vc.scrollTop = vc.scrollHeight;
  ctrl = new AbortController();
  try {
    var res = await fetch('/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q, image_base64: b64, image_mime: mime }), signal: ctrl.signal });
    var data = await res.json(); th.remove(); addAI(data, q);
    ac.m.push({ r: 'a', d: data, q: q });
    try { localStorage.setItem('b_chats', JSON.stringify(chats)); } catch (e) {}
  } catch (e) {
    th.remove();
    addAI({ direct_answer: e.name === 'AbortError' ? 'Generation stopped.' : 'Network timeout. Please try again.', evidence: [], sources: [], confidence: 'Info' }, q);
  }
  ctrl = null; sb.textContent = '↑'; vc.scrollTop = vc.scrollHeight;
}
</script>
</body>
</html>"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/logo.png")
def logo():
    return send_from_directory(".", "logo.png")

@app.route("/manifest.json")
def manifest():
    return jsonify({"name": "BLURO", "short_name": "BLURO", "start_url": "/", "display": "standalone", "background_color": "#0047CC", "theme_color": "#0047CC", "icons": [{"src": "/logo.png", "sizes": "512x512", "type": "image/png"}]})

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json() or {}
        q = (data.get("question") or "").strip()
        img_b64 = data.get("image_base64") or ""
        img_mime = data.get("image_mime") or "image/jpeg"
        if not q and not img_b64:
            return jsonify({"error": "Empty"}), 400
        api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
        if not api_key:
            return jsonify({"direct_answer": "Server configuration error: GEMINI_API_KEY is missing in Render Environment.", "evidence": [], "sources": [], "confidence": "Setup Needed"})
        prompt_text = q if q else "Analyze this image scientifically with evidence and sources."
        contents = [prompt_text]
        if img_b64:
            img_bytes = base64.b64decode(img_b64)
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type=img_mime))
             client = genai.Client(api_key=api_key, http_options={"timeout": 20000})
          
        cfg = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, response_mime_type="application/json", temperature=0.3)
        res = None
        last_err = ""
        for m in ["gemini-3.8-flash", "gemini-3.8-flash-lite", "gemini-3.8-flash"]:
            try:
                res = client.models.generate_content(model=m, contents=contents, config=cfg)
                if res and res.text:
                    break
            except Exception as me:
                last_err = str(me)
                continue
        if not res or not res.text:
            return jsonify({"direct_answer": f"Notice: {last_err}", "evidence": [], "sources": [], "confidence": "Notice"})
        raw = res.text.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json\n", "", 1).strip()
        return jsonify(json.loads(raw))
    except Exception as e:
        return jsonify({"direct_answer": f"API Notice: {str(e)}", "evidence": [], "sources": [], "confidence": "Notice"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
  
