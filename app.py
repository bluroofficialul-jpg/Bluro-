import os, json, base64
from flask import Flask, request, jsonify, render_template_string, Response
from google import genai
from google.genai import types

app = Flask(__name__)

SYSTEM_PROMPT = 'You are BLURO, an evidence-based scientific research assistant. Respond ONLY in valid JSON with keys: "direct_answer" (string, clear concise explanation in the same language as the user), "evidence" (array of 3-4 short scientific evidence points), "sources" (array of 2-3 credible scientific sources/institutions), "confidence" (string like "95% Scientific Consensus").'

ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="110" fill="#0052FF"/><text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" fill="#FFFFFF" font-family="Arial,sans-serif" font-weight="bold" font-size="310">B</text></svg>'

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#08080a">
<link rel="manifest" href="/manifest.json">
<link rel="icon" type="image/svg+xml" href="/icon.svg">
<title>BLURO</title>
<style>
:root{--bg:#08080a;--sf:#121216;--sf2:#1a1a20;--bd:#24242c;--tx:#f4f4f6;--mt:#8e8e9a;--ac:#0052FF}
body.light{--bg:#f6f7f9;--sf:#fff;--sf2:#eef0f4;--bd:#dcdfe6;--tx:#111318;--mt:#646a78}
body.oled{--bg:#000;--sf:#0b0b0e;--sf2:#141419;--bd:#1e1e26}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,sans-serif;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
.top{padding:12px 14px 8px;display:flex;align-items:center;justify-content:space-between;gap:8px}
.ibtn{width:38px;height:38px;border-radius:12px;border:1px solid var(--bd);background:var(--sf);color:var(--tx);display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0}
.pill{display:flex;background:var(--sf);border:1px solid var(--bd);border-radius:14px;padding:3px;flex:1;max-width:260px}
.tbtn{flex:1;border:none;background:transparent;color:var(--mt);font-size:13px;font-weight:600;padding:7px 8px;border-radius:11px;cursor:pointer}
.tbtn.act{background:var(--sf2);color:var(--tx)}
.bg-dim{position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:40;display:none}
.bg-dim.open{display:block}
.drw{position:fixed;top:0;left:-290px;width:280px;height:100dvh;background:var(--sf);border-right:1px solid var(--bd);z-index:50;display:flex;flex-direction:column;padding:14px;transition:left .22s}
.drw.open{left:0}
.drw-hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.new-btn{width:100%;padding:11px 14px;border-radius:12px;border:1px solid var(--bd);background:var(--sf2);color:var(--tx);font-weight:600;font-size:13.5px;text-align:left;cursor:pointer;margin-bottom:10px}
.srch{width:100%;padding:9px 12px;border-radius:10px;border:1px solid var(--bd);background:var(--bg);color:var(--tx);font-size:13px;margin-bottom:12px;outline:none}
.hlbl{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--mt);margin-bottom:6px}
.hlst{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:5px}
.hitm{padding:10px 12px;border-radius:10px;font-size:13.5px;color:var(--tx);background:transparent;border:none;text-align:left;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hitm.act{background:var(--sf2)}
.drw-ft{border-top:1px solid var(--bd);padding-top:12px;margin-top:8px;display:flex;align-items:center;gap:8px}
.upill{display:flex;align-items:center;gap:10px;flex:1;cursor:pointer;overflow:hidden}
.avt{width:34px;height:34px;border-radius:50%;background:var(--ac);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0}
.view{flex:1;overflow-y:auto;display:none;flex-direction:column;padding:12px 16px}
.view.act{display:flex}
.hero{margin:auto;text-align:center;max-width:440px;padding:16px}
.hero h1{font-size:32px;font-weight:800;letter-spacing:3.5px}
.hero p{margin-top:6px;font-size:13px;color:var(--mt)}
.chips{margin-top:20px;display:flex;flex-direction:column;gap:8px}
.chip{padding:11px 14px;border-radius:14px;border:1px solid var(--bd);background:var(--sf);color:var(--tx);font-size:13px;text-align:left;cursor:pointer}
.feed{display:flex;flex-direction:column;gap:14px;max-width:680px;width:100%;margin:0 auto;padding-bottom:16px}
.u-msg{align-self:flex-end;background:var(--ac);color:#fff;padding:11px 15px;border-radius:18px 18px 4px 18px;max-width:82%;font-size:14.5px;line-height:1.45}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:18px;padding:15px}
.brow{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:8px}
.btag{font-size:11px;font-weight:700;letter-spacing:1.2px;color:#5b93ff}
.cbadge{font-size:11px;padding:3px 9px;border-radius:99px;background:rgba(0,82,255,.15);color:#6ea0ff;font-weight:600}
.dtxt{font-size:14.5px;line-height:1.6;color:var(--tx)}
.etog{margin-top:12px;width:100%;padding:9px 12px;border-radius:11px;border:1px solid var(--bd);background:var(--sf2);color:var(--tx);font-size:12.5px;font-weight:600;display:flex;justify-content:space-between;cursor:pointer}
.ebox{display:none;margin-top:10px;padding-top:10px;border-top:1px solid var(--bd);font-size:13px;color:var(--mt)}
.ebox.open{display:block}
.ebox ul{padding-left:18px;display:flex;flex-direction:column;gap:6px;margin-bottom:8px}
.srcs{font-size:12px;color:#6ea0ff}
.thk{display:flex;align-items:center;gap:10px;padding:10px 4px}
.orb{width:14px;height:14px;border-radius:50%;background:var(--ac);animation:pls 1.1s infinite ease-in-out}
@keyframes pls{0%,100%{transform:scale(.85);opacity:.5}50%{transform:scale(1.2);opacity:1}}
.lgrid{display:grid;grid-template-columns:1fr;gap:10px;max-width:680px;width:100%;margin:0 auto}
.lcard{background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:14px;cursor:pointer}
.dock{padding:8px 14px 14px;max-width:680px;width:100%;margin:0 auto}
.ibox{display:flex;align-items:center;gap:6px;background:var(--sf);border:1px solid var(--bd);border-radius:26px;padding:5px 6px}
.ibox .ibtn{border:none;background:transparent;width:36px;height:36px}
.ibox input[type="text"],.ibox input:not([type]){flex:1;background:transparent;border:none;color:var(--tx);font-size:15px;outline:none;padding:6px 4px;min-width:0}
.sbtn{width:36px;height:36px;border-radius:50%;border:none;background:var(--ac);color:#fff;font-size:16px;font-weight:700;cursor:pointer;flex-shrink:0}
.modal{position:fixed;inset:0;background:var(--bg);z-index:60;display:none;flex-direction:column;padding:16px}
.modal.open{display:flex}
.mtop{display:flex;align-items:center;gap:12px;margin-bottom:18px}
.mbody{display:flex;flex-direction:column;gap:14px;max-width:480px;width:100%;margin:0 auto}
.sgrp{background:var(--sf);border:1px solid var(--bd);border-radius:16px;overflow:hidden}
.srow{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--bd);font-size:14px;cursor:pointer}
.srow:last-child{border-bottom:none}
.finp{padding:13px 14px;border-radius:12px;border:1px solid var(--bd);background:var(--sf);color:var(--tx);font-size:14px;outline:none}
.pbtn{padding:13px;border-radius:12px;border:none;background:var(--ac);color:#fff;font-weight:700;font-size:14.5px;cursor:pointer}
.dbtn{padding:13px;border-radius:12px;border:1px solid #5c2328;background:rgba(220,53,69,.12);color:#ff6b78;font-weight:600;font-size:14px;cursor:pointer}
</style>
</head>
<body>
<div class="bg-dim" id="dim" onclick="drw(0)"></div>
<aside class="drw" id="drw">
  <div class="drw-hd"><span style="font-weight:800;letter-spacing:2px">BLURO</span><button class="ibtn" onclick="drw(0)">✕</button></div>
  <button class="new-btn" onclick="newChat();drw(0)">+ New Research</button>
  <input class="srch" id="srch" placeholder="Search chat history..." oninput="rHist()">
  <div class="hlbl">History</div>
  <div class="hlst" id="hlst"></div>
  <div class="drw-ft">
    <div class="upill" onclick="openM('authM')">
      <div class="avt" id="avt">G</div>
      <div style="overflow:hidden"><div id="uname" style="font-size:13.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Sign Up / Log In</div><div id="uplan" style="font-size:11.5px;color:var(--mt)">Guest Mode</div></div>
    </div>
    <button class="ibtn" onclick="openM('setM')">⚙</button>
  </div>
</aside>

<div class="top">
  <button class="ibtn" onclick="drw(1)">☰</button>
  <div style="position:relative">
    <button class="ibtn" id="mBtn" onclick="togMod()" style="width:auto;padding:0 12px;gap:6px;font-size:13px;font-weight:700"><span id="mLbl">Bluro 3.8</span><span style="font-size:10px;color:var(--mt)">⌄</span></button>
    <div id="mMenu" style="display:none;position:fixed;top:56px;left:14px;width:235px;background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:6px;z-index:55;box-shadow:0 12px 30px rgba(0,0,0,.6)">
      <div onclick="setMod('auto','Bluro Auto')" style="padding:10px 12px;border-radius:11px;cursor:pointer"><div style="font-size:13.5px;font-weight:600">Auto</div><div style="font-size:11.5px;color:var(--mt)">Adapts to your research</div></div>
      <div onclick="setMod('fast','Bluro 3.0')" style="padding:10px 12px;border-radius:11px;cursor:pointer"><div style="font-size:13.5px;font-weight:600">Everyday Research</div><div style="font-size:11.5px;color:var(--mt)">Bluro 3.0 • Fast & direct</div></div>
      <div onclick="setMod('deep','Bluro 3.8')" style="padding:10px 12px;border-radius:11px;cursor:pointer"><div style="font-size:13.5px;font-weight:600">Deeper Analysis</div><div style="font-size:11.5px;color:var(--mt)">Bluro 3.8 • Deep evidence</div></div>
    </div>
  </div>
  <div class="pill">
    <button class="tbtn act" id="bChat" onclick="tab('chat')">Chat</button>
    <button class="tbtn" id="bLib" onclick="tab('lib')">Science Library</button>
  </div>
  <button class="ibtn" onclick="newChat()">✎</button>
</div>


<div class="view act" id="vChat">
  <div class="hero" id="hero">
    <h1>BLURO</h1>
    <p>Evidence-Based Science Research</p>
    <div class="chips">
      <button class="chip" onclick="qAsk('What happens inside a black hole event horizon?')">Black hole event horizon</button>
      <button class="chip" onclick="qAsk('How does time dilation work near light speed?')">Time dilation & relativity</button>
      <button class="chip" onclick="qAsk('Why are spotted hyenas able to crush bone?')">Hyena bite force biology</button>
    </div>
  </div>
  <div class="feed" id="feed"></div>
</div>

<div class="view" id="vLib"><div class="lgrid" id="lgrid"></div></div>

<div class="dock" id="dock">
  <div class="ibox">
    <input type="file" id="galInp" accept="image/*" style="display:none" onchange="onImgPick(this)">
    <input type="file" id="camInp" accept="image/*" capture="environment" style="display:none" onchange="onImgPick(this)">
    <button type="button" class="ibtn" onclick="togPlus()" title="Add"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></button>
    <input id="qin" placeholder="ask bluro" autocomplete="off" onkeypress="if(event.key==='Enter')sendOrStop()">
    <span id="imgTag" style="font-size:11px;color:#5b93ff;white-space:nowrap"></span>
    <button type="button" class="ibtn" id="micBtn" onclick="toggleVoice()" title="Voice"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg></button>
    <button class="sbtn" id="sbtn" onclick="sendOrStop()">↑</button>
  </div>
  <div id="plusSheet" style="display:none;margin-top:10px;padding:12px;background:var(--sf);border:1px solid var(--bd);border-radius:20px;gap:10px">
    <button type="button" onclick="togPlus();document.getElementById('galInp').click()" style="flex:1;padding:14px 10px;background:var(--bg);border:1px solid var(--bd);border-radius:16px;color:var(--tx);display:flex;flex-direction:column;align-items:center;gap:8px;font-size:13px;cursor:pointer"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg><span>Photos</span></button>
    <button type="button" onclick="togPlus();document.getElementById('camInp').click()" style="flex:1;padding:14px 10px;background:var(--bg);border:1px solid var(--bd);border-radius:16px;color:var(--tx);display:flex;flex-direction:column;align-items:center;gap:8px;font-size:13px;cursor:pointer"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg><span>Camera</span></button>
  </div>
</div>

<div class="modal" id="setM">
  <div class="mtop"><button class="ibtn" onclick="closeM('setM')">←</button><h2>Settings</h2></div>
  <div class="mbody">
    <div class="sgrp">
      <div class="srow" onclick="closeM('setM');openM('authM')"><span>Manage Account</span><span id="sAcc" style="color:var(--mt);font-size:13px">Sign Up →</span></div>
      <div class="srow"><span>Usage Plan</span><span style="color:#5b93ff;font-size:13px">Unlimited Free</span></div>
    </div>
    <div class="sgrp">
      <div class="srow" onclick="cycTheme()"><span>Theme</span><span id="sThm" style="color:var(--mt);font-size:13px">Dark</span></div>
      <div class="srow" onclick="cycDepth()"><span>Research Depth</span><span id="sDep" style="color:var(--mt);font-size:13px">Evidence + Sources</span></div>
      <div class="srow" onclick="togEv()"><span>Auto-Expand Evidence</span><span id="sEv" style="color:var(--mt);font-size:13px">Off</span></div>
    </div>
    <button class="dbtn" onclick="clrHist()">Clear All Chat History</button>
  </div>
</div>

<div class="modal" id="authM">
  <div class="mtop"><button class="ibtn" onclick="closeM('authM')">←</button><h2 id="aTit">Create BLURO Account</h2></div>
  <div class="mbody">
    <input class="finp" id="aName" placeholder="Your Full Name (e.g. Minsarul)">
    <input class="finp" id="aMail" placeholder="Email Address (e.g. name@gmail.com)">
    <button class="pbtn" onclick="saveAcc()">Save & Continue</button>
    <button class="dbtn" id="outBtn" style="display:none" onclick="outAcc()">Sign Out</button>
  </div>
</div>

<script>
const CATS=[
  {n:"Space & Universe",d:"Black holes, dark matter, JWST & cosmology",p:"Explain how Sagittarius A* supermassive black hole affects nearby stars."},
  {n:"Physics",d:"Relativity, quantum mechanics & spacetime",p:"Explain Einstein's 4D Minkowski spacetime and time dilation simply."},
  {n:"Chemistry",d:"Elements, molecular reactions & astrochemistry",p:"How are heavy elements like gold forged in neutron star collisions?"},
  {n:"Biology",d:"Evolution, genetics & extremophile life",p:"How do extremophiles survive deep-sea hydrothermal vents?"},
  {n:"Earth & Climate",d:"Atmosphere, magnetosphere & geology",p:"How does Earth's magnetic field protect our atmosphere from solar wind?"},
  {n:"Animals",d:"Wildlife ecology, predator biology & behavior",p:"Explain the bite force and bone-crushing adaptation of spotted hyenas."},
  {n:"Astronomy",d:"Exoplanets, solar system & observational science",p:"How do astronomers detect exoplanet atmospheres using JWST spectroscopy?"}
];
let chats=JSON.parse(localStorage.getItem('b_chats')||'[]'),cid=null,ctrl=null;
let prefs=JSON.parse(localStorage.getItem('b_prefs')||'{"t":"Dark","d":"Evidence + Sources","e":false}');
let user=JSON.parse(localStorage.getItem('b_user')||'null');
let selImgB64='',selImgMime='image/jpeg';let curTier='deep';
function togMod(){const m=document.getElementById('mMenu');m.style.display=m.style.display==='block'?'none':'block';}
function setMod(t,lbl){curTier=t;document.getElementById('mLbl').textContent=lbl;document.getElementById('mMenu').style.display='none';}


function appPrefs(){
  document.body.className=prefs.t==='Light'?'light':(prefs.t==='OLED Black'?'oled':'');
  document.getElementById('sThm').textContent=prefs.t;
  document.getElementById('sDep').textContent=prefs.d;
  document.getElementById('sEv').textContent=prefs.e?'On':'Off';
}
function upUser(){
  if(user&&user.n){
    document.getElementById('avt').textContent=user.n[0].toUpperCase();
    document.getElementById('uname').textContent=user.n;
    document.getElementById('uplan').textContent=user.m||'BLURO Member';
    document.getElementById('sAcc').textContent=user.n+' →';
    document.getElementById('aTit').textContent='Manage Account';
    document.getElementById('aName').value=user.n;
    document.getElementById('aMail').value=user.m||'';
    document.getElementById('outBtn').style.display='block';
  }else{
    document.getElementById('avt').textContent='G';
    document.getElementById('uname').textContent='Sign Up / Log In';
    document.getElementById('uplan').textContent='Guest Mode';
    document.getElementById('sAcc').textContent='Sign Up →';
    document.getElementById('aTit').textContent='Create BLURO Account';
    document.getElementById('outBtn').style.display='none';
  }
}
function saveAcc(){
  const n=document.getElementById('aName').value.trim(),m=document.getElementById('aMail').value.trim();
  if(!n)return alert('Enter your name');
  user={n,m};localStorage.setItem('b_user',JSON.stringify(user));upUser();closeM('authM');
}
function outAcc(){user=null;localStorage.removeItem('b_user');upUser();closeM('authM');}
function cycTheme(){const o=['Dark','OLED Black','Light'];prefs.t=o[(o.indexOf(prefs.t)+1)%3];localStorage.setItem('b_prefs',JSON.stringify(prefs));appPrefs();}
function cycDepth(){prefs.d=prefs.d==='Evidence + Sources'?'Concise Direct':'Evidence + Sources';localStorage.setItem('b_prefs',JSON.stringify(prefs));appPrefs();}
function togEv(){prefs.e=!prefs.e;localStorage.setItem('b_prefs',JSON.stringify(prefs));appPrefs();}
function drw(o){document.getElementById('drw').classList.toggle('open',!!o);document.getElementById('dim').classList.toggle('open',!!o);if(o)rHist();}
function openM(id){drw(0);document.getElementById(id).classList.add('open');}
function closeM(id){document.getElementById(id).classList.remove('open');}
function rHist(){
  const q=document.getElementById('srch').value.toLowerCase(),l=document.getElementById('hlst');l.innerHTML='';
  chats.filter(c=>c.t.toLowerCase().includes(q)).forEach(c=>{
    const b=document.createElement('button');b.className='hitm'+(c.id===cid?' act':'');b.textContent=c.t;
    b.onclick=()=>{cid=c.id;document.getElementById('hero').style.display='none';const f=document.getElementById('feed');f.innerHTML='';c.m.forEach(x=>x.r==='u'?addU(x.t):addAI(x.d));drw(0);};
    l.appendChild(b);
  });
}
function newChat(){cid=null;document.getElementById('feed').innerHTML='';document.getElementById('hero').style.display='block';}
function clrHist(){if(confirm('Clear all history?')){chats=[];localStorage.removeItem('b_chats');newChat();closeM('setM');}}
CATS.forEach(c=>{
  const d=document.createElement('div');d.className='lcard';
  d.innerHTML=`<div style="font-weight:700;margin-bottom:4px">${c.n}</div><div style="font-size:13px;color:var(--mt)">${c.d}</div>`;
  d.onclick=()=>{tab('chat');qAsk(c.p);};document.getElementById('lgrid').appendChild(d);
});
function tab(t){
  document.getElementById('bChat').classList.toggle('act',t==='chat');
  document.getElementById('bLib').classList.toggle('act',t==='lib');
  document.getElementById('vChat').classList.toggle('act',t==='chat');
  document.getElementById('vLib').classList.toggle('act',t==='lib');
  document.getElementById('dock').style.display=t==='chat'?'block':'none';
}
function togPlus(){const p=document.getElementById('plusSheet');p.style.display=p.style.display==='flex'?'none':'flex';}
function onImgPick(inp){
  const f=inp.files&&inp.files[0];if(!f)return;
  selImgMime=f.type||'image/jpeg';
  const r=new FileReader();
  r.onload=()=>{selImgB64=String(r.result||'').split(',')[1]||'';document.getElementById('imgTag').textContent='Photo ✓';};
  r.readAsDataURL(f);
}
function toggleVoice(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert('Voice not supported');return;}
  const mb=document.getElementById('micBtn');mb.style.color='#5b93ff';
  const rec=new SR();rec.lang='en-US';
  rec.onresult=(e)=>{document.getElementById('qin').value=e.results[0][0].transcript||'';};
  rec.onend=()=>{mb.style.color='';};
  rec.start();
}
function qAsk(t){document.getElementById('qin').value=t;send();}
function addU(t){const d=document.createElement('div');d.className='u-msg';d.textContent=t;document.getElementById('feed').appendChild(d);}
function addAI(data){
  const c=document.createElement('div');c.className='card';
  const id='e'+Math.random().toString(36).slice(2,8);
  const ev=(data.evidence||[]).map(x=>`<li>${x}</li>`).join('');
  const sr=(data.sources||[]).join(' • ');
  c.innerHTML=`<div class="brow"><span class="btag">BLURO</span><span class="cbadge">${data.confidence||'Verified'}</span></div>
    <div class="dtxt">${data.direct_answer||data.error||'No response'}</div>
  ${ev&&prefs.d!=='Concise Direct'?`<button class="etog" onclick="document.getElementById('${id}').classList.toggle('open')"><span>Show Evidence & Sources</span><span>▾</span></button>
  <div class="ebox ${prefs.e?'open':''}" id="${id}"><ul>${ev}</ul><div class="srcs"><strong>Sources:</strong> ${sr}</div></div>`:''}`;
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
  selImgB64='';document.getElementById('imgTag').textContent='';document.getElementById('galInp').value='';document.getElementById('camInp').value='';
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
appPrefs();upUser();
</script>
</body>
</html>'''

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
        try:
            img_bytes = base64.b64decode(img_b64)
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type=img_mime))
        except Exception as e:
            return jsonify({"direct_answer": f"Image error: {e}", "evidence": [], "sources": [], "confidence": "Error"}), 400
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    cfg = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.3
    )
  
  try:
        res = client.models.generate_content(model="gemini-3.8-flash", contents=contents, config=cfg)
        return jsonify(json.loads(res.text))
    except Exception as e:
        return jsonify({"direct_answer": f"Error: {str(e)}", "evidence": [], "sources": [], "confidence": "Error"}), 500
