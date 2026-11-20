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
  <rect width="512" height="512" rx="112" fill="#0047CC"/>
  <path d="M172 120h108c54 0 92 32 92 78 0 36-22 62-56 72 44 10 72 42 72 86 0 56-44 92-108 92H172c-12 0-20-8-20-20V256c32 34 86 52 148 52 34 0 58 14 58 38 0 26-22 42-56 42h-86V312c-26-8-46-22-64-42v122h-20V140c0-12 8-20 20-20zm44 56v66c24 22 64 34 108 34 26 0 44-14 44-36 0-24-20-40-52-40h-100v-24z" fill="#ffffff"/>
</svg>"""

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#000000">
<link rel="icon" type="image/svg+xml" href="/icon.svg">
<link rel="apple-touch-icon" href="/icon.svg">
<link rel="manifest" href="/manifest.json">
<title>BLURO</title>
<style>
:root{--bg:#000000;--surf:#121316;--card:#18191e;--bdr:#262830;--txt:#f5f6f8;--mut:#8e929f;--acc:#0047CC;--ubg:#1f2128}
[data-theme="light"]{--bg:#f8fafc;--surf:#ffffff;--card:#ffffff;--bdr:#e2e8f0;--txt:#0f172a;--mut:#64748b;--acc:#0047CC;--ubg:#eef2ff}
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',Roboto,sans-serif;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--txt);height:100dvh;display:flex;flex-direction:column;overflow:hidden}

#splash{position:fixed;inset:0;background:#000000;z-index:100;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;transition:opacity 0.45s ease,visibility 0.45s}
#splash.hide{opacity:0;visibility:hidden}
.slogo{width:76px;height:76px;border-radius:20px;box-shadow:0 12px 36px rgba(0,71,204,0.45);animation:popIn 0.6s cubic-bezier(0.16,1,0.3,1)}
@keyframes popIn{0%{transform:scale(0.82);opacity:0}100%{transform:scale(1);opacity:1}}

header{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:var(--bg);border-bottom:1px solid var(--bdr);gap:8px}
.ibtn{background:var(--surf);border:1px solid var(--bdr);color:var(--txt);width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:17px;flex-shrink:0}
.mbtn{background:var(--surf);border:1px solid var(--bdr);color:var(--txt);padding:7px 13px;border-radius:20px;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:5px}
.tabs{display:flex;background:var(--surf);border:1px solid var(--bdr);border-radius:20px;padding:3px}
.tab{padding:5px 12px;border-radius:16px;font-size:12.5px;font-weight:600;color:var(--mut);cursor:pointer;border:none;background:transparent}
.tab.active{background:var(--bdr);color:var(--txt)}

main{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:14px}
.hero{margin:auto;text-align:center;max-width:340px;padding:16px;display:flex;flex-direction:column;align-items:center;gap:12px}
.hero img{width:54px;height:54px;border-radius:15px}
.hero h1{font-size:24px;font-weight:700;letter-spacing:-0.4px}
.hero p{font-size:13.5px;color:var(--mut);line-height:1.5}
.chips{display:flex;flex-direction:column;gap:8px;width:100%;margin-top:6px}
.chip{background:var(--surf);border:1px solid var(--bdr);color:var(--txt);padding:11px 14px;border-radius:14px;font-size:13px;text-align:left;cursor:pointer;display:flex;align-items:center;gap:10px}

.u-wrap{align-self:flex-end;max-width:82%;display:flex;flex-direction:column;align-items:flex-end;gap:6px}
.u-img{max-width:210px;border-radius:14px;border:1px solid var(--bdr)}
.u-msg{background:var(--ubg);color:var(--txt);padding:11px 15px;border-radius:20px 20px 4px 20px;font-size:15px;line-height:1.45;word-wrap:break-word;border:1px solid var(--bdr)}

.ai-wrap{display:flex;flex-direction:column;gap:6px;max-width:94%}
.card{background:var(--card);border:1px solid var(--bdr);border-radius:18px;padding:15px;display:flex;flex-direction:column;gap:10px}
.brow{display:flex;align-items:center;justify-content:space-between}
.btag{font-size:11px;font-weight:800;letter-spacing:0.8px;color:#3b82f6;display:flex;align-items:center;gap:6px}
.cbadge{font-size:11px;padding:3px 9px;border-radius:99px;background:rgba(0,71,204,0.18);color:#60a5fa;font-weight:600}
.dtxt{font-size:15px;line-height:1.58}
.etog{background:transparent;border:1px solid var(--bdr);color:var(--mut);padding:6px 11px;border-radius:10px;font-size:12px;cursor:pointer;align-self:flex-start}
.ebox{display:none;flex-direction:column;gap:8px;padding-top:8px;border-top:1px solid var(--bdr);font-size:13px;color:var(--mut)}
.ebox.open{display:flex}
.ebox ul{padding-left:18px;display:flex;flex-direction:column;gap:4px}
.srcs{font-size:12px;color:var(--txt)}

.actbar{display:flex;align-items:center;gap:4px;padding:2px 4px}
.abtn{background:transparent;border:none;color:var(--mut);width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:background 0.15s,color 0.15s}
.abtn:active,.abtn.on{color:#60a5fa;background:rgba(96,165,250,0.12)}

.thk{display:flex;align-items:center;gap:10px;padding:11px 15px;background:var(--surf);border:1px solid var(--bdr);border-radius:18px;align-self:flex-start}
.orb{width:11px;height:11px;border-radius:50%;background:var(--acc);animation:pulse 1.1s infinite}
@keyframes pulse{0%,100%{transform:scale(0.8);opacity:0.5}50%{transform:scale(1.25);opacity:1}}

footer{padding:8px 12px 14px;background:var(--bg)}
.composer{background:var(--surf);border:1px solid var(--bdr);border-radius:26px;padding:8px 10px;display:flex;flex-direction:column;gap:8px}
#prevWrap{display:none;padding:4px 4px 0}
.prevCard{position:relative;display:inline-block;border-radius:14px;overflow:hidden;border:1px solid var(--bdr);background:#000}
#prevImg{display:block;height:74px;width:auto;max-width:140px;object-fit:cover}
.prevClose{position:absolute;top:5px;right:5px;width:22px;height:22px;border-radius:50%;background:rgba(0,0,0,0.78);color:#fff;border:1px solid rgba(255,255,255,0.25);font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;cursor:pointer}

.ibox{display:flex;align-items:center;gap:6px}
.cbtn{width:36px;height:36px;border-radius:50%;border:none;background:transparent;color:#ffffff;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:21px;flex-shrink:0}
[data-theme="light"] .cbtn{color:#0f172a}
#qin{flex:1;background:transparent;border:none;outline:none;color:var(--txt);font-size:15.5px;padding:6px 4px}
#sbtn{width:36px;height:36px;border-radius:50%;border:none;background:var(--acc);color:#fff;font-size:16px;font-weight:700;cursor:pointer;flex-shrink:0}

.lib-grid{display:grid;grid-template-columns:1fr;gap:12px}
.lcard{background:var(--surf);border:1px solid var(--bdr);border-radius:16px;padding:15px;cursor:pointer}
.lcard h3{font-size:15.5px;margin-bottom:5px}
.lcard p{font-size:13px;color:var(--mut);line-height:1.4}

.drawer{position:fixed;inset:0;background:rgba(0,0,0,0.65);z-index:50;display:none}
.drawer.open{display:flex}
.dpanel{width:280px;background:var(--surf);height:100%;padding:16px;display:flex;flex-direction:column;gap:12px;border-right:1px solid var(--bdr)}
.citem{padding:10px;border-radius:12px;border:1px solid var(--bdr);font-size:13px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

.pop{position:fixed;bottom:76px;left:16px;background:var(--card);border:1px solid var(--bdr);border-radius:16px;padding:6px;display:none;flex-direction:column;gap:4px;z-index:40;box-shadow:0 10px 25px rgba(0,0,0,0.5)}
.pop.open{display:flex}
.pitem{padding:10px 14px;border:none;background:transparent;color:var(--txt);text-align:left;font-size:14px;border-radius:11px;cursor:pointer;display:flex;align-items:center;gap:10px}
.mpop{position:fixed;top:58px;left:56px;background:var(--card);border:1px solid var(--bdr);border-radius:16px;padding:8px;display:none;flex-direction:column;gap:4px;z-index:40;width:215px;box-shadow:0 10px 25px rgba(0,0,0,0.5)}
.mpop.open{display:flex}
#toast{position:fixed;bottom:84px;left:50%;transform:translateX(-50%);background:#262830;color:#fff;padding:7px 14px;border-radius:99px;font-size:12.5px;opacity:0;pointer-events:none;transition:opacity 0.25s;z-index:80}
#toast.show{opacity:1}
</style>
</head>
<body>

<div id="splash">
  <img src="/icon.svg" class="slogo" alt="BLURO">
</div>
<div id="toast">Copied</div>

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
  <button class="pitem" onclick="setModel('Bluro 3.8')"><div><strong>Bluro 3.8</strong><br><small style="color:var(--mut)">Fast science research engine</small></div></button>
  <button class="pitem" onclick="setModel('Bluro Pro')"><div><strong>Bluro Pro</strong><br><small style="color:var(--mut)">Deep astrophysics reasoning</small></div></button>
</div>

<main id="vChat">
  <div class="hero" id="hero">
    <img src="/icon.svg" alt="BLURO">
    <h1>Ask BLURO</h1>
    <p>Evidence-backed research assistant for astrophysics, cosmology, and science.</p>
    <div class="chips">
      <div class="chip" onclick="qAsk('What happens inside a black hole event horizon?')">🌌 What happens inside a black hole event horizon?</div>
      <div class="chip" onclick="qAsk('How does James Webb Space Telescope detect exoplanet atmospheres?')">🔭 How does JWST detect exoplanet atmospheres?</div>
      <div class="chip" onclick="qAsk('How does quantum entanglement work without violating relativity?')">⚛️ Quantum entanglement & relativity</div>
    </div>
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

<footer>
  <div class="composer">
    <div id="prevWrap">
      <div class="prevCard">
        <img id="prevImg" src="" alt="Preview">
        <button class="prevClose" onclick="clearImg()">✕</button>
      </div>
    </div>
    <div class="ibox">
      <button class="cbtn" onclick="togglePlus()">+</button>
      <input id="qin" placeholder="ask bluro" onkeydown="if(event.key==='Enter')send()">
      <button class="cbtn" onclick="startVoice()">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
      </button>
      <button id="sbtn" onclick="sendOrStop()">↑</button>
    </div>
  </div>
</footer>

<div class="pop" id="plusPop">
  <button class="pitem" onclick="document.getElementById('galInp').click();togglePlus()">🖼️ Photos & Gallery</button>
  <button class="pitem" onclick="document.getElementById('camInp').click();togglePlus()">📷 Take Photo</button>
</div>
<input type="file" id="galInp" accept="image/*" style="display:none" onchange="handleImg(this)">
<input type="file" id="camInp" accept="image/*" capture="environment" style="display:none" onchange="handleImg(this)">

<div class="drawer" id="drawer" onclick="if(event.target===this)toggleDrawer()">
  <div class="dpanel">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div style="display:flex;align-items:center;gap:8px"><img src="/icon.svg" style="width:24px;height:24px;border-radius:6px"><strong>BLURO</strong></div>
      <button class="ibtn" onclick="toggleTheme()">◐</button>
    </div>
    <button class="pitem" style="background:var(--acc);color:#fff;justify-content:center;font-weight:600" onclick="newChat();toggleDrawer()">+ New Research Chat</button>
    <div id="hList" style="display:flex;flex-direction:column;gap:8px;overflow-y:auto;flex:1"></div>
  </div>
</div>

<script>
window.addEventListener('load',()=>{setTimeout(()=>{document.getElementById('splash').classList.add('hide');},650);});
let chats=JSON.parse(localStorage.getItem('b_chats')||'[]'),cid=null,selImgB64='',selImgMime='image/jpeg',selDataUrl='',ctrl=null,lastQ='';
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),1800);}
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
  cid=null;document.getElementById('feed').innerHTML='';document.getElementById('hero').style.display='flex';clearImg();switchTab('chat');
}
function renderHist(){
  const h=document.getElementById('hList');h.innerHTML='';
  chats.forEach(c=>{
    const d=document.createElement('div');d.className='citem';d.textContent=c.t;
    d.onclick=()=>{cid=c.id;document.getElementById('hero').style.display='none';const f=document.getElementById('feed');f.innerHTML='';c.m.forEach(x=>x.r==='u'?addU(x.t,x.img||''):addAI(x.d,x.q||''));toggleDrawer();switchTab('chat');};
    h.appendChild(d);
  });
}

function handleImg(inp){
  const f=inp.files[0];if(!f)return;selImgMime=f.type||'image/jpeg';
  const r=new FileReader();
  r.onload=()=>{
    selDataUrl=r.result;
    selImgB64=r.result.split(',')[1];
    document.getElementById('prevImg').src=selDataUrl;
    document.getElementById('prevWrap').style.display='block';
  };
  r.readAsDataURL(f);
}

function clearImg(){
  selImgB64='';selDataUrl='';
  document.getElementById('prevWrap').style.display='none';
  document.getElementById('prevImg').src='';
  document.getElementById('galInp').value='';
  document.getElementById('camInp').value='';
}

function startVoice(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR)return alert('Voice not supported on this browser');
  const rec=new SR();rec.onresult=e=>{document.getElementById('qin').value=e.results[0][0].transcript;send();};rec.start();
}

function qAsk(t){switchTab('chat');document.getElementById('qin').value=t;send();}
function addU(t,imgUrl){
  const w=document.createElement('div');w.className='u-wrap';
  if(imgUrl){const im=document.createElement('img');im.className='u-img';im.src=imgUrl;w.appendChild(im);}
  if(t){const d=document.createElement('div');d.className='u-msg';d.textContent=t;w.appendChild(d);}
  document.getElementById('feed').appendChild(w);
}

function copyResp(btn,txt){
  navigator.clipboard.writeText(txt);
  btn.classList.add('on');
  toast('Copied to clipboard');
  setTimeout(()=>btn.classList.remove('on'),1500);
}

function shareResp(txt){
  if(navigator.share){navigator.share({title:'BLURO Research',text:txt}).catch(()=>{});}
  else{navigator.clipboard.writeText(txt);toast('Copied to share');}
}

function addAI(data,origQ){
  const wrap=document.createElement('div');wrap.className='ai-wrap';
  const c=document.createElement('div');c.className='card';
  const id='e'+Math.random().toString(36).slice(2,8);
  const ansTxt=data.direct_answer||data.error||'No response';
  const evList=data.evidence||[];
  const srList=data.sources||[];
  const ev=evList.map(x=>`<li>${x}</li>`).join('');
  const sr=srList.join(' • ');
  const fullCopy=[ansTxt,evList.length?'\nEvidence:\n- '+evList.join('\n- '):'',srList.length?'\nSources: '+sr:''].join('');

  c.innerHTML=`<div class="brow"><span class="btag"><img src="/icon.svg" style="width:15px;height:15px;border-radius:4px">BLURO</span><span class="cbadge">${data.confidence||'Verified'}</span></div>
  <div class="dtxt">${ansTxt}</div>
  ${ev?`<button class="etog" onclick="document.getElementById('${id}').classList.toggle('open')">Evidence & Sources ⌄</button>
  <div class="ebox" id="${id}"><ul>${ev}</ul><div class="srcs"><strong>Sources:</strong> ${sr}</div></div>`:''}`;

  const bar=document.createElement('div');bar.className='actbar';
  const bLike=document.createElement('button');bLike.className='abtn';bLike.title='Good response';
  bLike.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/></svg>';
  bLike.onclick=()=>{bLike.classList.toggle('on');bDis.classList.remove('on');toast('Feedback saved');};

  const bDis=document.createElement('button');bDis.className='abtn';bDis.title='Bad response';
  bDis.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/></svg>';
  bDis.onclick=()=>{bDis.classList.toggle('on');bLike.classList.remove('on');toast('Feedback saved');};

  const bReg=document.createElement('button');bReg.className='abtn';bReg.title='Regenerate';
  bReg.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>';
  bReg.onclick=()=>{if(origQ||lastQ){qAsk(origQ||lastQ);}};

  const bShr=document.createElement('button');bShr.className='abtn';bShr.title='Share';
  bShr.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>';
  bShr.onclick=()=>shareResp(fullCopy);

  const bCpy=document.createElement('button');bCpy.className='abtn';bCpy.title='Copy';
  bCpy.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>';
  bCpy.onclick=()=>copyResp(bCpy,fullCopy);

  bar.append(bLike,bDis,bReg,bShr,bCpy);
  wrap.append(c,bar);
  document.getElementById('feed').appendChild(wrap);
}

function sendOrStop(){if(ctrl){ctrl.abort();ctrl=null;return;}send();}
async function send(){
  const inp=document.getElementById('qin'),q=inp.value.trim();
  if(!q&&!selImgB64)return;
  lastQ=q;
  const b64=selImgB64,mime=selImgMime,imgUrl=selDataUrl;
  document.getElementById('hero').style.display='none';
  addU(q,imgUrl);
  const titleTxt=q||'Image Analysis';
  if(!cid){cid='c'+Date.now();chats.unshift({id:cid,t:titleTxt.slice(0,40),m:[]});}
  const ac=chats.find(x=>x.id===cid);ac.m.push({r:'u',t:q});localStorage.setItem('b_chats',JSON.stringify(chats));
  clearImg();
  inp.value='';const sb=document.getElementById('sbtn');sb.textContent='■';
  const fd=document.getElementById('feed'),vc=document.getElementById('vChat');
  const th=document.createElement('div');th.className='thk';
  th.innerHTML='<div class="orb"></div><span style="font-size:13px;color:var(--mut)">Researching evidence...</span>';
  fd.appendChild(th);vc.scrollTop=vc.scrollHeight;
  ctrl=new AbortController();
  try{
    const res=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,image_base64:b64,image_mime:mime}),signal:ctrl.signal});
    const data=await res.json();th.remove();addAI(data,q);ac.m.push({r:'a',d:data,q:q});localStorage.setItem('b_chats',JSON.stringify(chats));
  }catch(e){th.remove();addAI({direct_answer:e.name==='AbortError'?'Generation stopped.':'Network timeout. Please try again.',evidence:[],sources:[],confidence:'Info'},q);}
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
        "background_color": "#000000",
        "theme_color": "#0047CC",
        "icons": [{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"}]
    })

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
        client = genai.Client(api_key=api_key)
        cfg = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.3
        )
        res = client.models.generate_content(model="gemini-3.8-flash", contents=contents, config=cfg)
        raw = (res.text or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json\n", "", 1).strip()
        return jsonify(json.loads(raw))
    except Exception as e:
        return jsonify({"direct_answer": f"API Notice: {str(e)}", "evidence": [], "sources": [], "confidence": "Notice"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
      
