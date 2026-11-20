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
