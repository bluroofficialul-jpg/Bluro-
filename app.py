import os, json
from flask import Flask, request, jsonify, render_template_string, Response
from google import genai
from google.genai import types

app = Flask(__name__)

SYSTEM_PROMPT = 'You are BLURO, an evidence-based scientific research AI. Reply ONLY in valid JSON: {"direct_answer":"Clear direct answer in 2-4 sentences (warm welcome for greetings).","evidence":["Key scientific evidence 1 (empty [] for greetings)","Key scientific evidence 2"],"sources":["Verified institution/journal e.g. NASA, Nature"],"confidence":"98% Empirical Consensus"}. Match user language.'

ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="112" fill="#0052FF"/><path fill="#FFF" d="M168 112h112c56 0 96 34 96 84 0 34-18 60-48 72 38 12 62 42 62 82 0 56-44 90-106 90H168V112zm64 128h44c24 0 40-14 40-36s-16-36-40-36h-44v72zm0 144h50c28 0 46-15 46-39s-18-39-46-39h-50v78z"/></svg>'

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
:root{--bg:#08080a;--sf:#121216;--sf2:#1a1a20;--bd:#24242c;--tx:#f4f4f6;--mt:#8b8b97;--ac:#0052FF}
body.light{--bg:#f6f7f9;--sf:#fff;--sf2:#eef0f4;--bd:#dcdfe6;--tx:#111216;--mt:#5c606c}
body.oled{--bg:#000;--sf:#0b0b0e;--sf2:#141419;--bd:#1e1e26}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
.top{padding:12px 14px 8px;display:flex;align-items:center;justify-content:space-between;gap:10px}
.ibtn{width:38px;height:38px;border-radius:12px;border:1px solid var(--bd);background:var(--sf);color:var(--tx);font-size:18px;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0}
.pill{display:flex;background:var(--sf);border:1px solid var(--bd);border-radius:999px;padding:3px;flex:1;max-width:260px}
.tbtn{flex:1;border:none;background:transparent;color:var(--mt);font-size:13px;font-weight:600;padding:7px 10px;border-radius:999px;cursor:pointer}
.tbtn.act{background:var(--sf2);color:var(--tx)}
.bg-dim{position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:40;display:none}
.bg-dim.open{display:block}
.drw{position:fixed;top:0;left:-290px;width:280px;height:100dvh;background:var(--sf);border-right:1px solid var(--bd);z-index:50;display:flex;flex-direction:column;transition:left .25s;padding:16px 14px}
.drw.open{left:0}
.drw-hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;font-weight:800;letter-spacing:2px}
.new-btn{width:100%;padding:11px 14px;border-radius:12px;border:1px solid var(--bd);background:var(--sf2);color:var(--tx);font-size:14px;font-weight:600;text-align:left;cursor:pointer;margin-bottom:10px}
.srch{width:100%;padding:9px 12px;border-radius:10px;border:1px solid var(--bd);background:var(--bg);color:var(--tx);font-size:13px;outline:none;margin-bottom:10px}
.hlbl{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--mt);margin-bottom:6px}
.hlst{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:5px}
.hitm{padding:10px 12px;border-radius:10px;font-size:13.5px;color:var(--tx);background:transparent;border:none;text-align:left;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hitm.act{background:var(--sf2)}
.drw-ft{border-top:1px solid var(--bd);padding-top:12px;margin-top:8px;display:flex;align-items:center;justify-content:space-between;gap:8px}
.upill{display:flex;align-items:center;gap:10px;flex:1;cursor:pointer;padding:6px;border-radius:12px;overflow:hidden}
.avt{width:34px;height:34px;border-radius:50%;background:var(--ac);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.view{flex:1;overflow-y:auto;display:none;flex-direction:column;padding:16px}
.view.act{display:flex}
.hero{margin:auto;text-align:center;max-width:440px;padding:16px}
.hero h1{font-size:32px;font-weight:800;letter-spacing:3.5px}
.hero p{margin-top:6px;font-size:13px;color:var(--mt)}
.chips{margin-top:20px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px}
.chip{background:var(--sf);border:1px solid var(--bd);color:var(--tx);font-size:12.5px;padding:8px 14px;border-radius:999px;cursor:pointer}
.feed{display:flex;flex-direction:column;gap:16px;max-width:720px;width:100%;margin:0 auto;padding-bottom:16px}
.u-msg{align-self:flex-end;background:var(--ac);color:#fff;padding:11px 16px;border-radius:20px 20px 4px 20px;font-size:15px;max-width:82%;word-wrap:break-word}
.thk{display:flex;align-items:center;gap:12px;padding:8px 4px}
.orb{width:13px;height:13px;border-radius:50%;background:var(--ac);animation:pls 1.25s infinite ease-in-out}
@keyframes pls{0%,100%{transform:scale(.85);box-shadow:0 0 0 0 rgba(0,82,255,.75)}50%{transform:scale(1.25);box-shadow:0 0 0 11px rgba(0,82,255,0)}}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:18px;padding:16px}
.brow{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.btag{font-size:11px;font-weight:800;letter-spacing:1.5px;color:#5b93ff}
.cbadge{font-size:11px;background:rgba(0,82,255,.16);color:#6ea0ff;padding:3px 9px;border-radius:999px}
.dtxt{font-size:15px;line-height:1.6}
.etog{margin-top:12px;background:var(--sf2);border:1px solid var(--bd);color:var(--tx);font-size:13px;font-weight:600;padding:8px 12px;border-radius:10px;cursor:pointer;width:100%;display:flex;justify-content:space-between}
.ebox{display:none;margin-top:10px;padding-top:10px;border-top:1px solid var(--bd);font-size:13.5px;line-height:1.55}
.ebox.open{display:block}
.ebox ul{padding-left:18px;margin-bottom:8px}
.srcs{font-size:12px;color:var(--mt);background:var(--bg);padding:8px 10px;border-radius:8px}
.lgrid{display:grid;gap:12px;max-width:720px;width:100%;margin:0 auto;padding-bottom:24px}
.lcard{background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:16px;cursor:pointer}
.modal{position:fixed;inset:0;background:var(--bg);z-index:60;display:none;flex-direction:column;overflow-y:auto}
.modal.open{display:flex}
.mtop{padding:14px 16px;display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--bd)}
.mbody{padding:18px 16px;max-width:540px;width:100%;margin:0 auto;display:flex;flex-direction:column;gap:14px}
.sgrp{background:var(--sf);border:1px solid var(--bd);border-radius:16px;overflow:hidden}
.srow{padding:15px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--bd);font-size:14.5px;cursor:pointer}
.srow:last-child{border-bottom:none}
.finp{width:100%;padding:13px 14px;border-radius:12px;border:1px solid var(--bd);background:var(--sf);color:var(--tx);font-size:15px;outline:none}
.pbtn{width:100%;padding:13px;border-radius:12px;border:none;background:var(--ac);color:#fff;font-size:15px;font-weight:700;cursor:pointer}
.dbtn{width:100%;padding:13px;border-radius:12px;border:1px solid rgba(255,77,77,.35);background:rgba(255,77,77,.1);color:#ff5c5c;font-size:14px;font-weight:600;cursor:pointer}
.dock{padding:10px 14px 16px;background:var(--bg);border-top:1px solid var(--bd)}
.ibox{max-width:720px;margin:0 auto;display:flex;align-items:center;background:var(--sf);border:1px solid var(--bd);border-radius:999px;padding:6px 8px 6px 18px}
.ibox input{flex:1;background:transparent;border:none;outline:none;color:var(--tx);font-size:15px}
.sbtn{width:36px;height:36px;border-radius:50%;border:none;background:var(--ac);color:#fff;font-size:16px;font-weight:700;cursor:pointer}
</style>
</head>
<body>
<div class="bg-dim" id="dim" onclick="drw(0)"></div>
<aside class="drw" id="drw">
  <div class="drw-hd"><span>BLURO</span><button class="ibtn" style="width:32px;height:32px" onclick="drw(0)">✕</button></div>
  <button class="new-btn" onclick="newChat()">＋ New Chat</button>
  <input class="srch" id="srch" placeholder="Search chats..." oninput="rHist()">
  <div class="hlbl">Recent Research</div>
  <div class="hlst" id="hlst"></div>
  <div class="drw-ft">
    <div class="upill" onclick="openM('authM')">
      <div class="avt" id="avt">G</div>
      <div style="overflow:hidden"><div id="uname" style="font-size:13.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Sign Up / Log In</div><div id="uplan" style="font-size:11px;color:#5b93ff">Guest Mode</div></div>
    </div>
    <button class="ibtn" onclick="openM('setM')">⚙️</button>
  </div>
</aside>

<div class="top">
  <button class="ibtn" onclick="drw(1)">☰</button>
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
    <input id="qin" placeholder="ask bluro" autocomplete="off" onkeypress="if(event.key==='Enter')sendOrStop()">
    <button class="sbtn" id="sbtn" onclick="sendOrStop()">↑</button>
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
  {n:"Space & Universe",d:"Black holes, dark matter, JWST & cosmology",p:"Explain how Sagittarius A* supermassive black hole shapes the Milky Way galaxy."},
  {n:"Physics",d:"Relativity, quantum mechanics & spacetime",p:"Explain Einstein's 4D Minkowski spacetime and time dilation with experimental proof."},
  {n:"Chemistry",d:"Elements, molecular reactions & astrochemistry",p:"How are heavy elements like gold forged in neutron star collisions?"},
  {n:"Biology",d:"Evolution, genetics & extremophile life",p:"How do extremophiles survive deep-sea hydrothermal vents?"},
  {n:"Earth & Climate",d:"Atmosphere, magnetosphere & geology",p:"How does Earth's magnetic field protect our atmosphere from solar wind?"},
  {n:"Animals",d:"Wildlife ecology, predator biology & behavior",p:"Explain the bite force and bone-crushing adaptation of spotted hyenas."},
  {n:"Astronomy",d:"Exoplanets, solar system & observational science",p:"How do astronomers detect exoplanet atmospheres using transit spectroscopy?"}
];
let chats=JSON.parse(localStorage.getItem('b_chats')||'[]'),cid=null,ctrl=null;
let prefs=JSON.parse(localStorage.getItem('b_prefs')||'{"t":"Dark","d":"Evidence + Sources","e":false}');
let user=JSON.parse(localStorage.getItem('b_user')||'null');

function apPrefs(){
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
function cycTheme(){const o=['Dark','OLED Black','Light'];prefs.t=o[(o.indexOf(prefs.t)+1)%3];localStorage.setItem('b_prefs',JSON.stringify(prefs));apPrefs();}
function cycDepth(){prefs.d=prefs.d==='Evidence + Sources'?'Concise Direct':'Evidence + Sources';localStorage.setItem('b_prefs',JSON.stringify(prefs));apPrefs();}
function togEv(){prefs.e=!prefs.e;localStorage.setItem('b_prefs',JSON.stringify(prefs));apPrefs();}
function drw(o){document.getElementById('drw').classList.toggle('open',!!o);document.getElementById('dim').classList.toggle('open',!!o);if(o)rHist();}
function openM(id){drw(0);document.getElementById(id).classList.add('open');}
function closeM(id){document.getElementById(id).classList.remove('open');}
function rHist(){
  const q=document.getElementById('srch').value.toLowerCase(),l=document.getElementById('hlst');l.innerHTML='';
  chats.filter(c=>c.t.toLowerCase().includes(q)).forEach(c=>{
    const b=document.createElement('button');b.className='hitm'+(c.id===cid?' act':'');b.textContent=c.t;
    b.onclick=()=>{cid=c.id;document.getElementById('hero').style.display='none';const f=document.getElementById('feed');f.innerHTML='';c.m.forEach(x=>x.r==='u'?addU(x.t):addAI(x.d));tab('chat');drw(0);};
    l.appendChild(b);
  });
}
function newChat(){cid=null;document.getElementById('feed').innerHTML='';document.getElementById('hero').style.display='block';tab('chat');drw(0);}
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
  const inp=document.getElementById('qin'),q=inp.value.trim();if(!q)return;
  document.getElementById('hero').style.display='none';addU(q);
  if(!cid){cid='c'+Date.now();chats.unshift({id:cid,t:q.slice(0,40),m:[]});}
  const ac=chats.find(x=>x.id===cid);ac.m.push({r:'u',t:q});localStorage.setItem('b_chats',JSON.stringify(chats));
  inp.value='';const sb=document.getElementById('sbtn');sb.textContent='■';
  const fd=document.getElementById('feed'),vc=document.getElementById('vChat');
  const th=document.createElement('div');th.className='thk';
  th.innerHTML='<div class="orb"></div><span style="font-size:13px;color:var(--mt)">Researching evidence...</span>';
  fd.appendChild(th);vc.scrollTop=vc.scrollHeight;
  ctrl=new AbortController();
  try{
    const res=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q}),signal:ctrl.signal});
    const data=await res.json();th.remove();addAI(data);ac.m.push({r:'a',d:data});localStorage.setItem('b_chats',JSON.stringify(chats));
  }catch(e){th.remove();addAI({direct_answer:e.name==='AbortError'?'Generation stopped.':'Connection error.',confidence:'Info'});}
  ctrl=null;sb.textContent='↑';vc.scrollTop=vc.scrollHeight;
}
apPrefs();upUser();
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
    return jsonify({"name":"BLURO","short_name":"BLURO","start_url":"/","display":"standalone","background_color":"#08080a","theme_color":"#0052FF","icons":[{"src":"/icon.svg","sizes":"512x512","type":"image/svg+xml","purpose":"any maskable"}]})

@app.route("/ask", methods=["POST"])
def ask():
    q = (request.get_json() or {}).get("question", "").strip()
    if not q:
        return jsonify({"error": "Empty"}), 400
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        res = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=q,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, response_mime_type="application/json", temperature=0.3)
        )
        return jsonify(json.loads(res.text))
    except Exception as e:
        return jsonify({"direct_answer": f"Error: {str(e)}", "evidence": [], "sources": [], "confidence": "Error"}), 500

if __name__ == "__main__":
    app.run(host="
  
