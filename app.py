import os
import json
from flask import Flask, request, jsonify, render_template_string, Response
from google import genai
from google.genai import types

app = Flask(__name__)

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    return genai.Client(api_key=api_key)

SYSTEM_PROMPT = """You are BLURO, a calm, authoritative, evidence-based scientific research AI assistant.
Respond ONLY in valid JSON with the exact keys below (no markdown blocks, no extra text):
{
  "direct_answer": "Clear, direct, accurate answer in 2-4 sentences. For greetings, welcome the user warmly as BLURO and invite a science question.",
  "evidence": [
    "Key scientific evidence point 1 with concrete data/mechanism (leave empty array [] for simple greetings)",
    "Key scientific evidence point 2 with empirical findings"
  ],
  "sources": [
    "Verified institution, peer-reviewed journal, or space agency (e.g., NASA, Nature, ESA, CERN)"
  ],
  "confidence": "98% (High Empirical Consensus)"
}
Use the same language as the user's question (English or Bengali)."""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="112" fill="#0052FF"/>
  <path fill="#FFFFFF" d="M168 112h112c56 0 96 34 96 84 0 34-18 60-48 72 38 12 62 42 62 82 0 56-44 90-106 90H168V112zm64 128h44c24 0 40-14 40-36s-16-36-40-36h-44v72zm0 144h50c28 0 46-15 46-39s-18-39-46-39h-50v78z"/>
</svg>"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#08080a">
<link rel="manifest" href="/manifest.json">
<link rel="icon" type="image/svg+xml" href="/icon.svg">
<link rel="apple-touch-icon" href="/icon.svg">
<title>BLURO</title>
<style>
  :root {
    --bg: #08080a;
    --surface: #121216;
    --surface-2: #1a1a20;
    --border: #24242c;
    --text: #f4f4f6;
    --muted: #8b8b97;
    --accent: #0052FF;
    --accent-soft: rgba(0, 82, 255, 0.16);
  }
  body.theme-light {
    --bg: #f6f7f9;
    --surface: #ffffff;
    --surface-2: #eef0f4;
    --border: #dcdfe6;
    --text: #111216;
    --muted: #5c606c;
  }
  body.theme-oled {
    --bg: #000000;
    --surface: #0b0b0e;
    --surface-2: #141419;
    --border: #1e1e26;
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
    transition: background 0.25s, color 0.25s;
  }

  .top-bar {
    padding: 12px 14px 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    background: var(--bg);
    z-index: 10;
  }
  .icon-btn {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
  }
  .tab-pill {
    display: flex;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 3px;
    flex: 1;
    max-width: 260px;
  }
  .tab-btn {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--muted);
    font-size: 13px;
    font-weight: 600;
    padding: 7px 10px;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .tab-btn.active {
    background: var(--surface-2);
    color: var(--text);
  }

  .drawer-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.65);
    z-index: 40;
    display: none;
  }
  .drawer-backdrop.open { display: block; }
  .drawer {
    position: fixed;
    top: 0;
    left: -290px;
    width: 280px;
    height: 100dvh;
    background: var(--surface);
    border-right: 1px solid var(--border);
    z-index: 50;
    display: flex;
    flex-direction: column;
    transition: left 0.28s cubic-bezier(0.22, 1, 0.36, 1);
    padding: 16px 14px;
  }
  .drawer.open { left: 0; }
  .drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }
  .drawer-title {
    font-size: 16px;
    font-weight: 800;
    letter-spacing: 2px;
  }
  .new-chat-btn {
    width: 100%;
    padding: 11px 14px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    margin-bottom: 12px;
  }
  .search-history {
    width: 100%;
    padding: 9px 12px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
    font-size: 13px;
    outline: none;
    margin-bottom: 12px;
  }
  .history-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--muted);
    margin-bottom: 8px;
    padding-left: 4px;
  }
  .history-list {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .history-item {
    padding: 10px 12px;
    border-radius: 10px;
    font-size: 13.5px;
    color: var(--text);
    background: transparent;
    border: none;
    text-align: left;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .history-item:hover, .history-item.active {
    background: var(--surface-2);
  }
  .drawer-footer {
    border-top: 1px solid var(--border);
    padding-top: 12px;
    margin-top: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  .user-pill {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    cursor: pointer;
    padding: 6px;
    border-radius: 12px;
  }
  .user-pill:active { background: var(--surface-2); }
  .avatar-circle {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    font-weight: 700;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .user-meta { overflow: hidden; }
  .user-name { font-size: 13.5px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .user-plan { font-size: 11px; color: #5b93ff; font-weight: 600; }

  .view {
    flex: 1;
    overflow-y: auto;
    display: none;
    flex-direction: column;
    padding: 16px;
  }
  .view.active { display: flex; }

  .hero {
    margin: auto;
    text-align: center;
    max-width: 440px;
    width: 100%;
    padding: 16px;
  }
  .hero h1 {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 3.5px;
  }
  .hero p {
    margin-top: 6px;
    font-size: 13px;
    color: var(--muted);
  }
  .chip-row {
    margin-top: 22px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
  }
  .prompt-chip {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 12.5px;
    padding: 8px 14px;
    border-radius: 999px;
    cursor: pointer;
  }
  .prompt-chip:active { border-color: var(--accent); }

  .chat-feed {
    display: flex;
    flex-direction: column;
    gap: 16px;
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
    animation: bluroPulse 1.25s infinite ease-in-out;
  }
  @keyframes bluroPulse {
    0% { transform: scale(0.85); box-shadow: 0 0 0 0 rgba(0, 82, 255, 0.75); }
    50% { transform: scale(1.25); box-shadow: 0 0 0 11px rgba(0, 82, 255, 0); }
    100% { transform: scale(0.85); box-shadow: 0 0 0 0 rgba(0, 82, 255, 0); }
  }
  .thinking-label {
    font-size: 13px;
    color: var(--muted);
    animation: fadePulse 1.25s infinite ease-in-out;
  }
  @keyframes fadePulse {
    0%, 100% { opacity: 0.45; }
    50% { opacity: 1; }
  }

  .ai-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px;
    animation: slideUp 0.25s ease;
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(6px); }
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
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #5b93ff;
  }
  .conf-badge {
    font-size: 11px;
    background: var(--accent-soft);
    color: #6ea0ff;
    padding: 3px 9px;
    border-radius: 999px;
  }
  .direct-text {
    font-size: 15px;
    line-height: 1.6;
  }
  .evidence-toggle {
    margin-top: 12px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 10px;
    cursor: pointer;
    width: 100%;
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
  }
  .evidence-box.open { display: block; }
  .evidence-box ul { padding-left: 18px; margin-bottom: 10px; }
  .evidence-box li { margin-bottom: 6px; }
  .sources-list {
    font-size: 12px;
    color: var(--muted);
    background: var(--bg);
    padding: 8px 10px;
    border-radius: 8px;
  }

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
  }
  .lib-card:active { border-color: var(--accent); }
  .lib-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
  .lib-sub { font-size: 13px; color: var(--muted); }

  .modal-screen {
    position: fixed;
    inset: 0;
    background: var(--bg);
    z-index: 60;
    display: none;
    flex-direction: column;
    overflow-y: auto;
  }
  .modal-screen.open { display: flex; }
  .modal-top {
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid var(--border);
  }
  .modal-top h2 { font-size: 18px; font-weight: 700; }
  .modal-body {
    padding: 18px 16px;
    max-width: 540px;
    width: 100%;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .settings-group {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
  }
  .settings-row {
    padding: 15px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    font-size: 14.5px;
    cursor: pointer;
  }
  .settings-row:last-child { border-bottom: none; }
  .settings-val { font-size: 13px; color: var(--muted); font-weight: 600; }
  .form-input {
    width: 100%;
    padding: 13px 14px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    font-size: 15px;
    outline: none;
  }
  .primary-btn {
    width: 100%;
    padding: 13px;
    border-radius: 12px;
    border: none;
    background: var(--accent);
    color: #fff;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
  }
  .danger-btn {
    width: 100%;
    padding: 13px;
    border-radius: 12px;
    border: 1px solid rgba(255, 77, 77, 0.35);
    background: rgba(255, 77, 77, 0.1);
    color: #ff5c5c;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
  }

  .input-dock {
    padding: 10px 14px 16px;
    background: var(--bg);
    border-top: 1px solid var(--border);
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
</style>
</head>
<body>

  <div class="drawer-backdrop" id="drawerBackdrop" onclick="toggleDrawer(false)"></div>
  <aside class="drawer" id="drawer">
    <div class="drawer-header">
      <span class="drawer-title">BLURO</span>
      <button class="icon-btn" style="width:32px;height:32px;" onclick="toggleDrawer(false)">✕</button>
    </div>
    <button class="new-chat-btn" onclick="startNewChat()">＋ New Chat</button>
    <input type="text" class="search-history" id="searchHistory" placeholder="Search chats..." oninput="renderHistory()">
    <div class="history-label">Recent Research</div>
    <div class="history-list" id="historyList"></div>
    <div class="drawer-footer">
      <div class="user-pill" onclick="openAuthModal()">
        <div class="avatar-circle" id="drawerAvatar">G</div>
        <div class="user-meta">
          <div class="user-name" id="drawerUserName">Sign Up / Log In</div>
          <div class="user-plan" id="drawerUserPlan">Free Account</div>
        </div>
      </div>
      <button class="icon-btn" onclick="openSettings()" title="Settings">⚙️</button>
    </div>
  </aside>

  <div class="top-bar">
    <button class="icon-btn" onclick="toggleDrawer(true)">☰</button>
    <div class="tab-pill">
      <button class="tab-btn active" id="btnChat" onclick="switchTab('chat')">Chat</button>
      <button class="tab-btn" id="btnLib" onclick="switchTab('lib')">Science Library</button>
    </div>
    <button class="icon-btn" onclick="startNewChat()" title="New Chat">✎</button>
  </div>

  <div class="view active" id="viewChat">
    <div class="hero" id="heroScreen">
      <h1>BLURO</h1>
      <p>Evidence-Based Science Research</p>
      <div class="chip-row">
        <button class="prompt-chip" onclick="quickAsk('What happens inside a black hole event horizon?')">Black hole event horizon</button>
        <button class="prompt-chip" onclick="quickAsk('How does
        
