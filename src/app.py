import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import re
import json
import time
import uuid
import asyncio
import hashlib
import traceback
from pathlib import Path
from datetime import datetime

import streamlit as st
import edge_tts
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.graph import build_graph
from src.states import AgentState
from src.rag import document_loader

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Study Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_FILE_MB = 25
ALLOWED_TYPES = ["pdf", "docx", "txt", "csv", "md"]
UPLOAD_DIR = Path("Uploaded_Documents")

EXAMPLE_PROMPTS = [
    "Summarize my uploaded notes in 5 bullet points",
    "Quiz me on the key concepts from this material",
    "Explain this topic like I'm a beginner",
    "Find recent articles or videos related to this subject",
    "suggest some videos related to deep learning"
]

# Name of the youtube tool as registered in your tools_used package.
YOUTUBE_TOOL_NAME = "youtube_search_tool"

# A small curated set of Microsoft Edge neural voices — natural-sounding and
# free via edge-tts. Full list: `edge-tts --list-voices`.
EDGE_TTS_VOICES = {
    "Aria (US, warm)": "en-US-AriaNeural",
    "Guy (US, calm)": "en-US-GuyNeural",
    "Sonia (UK)": "en-GB-SoniaNeural",
    "Neerja (India)": "en-IN-NeerjaNeural",
    "Natasha (Australia)": "en-AU-NatashaNeural",
    "Nepali(Hemkala)":"ne-NP-HemkalaNeural",
    "Nepali(Sagar)":"ne-NP-SagarNeural"
}
DEFAULT_EDGE_VOICE_LABEL = "Aria (US, warm)"

# ---------------------------------------------------------------------------
# Custom styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Libre+Caslon+Display&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,500;0,8..60,600;1,8..60,400;1,8..60,500&family=Inter:wght@400;500;600;700&display=swap');

        :root {
            /* Warm reading-room palette: ivory page, oxblood leather spine, aged brass foil */
            --paper: #F7F1E1;
            --paper-dim: #EFE5C8;
            --paper-deep: #E7D9B2;
            --ink: #2B211A;
            --ink-soft: #5B4C3B;
            --ink-faint: #948263;
            --oxblood: #6E2A2E;
            --oxblood-deep: #521E22;
            --oxblood-light: #A45559;
            --brass: #AD8A45;
            --brass-deep: #8C6D2E;
            --brass-light: #E3CB8E;
            --pine: #3F5645;
            --navy: #1B2A4A;
            --navy-deep: #101B33;
            --navy-light: #3E5789;
            --rule: #D9C89C;
            --rule-strong: #C2AD79;
            --sidebar-bg: #1E1712;
            --sidebar-bg-alt: #271D16;
            --sidebar-text: #EFE4CB;
            --sidebar-text-dim: #B0A183;
            --rule-dark: rgba(239,228,203,0.14);
        }

        html, body, [class*="css"] {
            font-family: 'Source Serif 4', Georgia, serif;
            color: var(--ink);
        }
        .main {
            background:
                radial-gradient(ellipse 900px 500px at 12% -8%, rgba(173,138,69,0.10), transparent 60%),
                var(--paper);
        }
        h1, h2, h3 { font-family: 'Libre Caslon Display', Georgia, serif; letter-spacing: -0.005em; }
        p, span, div, label, li { font-family: 'Source Serif 4', Georgia, serif; }
        .stButton button, .stSelectbox, .stToggle, button, input, [data-testid="stChatInput"] textarea {
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
        }

        /* ---------- Hero: a manuscript title page ---------- */
        .hero {
            padding: 2.6rem 2.8rem 2.3rem 2.8rem;
            border-radius: 2px;
            background:
                linear-gradient(180deg, rgba(173,138,69,0.06), transparent 40%),
                var(--paper);
            border: 1px solid var(--rule-strong);
            border-left: 5px solid var(--oxblood);
            color: var(--ink);
            margin-bottom: 1.8rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 1px 0 var(--rule), 0 10px 26px -18px rgba(43,33,26,0.35);
            animation: fadeInUp 0.4s ease both;
        }
        .hero::before {
            content: "";
            position: absolute;
            top: 10px; left: 10px; right: 10px; bottom: 10px;
            border: 1px solid var(--brass-light);
            opacity: 0.55;
            pointer-events: none;
        }
        .hero::after {
            content: "❧";
            position: absolute;
            right: 1.6rem;
            bottom: 0.6rem;
            font-size: 2.4rem;
            color: var(--brass-light);
            opacity: 0.5;
            pointer-events: none;
        }
        .hero .eyebrow {
            font-family: 'Inter', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.22em;
            font-size: 0.68rem;
            color: var(--oxblood);
            font-weight: 700;
            margin: 0 0 0.8rem 0;
        }
        .hero .eyebrow::before { content: "✦ "; color: var(--brass-deep); }
        .hero h1 {
            font-size: 2.5rem;
            margin: 0 0 0.6rem 0;
            font-weight: 400;
            font-style: italic;
            letter-spacing: -0.005em;
            color: var(--navy);
        }
        .hero p { margin: 0; font-size: 1.04rem; color: var(--ink-soft); max-width: 50ch; line-height: 1.55; }
        .hero .badges { margin-top: 1.4rem; display: flex; gap: 1.7rem; flex-wrap: wrap; }
        .badge {
            display: inline-flex;
            align-items: center;
            font-family: 'Inter', sans-serif;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--brass-deep);
            font-weight: 600;
            border-bottom: 1px solid var(--rule-strong);
            padding-bottom: 0.2rem;
        }

        /* ---------- Sidebar: a librarian's desk ---------- */
        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(173,138,69,0.05), transparent 18%),
                var(--sidebar-bg);
            border-right: 1px solid rgba(173,138,69,0.25);
        }
        section[data-testid="stSidebar"] * { color: var(--sidebar-text) !important; }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4 { font-family: 'Libre Caslon Display', Georgia, serif; font-weight: 400; }
        section[data-testid="stSidebar"] .stButton button {
            width: 100%;
            font-family: 'Inter', sans-serif !important;
            border-radius: 2px;
            border: 1px solid var(--brass);
            background: transparent;
            color: var(--brass-light) !important;
            font-weight: 600;
            font-size: 0.85rem;
            letter-spacing: 0.02em;
            padding: 0.55rem 0;
            transition: background 0.18s ease, color 0.18s ease;
        }
        section[data-testid="stSidebar"] .stButton button:hover {
            background: var(--oxblood-light);
            color: var(--sidebar-bg) !important;
            border-color: var(--oxblood-light);
        }
        /* Index-card styling: a soft notch + dashed inner rule, like a library catalog card */
        .sidebar-card {
            background: var(--sidebar-bg-alt);
            border: 1px solid var(--rule-dark);
            border-left: 3px solid var(--brass);
            border-radius: 2px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.9rem;
            position: relative;
            transition: border-color 0.18s ease, transform 0.18s ease;
        }
        .sidebar-card:hover { border-left-color: var(--brass-light); transform: translateX(1px); }
        .sidebar-card small { color: var(--sidebar-text-dim) !important; font-family: 'Inter', sans-serif; }
        .stat-row { display:flex; gap:0.6rem; margin-bottom:0.9rem; }
        .stat-box {
            flex:1;
            background: var(--sidebar-bg-alt);
            border: 1px solid var(--rule-dark);
            border-top: 2px solid var(--brass);
            border-radius: 2px;
            padding: 0.7rem 0.5rem;
            text-align:center;
            transition: border-top-color 0.18s ease;
        }
        .stat-box:hover { border-top-color: var(--brass-light); }
        .stat-box .num { font-family: 'Libre Caslon Display', serif; font-size:1.5rem; font-weight:400; color: var(--brass-light); }
        .stat-box .lbl { font-family: 'Inter', sans-serif; font-size:0.64rem; letter-spacing:0.08em; text-transform:uppercase; color: var(--sidebar-text-dim) !important; }

        /* ---------- Global polish ---------- */
        * { scrollbar-width: thin; scrollbar-color: var(--rule-strong) transparent; }
        ::-webkit-scrollbar { width: 9px; height: 9px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--rule-strong); border-radius: 6px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--brass-deep); }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulseDot {
            0%   { box-shadow: 0 0 0 0 rgba(63,86,69,0.45); }
            70%  { box-shadow: 0 0 0 6px rgba(63,86,69,0); }
            100% { box-shadow: 0 0 0 0 rgba(63,86,69,0); }
        }
        .status-dot { animation: pulseDot 2.2s ease-out infinite; }
        .status-dot.offline { animation: none; }

        /* Block container: a touch of breathing room + subtle top vignette */
        div[data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 2.1rem;
            max-width: 1160px;
        }

        /* ---------- Chat bubbles: distinct roles, gentle entrance ---------- */
        div[data-testid="stChatMessage"] {
            border-radius: 8px;
            padding: 0.7rem 0.95rem;
            margin-bottom: 0.75rem;
            animation: fadeInUp 0.32s ease both;
            box-shadow: 0 1px 0 var(--rule);
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
            background: var(--paper-dim);
            border: 1px solid var(--rule);
            border-right: 3px solid var(--brass);
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
            background: var(--paper);
            border: 1px solid var(--rule);
            border-left: 3px solid var(--oxblood);
        }
        div[data-testid="stChatMessageContent"] p,
        div[data-testid="stChatMessageContent"] li { line-height: 1.65; }
        div[data-testid="stChatMessageContent"] h1,
        div[data-testid="stChatMessageContent"] h2,
        div[data-testid="stChatMessageContent"] h3 {
            color: var(--oxblood);
            margin-top: 0.9rem;
            margin-bottom: 0.4rem;
        }
        div[data-testid="stChatMessageContent"] code {
            background: var(--paper-dim);
            border: 1px solid var(--rule);
            border-radius: 3px;
            color: var(--oxblood-deep);
        }
        div[data-testid="stChatMessageContent"] blockquote {
            border-left: 3px solid var(--brass);
            padding-left: 0.8rem;
            color: var(--ink-soft);
            font-style: italic;
        }

        /* Chat input: give it a manuscript-ruled feel */
        div[data-testid="stChatInput"] {
            border: 1px solid var(--rule-strong) !important;
            border-radius: 8px !important;
            background: var(--paper) !important;
            box-shadow: 0 2px 10px -6px rgba(43,33,26,0.25) !important;
        }
        div[data-testid="stChatInput"]:focus-within {
            border-color: var(--oxblood) !important;
            box-shadow: 0 0 0 3px rgba(110,42,46,0.12) !important;
        }

        /* ---------- File uploader: themed dropzone ---------- */
        section[data-testid="stFileUploaderDropzone"] {
            background: var(--sidebar-bg-alt) !important;
            border: 1.5px dashed var(--brass) !important;
            border-radius: 4px !important;
        }
        section[data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--brass-light) !important;
            background: #2C2114 !important;
        }
        section[data-testid="stFileUploaderDropzone"] button {
            border: 1px solid var(--brass) !important;
            color: var(--brass-light) !important;
            background: transparent !important;
        }

        /* ---------- Selects / toggles in sidebar ---------- */
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: var(--sidebar-bg-alt) !important;
            border: 1px solid var(--rule-dark) !important;
            border-radius: 3px !important;
        }
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.82rem;
            letter-spacing: 0.02em;
            color: var(--sidebar-text-dim) !important;
        }

        /* ---------- Section dividers in sidebar: small-caps rule ---------- */
        section[data-testid="stSidebar"] hr {
            border-top: 1px solid rgba(173,138,69,0.25) !important;
            margin: 1.1rem 0;
        }
        div[data-testid="stStatusWidget"] { display: none; }

        /* ---------- Main-area buttons (example prompt chips) ---------- */
        div[data-testid="stAppViewContainer"] .main .stButton button {
            font-family: 'Inter', sans-serif !important;
            border-radius: 2px;
            border: 1px solid var(--rule-strong);
            background: var(--paper);
            color: var(--ink-soft);
            font-weight: 500;
            transition: border-color 0.18s ease, color 0.18s ease, background 0.18s ease;
        }
        div[data-testid="stAppViewContainer"] .main .stButton button:hover {
            border-color: var(--oxblood);
            color: var(--oxblood);
            background: var(--paper-dim);
        }

        /* ---------- YouTube video cards ---------- */
        .video-card-link {
            display: block;
            text-decoration: none !important;
            margin-top: 0.5rem;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .video-card-link:hover { transform: translateY(-2px); box-shadow: 0 8px 18px -12px rgba(43,33,26,0.4); }
        .video-card-link img {
            width: 100%;
            border-radius: 3px;
            display: block;
            border: 1px solid var(--rule-strong);
        }
        .video-card-title {
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--ink);
            margin-top: 0.4rem;
            line-height: 1.3;
        }
        .video-card-channel {
            font-family: 'Inter', sans-serif;
            font-size: 0.7rem;
            color: var(--oxblood);
            margin-top: 0.15rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .video-card-fallback {
            display: block;
            border: 1px solid var(--rule);
            border-left: 3px solid var(--brass);
            border-radius: 2px;
            padding: 0.6rem 0.8rem;
            margin-top: 0.5rem;
            text-decoration: none !important;
            background: var(--paper-dim);
            color: var(--ink);
        }
        /* ---------- Text-to-speech card ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--paper-dim) !important;
            border: 1px solid var(--rule-strong) !important;
            border-left: 3px solid var(--oxblood) !important;
            border-radius: 4px !important;
            padding: 0.2rem 0.2rem !important;
        }
        .tts-label {
            font-family: 'Inter', sans-serif;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--oxblood);
            font-weight: 700;
            margin: 0.3rem 0 0.5rem 0.1rem;
        }
        audio {
            width: 100%;
            height: 36px;
            border-radius: 18px;
            outline: none;
            accent-color: var(--navy);
            background-color: var(--navy);
        }
        audio::-webkit-media-controls-panel {
            background-color: var(--navy);
        }
        audio::-webkit-media-controls-play-button,
        audio::-webkit-media-controls-mute-button {
            background-color: var(--navy-light);
            border-radius: 50%;
        }
        audio::-webkit-media-controls-current-time-display,
        audio::-webkit-media-controls-time-remaining-display {
            color: var(--sidebar-text, #EFE4CB);
        }
        audio::-webkit-media-controls-timeline {
            background-color: var(--navy-light);
            border-radius: 12px;
            margin: 0 8px;
        }
        audio::-webkit-media-controls-volume-slider {
            background-color: var(--navy-light);
            border-radius: 12px;
        }

        /* ---------- Misc: info banner, section rules ---------- */
        div[data-testid="stAlertContainer"] {
            background: var(--paper-dim) !important;
            border: 1px solid var(--rule-strong) !important;
            border-left: 3px solid var(--brass) !important;
            border-radius: 3px !important;
            color: var(--ink) !important;
        }
        hr, div[data-testid="stMarkdownContainer"] hr {
            border-top: 1px solid var(--rule-strong) !important;
        }

    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">The AI Study Agent</div>
        <h1>Study, grounded in your own material</h1>
        <p>Ask questions, upload your notes, and get answers grounded in what you've given it — with web and video resources close at hand.</p>
        <div class="badges">
            <span class="badge">📄 Document retrieval</span>
            <span class="badge">🌐 Live web search</span>
            <span class="badge">▶️ Video resources</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Build (and cache) the compiled LangGraph workflow
# ---------------------------------------------------------------------------
@st.cache_resource
def get_workflow():
    return build_graph()

workflow_ready = False
workflow = None
init_error = None
try:
    workflow = get_workflow()
    workflow_ready = True
except Exception as e:
    init_error = e

if not workflow_ready:
    st.error("⚠️ Failed to initialize the study agent. The app will stay in read-only mode until this is fixed.")
    with st.expander("Show error details"):
        st.code("".join(traceback.format_exception(type(init_error), init_error, init_error.__traceback__)))

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
defaults = {
    "thread_id": str(uuid.uuid4()),
    "messages": [],           # [{"role", "content", "ts", "videos"}]
    "ingested_files": [],     # [{"name", "chunks", "hash"}]
    "ingested_hashes": set(), # dedupe uploads across reruns
    "pending_input": None,    # queued question from an example chip
    "is_processing": False,
    "show_steps": True,       # whether to show live tool/generation status while answering
    "tts_voice_label": DEFAULT_EDGE_VOICE_LABEL,  # selected edge-tts voice (display label)
    "tts_cache": {},          # (voice, text-hash) -> mp3 bytes, so we never re-call edge-tts for the same text+voice
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

config = {"configurable": {"thread_id": st.session_state.thread_id}}


def file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sanitize_filename(name: str) -> str:
    keep = "-_. "
    cleaned = "".join(c for c in name if c.isalnum() or c in keep).strip()
    return cleaned or "untitled_upload"


# ---------------------------------------------------------------------------
# Helpers for surfacing what the agent is doing (nodes / tool calls)
# ---------------------------------------------------------------------------
NODE_ICONS = {
    "rag": "📄", "doc": "📄", "retriev": "📄",
    "web": "🌐", "search": "🌐",
    "video": "▶️", "youtube": "▶️",
    "generat": "✍️", "answer": "✍️", "llm": "✍️", "respond": "✍️",
    "route": "🧭", "plan": "🧭", "decide": "🧭",
    "tool": "🛠️",
}


def icon_for(name: str) -> str:
    n = name.lower()
    for key, icon in NODE_ICONS.items():
        if key in n:
            return icon
    return "⚙️"


def humanize(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").strip().title()


def extract_latest_ai_content(messages):
    """Return the content of the most recent AIMessage that has real content (not just a tool call)."""
    content = None
    for m in messages or []:
        if isinstance(m, AIMessage) and m.content:
            content = m.content
        elif isinstance(m, dict) and m.get("type") in ("ai", "assistant") and m.get("content"):
            content = m["content"]
    return content


# Common alternate keys different graph implementations use for the final answer.
ANSWER_KEYS = ("answer", "response", "output", "final_answer", "generation", "result", "text")


def extract_answer_from_state(state):
    """Best-effort extraction of a final answer string from an arbitrary LangGraph state dict."""
    if state is None:
        return None
    if isinstance(state, str) and state.strip():
        return state
    if not isinstance(state, dict):
        return None

    # 1. Standard "messages" list (most common pattern).
    content = extract_latest_ai_content(state.get("messages"))
    if content:
        return content

    # 2. Common alternate top-level keys.
    for key in ANSWER_KEYS:
        val = state.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, list):
            nested = extract_latest_ai_content(val)
            if nested:
                return nested

    return None


def debug_state_summary(state):
    """A short, safe-to-display summary of a state dict for troubleshooting."""
    if not isinstance(state, dict):
        return f"type={type(state)} value={str(state)[:500]}"
    lines = []
    for k, v in state.items():
        if isinstance(v, list):
            lines.append(f"{k}: list[{len(v)}] -> {[type(i).__name__ for i in v][:5]}")
        else:
            lines.append(f"{k}: {type(v).__name__} = {str(v)[:200]}")
    return "\n".join(lines)


def get_thread_message_count(thread_config):
    """How many messages are currently checkpointed for this thread, BEFORE we run
    the current turn. Used to figure out which messages are new once the turn is done,
    so we never re-surface tool results (like YouTube videos) from earlier turns."""
    try:
        snapshot = workflow.get_state(thread_config)
        values = getattr(snapshot, "values", None) or {}
        return len(values.get("messages", []) or [])
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Video extraction / rendering
# ---------------------------------------------------------------------------
def extract_videos_from_messages(messages, debug_log=None):
    """Scan a list of graph messages for ToolMessage results from the YouTube tool
    and normalize them into a flat list of video dicts.

    debug_log: optional list; if provided, raw tool-message info is appended to it
    so we can inspect exactly what the tool returned when parsing fails.
    """
    videos = []
    for m in messages or []:
        name = None
        content = None

        if isinstance(m, ToolMessage):
            name = getattr(m, "name", None)
            content = m.content
        elif isinstance(m, dict) and m.get("type") == "tool":
            name = m.get("name")
            content = m.get("content")

        if name != YOUTUBE_TOOL_NAME or content is None:
            continue

        if debug_log is not None:
            debug_log.append(f"[{name}] type={type(content).__name__} raw={str(content)[:400]}")

        items = []
        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            items = content.get("videos") or content.get("items") or []
        elif isinstance(content, str):
            # Tool output is usually JSON-serialized by ToolNode; fall back to
            # Python-literal parsing in case the tool itself did str(list_of_dicts).
            for parser_name, parser in (("json", json.loads), ("literal", None)):
                try:
                    if parser_name == "json":
                        parsed = json.loads(content)
                    else:
                        import ast
                        parsed = ast.literal_eval(content)
                    if isinstance(parsed, list):
                        items = parsed
                        break
                    if isinstance(parsed, dict):
                        items = parsed.get("videos") or parsed.get("items") or []
                        break
                except Exception:
                    continue

        for item in items:
            if isinstance(item, dict) and item.get("url"):
                videos.append(item)

    # de-duplicate by URL while preserving order
    seen = set()
    unique = []
    for v in videos:
        url = v.get("url")
        if url and url not in seen:
            seen.add(url)
            unique.append(v)
    return unique


def get_videos_for_thread(thread_config, after_index=0, debug_log=None):
    """Fetch the latest full state from the checkpointer and pull out any YouTube
    results that appeared strictly AFTER `after_index` messages — i.e. only videos
    produced during the current turn.

    IMPORTANT: `after_index` must be the message count captured BEFORE this turn's
    stream/invoke ran (see get_thread_message_count). Without this slicing, every
    call re-scans the entire thread history and re-surfaces YouTube results from any
    earlier turn, even ones like "thank you" that never triggered the tool.
    """
    try:
        snapshot = workflow.get_state(thread_config)
        state_values = getattr(snapshot, "values", None) or {}
        all_messages = state_values.get("messages", []) or []
        new_messages = all_messages[after_index:]
        if debug_log is not None:
            debug_log.append(
                f"total messages={len(all_messages)}, after_index={after_index}, "
                f"new messages this turn={len(new_messages)}"
            )
        return extract_videos_from_messages(new_messages, debug_log=debug_log)
    except Exception as e:
        if debug_log is not None:
            debug_log.append(f"get_state() failed while fetching videos: {e}")
        return []


def render_videos(videos):
    if not videos:
        return
    st.markdown("**▶️ Related videos**")
    cols = st.columns(min(len(videos), 3))
    for i, v in enumerate(videos[:6]):
        title = v.get("title", "Video")
        channel = v.get("channel", "")
        url = v.get("url", "#")
        thumb = v.get("thumbnail")
        with cols[i % len(cols)]:
            if thumb:
                st.markdown(
                    f"""
                    <a class="video-card-link" href="{url}" target="_blank">
                        <img src="{thumb}">
                        <div class="video-card-title">{title}</div>
                        <div class="video-card-channel">{channel}</div>
                    </a>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <a class="video-card-fallback" href="{url}" target="_blank">
                        ▶️ <b>{title}</b><br>
                        <small>{channel}</small>
                    </a>
                    """,
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# Text-to-speech (edge-tts)
# ---------------------------------------------------------------------------
def extract_speech_text(markdown_text: str) -> str:
    """Cut a full answer down to just the substantive explanation before it's
    spoken. Source-attribution blocks (📄 documents / 🌐 web / 🎥 videos) and
    reference-only sections are already shown visually as text and video cards —
    reading filenames, page numbers, and URLs aloud adds nothing, so those
    sections are dropped here. Everything else (the actual explanation, examples,
    key takeaways) is kept as-is."""
    if not markdown_text:
        return ""

    skip_markers = ("📄", "🌐", "🎥")
    skip_keywords = ("source", "reference", "citation", "recommended video", "uploaded document", "external information")

    kept_lines = []
    skipping = False

    for line in markdown_text.splitlines():
        stripped = line.strip()
        looks_like_heading = stripped.startswith("#") or stripped.endswith(":") or any(m in stripped for m in skip_markers)

        if looks_like_heading:
            lower = stripped.lower()
            skipping = any(m in stripped for m in skip_markers) or any(kw in lower for kw in skip_keywords)

        if skipping:
            continue
        kept_lines.append(line)

    return "\n".join(kept_lines)


def clean_text_for_speech(text: str) -> str:
    """Strip markdown syntax and other non-spoken artifacts so the voice doesn't
    read out asterisks, hashes, code fences, or raw URLs."""
    if not text:
        return ""
    t = text

    t = re.sub(r"```.*?```", " code block omitted. ", t, flags=re.DOTALL)      # fenced code
    t = re.sub(r"`([^`]*)`", r"\1", t)                                        # inline code
    t = re.sub(r"!\[.*?\]\(.*?\)", "", t)                                     # images
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", t)                          # [text](url) -> text
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.MULTILINE)                      # headings
    t = re.sub(r"(\*\*|__)(.*?)\1", r"\2", t)                                 # bold
    t = re.sub(r"(\*|_)(.*?)\1", r"\2", t)                                    # italics
    t = re.sub(r"^\s*[-•▸>]\s*", "", t, flags=re.MULTILINE)                   # bullets / blockquote markers
    t = re.sub(r"\n{2,}", ". ", t)                                            # paragraph breaks -> pause
    t = re.sub(r"\s+", " ", t).strip()

    return t


async def _edge_tts_generate(text: str, voice: str) -> bytes:
    """Stream audio chunks from edge-tts and concatenate them into a single MP3."""
    communicate = edge_tts.Communicate(text, voice)
    audio_chunks = bytearray()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            audio_chunks.extend(chunk["data"])
    return bytes(audio_chunks)


def text_to_speech_bytes(text: str, voice: str):
    """Generate MP3 audio bytes for the given text via edge-tts. Returns None on
    failure (e.g. no network access) rather than raising, so a TTS failure never
    breaks the chat. edge-tts is async-only, so we run it through asyncio.run()
    here to call it from Streamlit's synchronous script execution."""
    clean = clean_text_for_speech(extract_speech_text(text))
    if not clean:
        return None
    try:
        return asyncio.run(_edge_tts_generate(clean, voice))
    except Exception:
        return None


def get_or_create_audio(text: str, voice: str):
    """Cache audio per unique (voice, text) pair so reruns / repeated Listen
    clicks on the same message don't re-hit the edge-tts service."""
    cache = st.session_state.setdefault("tts_cache", {})
    digest = hashlib.sha256(f"{voice}:{text}".encode("utf-8")).hexdigest()
    if digest in cache:
        return cache[digest]
    audio_bytes = text_to_speech_bytes(text, voice=voice)
    if audio_bytes:
        cache[digest] = audio_bytes
    return audio_bytes


def current_voice() -> str:
    label = st.session_state.get("tts_voice_label", DEFAULT_EDGE_VOICE_LABEL)
    return EDGE_TTS_VOICES.get(label, EDGE_TTS_VOICES[DEFAULT_EDGE_VOICE_LABEL])


def render_tts_control(text: str, key: str):
    """A single 'Generate audio' button inside a themed card. Click it once —
    audio is generated (or pulled from cache) and plays immediately. No toggle
    state to manage."""
    if not text or not text.strip():
        return

    audio_key = f"tts_audio_{key}"
    has_audio = bool(st.session_state.get(audio_key))

    with st.container(border=True):
        st.markdown(
            f'<div class="tts-label">{"▸ Audio" if has_audio else "▸ Listen to this answer"}</div>',
            unsafe_allow_html=True,
        )

        if not has_audio:
            if st.button("🔊 Generate audio", key=f"tts_btn_{key}"):
                audio_bytes = get_or_create_audio(text, voice=current_voice())
                if audio_bytes:
                    st.session_state[audio_key] = audio_bytes
                    st.rerun()
                else:
                    st.caption("Couldn't generate audio for this response — check network access to edge-tts.")

        if st.session_state.get(audio_key):
            try:
                st.audio(st.session_state[audio_key], format="audio/mp3", autoplay=True)
            except TypeError:
                # Older Streamlit versions don't support the autoplay kwarg.
                st.audio(st.session_state[audio_key], format="audio/mp3")


# ---------------------------------------------------------------------------
# Sidebar: document upload for the RAG tool
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📄 Study Material")
    st.caption(f"Upload notes, textbooks, or slides (max {MAX_FILE_MB} MB each) to ground answers in your own material.")

    uploaded_files = st.file_uploader(
        "Upload files",
        type=ALLOWED_TYPES,
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        new_files = []
        for uf in uploaded_files:
            data = uf.getbuffer()
            h = file_hash(bytes(data))
            if h in st.session_state.ingested_hashes:
                continue
            if uf.size > MAX_FILE_MB * 1024 * 1024:
                st.warning(f"⏭️ Skipped **{uf.name}** — exceeds {MAX_FILE_MB} MB limit.")
                continue
            new_files.append((uf, data, h))

        if new_files:
            for uf, data, h in new_files:
                st.markdown(
                    f"""
                    <div class="sidebar-card">
                        📎 <b>{uf.name}</b><br>
                        <small>{uf.size / 1024:.1f} KB &middot; ready to ingest</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if st.button(f"✨ Ingest {len(new_files)} new file(s)"):
                UPLOAD_DIR.mkdir(exist_ok=True)
                progress = st.progress(0.0, text="Starting ingestion...")
                succeeded, failed = 0, []

                for i, (uf, data, h) in enumerate(new_files, start=1):
                    safe_name = sanitize_filename(uf.name)
                    save_path = UPLOAD_DIR / safe_name
                    try:
                        with open(save_path, "wb") as f:
                            f.write(data)
                        num_chunks = document_loader(str(save_path))
                        st.session_state.ingested_files.append(
                            {"name": uf.name, "chunks": num_chunks, "hash": h}
                        )
                        st.session_state.ingested_hashes.add(h)
                        succeeded += 1
                    except Exception as e:
                        failed.append((uf.name, str(e)))
                    progress.progress(i / len(new_files), text=f"Processed {i}/{len(new_files)} files")

                progress.empty()
                if succeeded:
                    st.success(f"Ingested {succeeded} document(s) successfully.")
                for name, err in failed:
                    st.error(f"Failed to ingest **{name}**: {err}")
                if succeeded:
                    st.rerun()

    if st.session_state.ingested_files:
        st.markdown("#### 🗂️ Knowledge base")
        total_chunks = sum(f["chunks"] for f in st.session_state.ingested_files)
        st.markdown(
            f"""
            <div class="stat-row">
                <div class="stat-box"><div class="num">{len(st.session_state.ingested_files)}</div><div class="lbl">documents</div></div>
                <div class="stat-box"><div class="num">{total_chunks}</div><div class="lbl">chunks</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for idx, f in enumerate(st.session_state.ingested_files):
            cols = st.columns([5, 1])
            with cols[0]:
                st.markdown(
                    f"""
                    <div class="sidebar-card">
                        ✅ <b>{f['name']}</b><br>
                        <small>{f['chunks']} chunks embedded</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with cols[1]:
                if st.button("✕", key=f"remove_{idx}", help="Remove from this session's list (already-embedded chunks remain in the vector store)"):
                    st.session_state.ingested_hashes.discard(f["hash"])
                    st.session_state.ingested_files.pop(idx)
                    st.rerun()

    st.divider()

    st.session_state.show_steps = st.toggle(
        "🔎 Show agent steps", value=st.session_state.show_steps,
        help="See live progress as the agent searches documents, browses the web, or generates its answer.",
    )

    st.session_state.tts_voice_label = st.selectbox(
        "🔊 Voice",
        options=list(EDGE_TTS_VOICES.keys()),
        index=list(EDGE_TTS_VOICES.keys()).index(st.session_state.tts_voice_label),
        help="Voice used when you click 'Generate audio' on an answer.",
    )

    status_color = "#5A7A62" if workflow_ready else "#A45559"
    status_text = "Agent online" if workflow_ready else "Agent unavailable"
    dot_class = "status-dot" if workflow_ready else "status-dot offline"
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.8rem;">
            <div class="{dot_class}" style="width:9px;height:9px;border-radius:50%;background:{status_color};"></div>
            <span style="font-family:'Inter',sans-serif;font-size:0.85rem;">{status_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ Clear chat"):
            st.session_state.messages = []
            st.session_state.thread_id = str(uuid.uuid4())
            st.rerun()
    with col_b:
        chat_txt = "\n\n".join(
            f"{'You' if m['role']=='user' else 'Agent'} ({m.get('ts','')}): {m['content']}"
            for m in st.session_state.messages
        )
        st.download_button(
            "⬇️ Export",
            data=chat_txt or "No messages yet.",
            file_name=f"study_session_{st.session_state.thread_id[:8]}.txt",
            mime="text/plain",
            disabled=not st.session_state.messages,
        )

    st.markdown(
        '<p class="footer-note">Session ID: ' + st.session_state.thread_id[:8] + "…</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Render existing chat history
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown(
        """
        <div style="background: var(--paper-dim); border: 1px solid var(--rule-strong);
                    border-left: 3px solid var(--brass); border-radius: 4px;
                    padding: 1.1rem 1.3rem; margin-bottom: 0.9rem;">
            <span style="font-family:'Libre Caslon Display', serif; font-size:1.05rem; color: var(--ink);">
                👋 Welcome — ask a study question below, or upload material in the sidebar first.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-family:\'Inter\',sans-serif; text-transform:uppercase; letter-spacing:0.08em; '
        'font-size:0.72rem; color: var(--brass-deep); font-weight:600; margin-bottom:0.6rem;">'
        '✦ Try one of these to get going</p>',
        unsafe_allow_html=True,
    )
    chip_cols = st.columns(len(EXAMPLE_PROMPTS))
    for col, prompt in zip(chip_cols, EXAMPLE_PROMPTS):
        with col:
            if st.button(prompt, use_container_width=True, disabled=not workflow_ready):
                st.session_state.pending_input = prompt

for idx, msg in enumerate(st.session_state.messages):
    avatar = "🧑‍🎓" if msg["role"] == "user" else "📚"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("ts"):
            st.caption(msg["ts"])
        if msg["role"] == "assistant":
            render_videos(msg.get("videos", []))
            render_tts_control(msg["content"], key=f"hist_{idx}")

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
typed_input = st.chat_input("Ask a study question...", disabled=not workflow_ready or st.session_state.is_processing)
user_input = st.session_state.pending_input or typed_input
st.session_state.pending_input = None

if user_input:
    ts = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "content": user_input, "ts": ts})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(user_input)
        st.caption(ts)

    with st.chat_message("assistant", avatar="📚"):
        st.session_state.is_processing = True
        start = time.time()
        answer = None
        seen_steps = []
        last_node_state = None
        debug_notes = []
        video_debug = []

        # Snapshot how many messages exist BEFORE this turn runs. Everything at or
        # after this index in the final state is new this turn — this is what lets
        # us render only THIS turn's YouTube results, instead of re-surfacing
        # tool output from earlier turns on every subsequent message (including
        # ones like "thank you" that never call the tool at all).
        prev_message_count = get_thread_message_count(config)

        status_box = st.status("🧠 Thinking…", expanded=st.session_state.show_steps) if st.session_state.show_steps else None
        placeholder = st.empty()
        if not status_box:
            placeholder.markdown("_Thinking…_")

        def log_step(text: str):
            seen_steps.append(text)
            if status_box:
                status_box.write(text)

        try:
            # Prefer streaming so we can surface each node / tool call as it runs.
            stream = workflow.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="updates",
            )
            for update in stream:
                if not isinstance(update, dict):
                    continue
                for node_name, node_state in update.items():
                    label = f"{icon_for(node_name)} {humanize(node_name)}"
                    if status_box:
                        status_box.update(label=label)
                    log_step(label)
                    last_node_state = node_state

                    node_messages = node_state.get("messages", []) if isinstance(node_state, dict) else []
                    for m in node_messages:
                        tool_calls = getattr(m, "tool_calls", None)
                        if isinstance(m, AIMessage) and tool_calls:
                            for tc in tool_calls:
                                tool_name = tc.get("name", "tool") if isinstance(tc, dict) else getattr(tc, "name", "tool")
                                log_step(f"🛠️ Using tool: `{tool_name}`")

                    found = extract_answer_from_state(node_state)
                    if found:
                        answer = found

            # If streaming updates never surfaced a final answer, check the graph's
            # full accumulated state as a second attempt before giving up.
            if answer is None:
                try:
                    snapshot = workflow.get_state(config)
                    final_state = getattr(snapshot, "values", None)
                    answer = extract_answer_from_state(final_state)
                    if answer is None:
                        debug_notes.append("get_state() values:\n" + debug_state_summary(final_state))
                except Exception as gs_err:
                    debug_notes.append(f"get_state() failed: {gs_err}")

            if answer is None:
                debug_notes.append("last node_state seen:\n" + debug_state_summary(last_node_state))
                answer = "I couldn't generate a response — please try rephrasing your question."

            if status_box:
                status_box.update(label="✅ Done" if debug_notes == [] else "⚠️ Done (no answer found)",
                                   state="complete" if debug_notes == [] else "error",
                                   expanded=bool(debug_notes))

        except Exception as stream_err:
            # Some graphs / langgraph versions may not support stream_mode="updates" —
            # fall back to a plain invoke so the app still works.
            if status_box:
                status_box.update(label="⚙️ Generating (fallback mode)…")
            try:
                result = workflow.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=config,
                )
                answer = extract_answer_from_state(result)
                if answer is None:
                    debug_notes.append("invoke() result:\n" + debug_state_summary(result))
                    answer = "I couldn't generate a response — please try rephrasing your question."
                if status_box:
                    status_box.update(label="✅ Done" if not debug_notes else "⚠️ Done (no answer found)",
                                       state="complete", expanded=bool(debug_notes))
            except Exception as e:
                answer = f" Something went wrong while answering: `{e}`"
                debug_notes.append(f"Streaming error: {stream_err}\n\nFallback error: {e}\n\n{traceback.format_exc()}")
                if status_box:
                    status_box.update(label="❌ Error", state="error", expanded=True)
        finally:
            st.session_state.is_processing = False

        # Pull any YouTube results out of the final checkpointed state, but ONLY
        # the ones that appeared after `prev_message_count` — i.e. only videos the
        # tool produced during THIS turn. This is what prevents old video results
        # from re-appearing under unrelated later replies like "thank you".
        videos = get_videos_for_thread(config, after_index=prev_message_count, debug_log=video_debug)

        elapsed = time.time() - start
        placeholder.markdown(answer)
        st.caption(f"answered in {elapsed:.1f}s" + (f" · {len(seen_steps)} step(s)" if seen_steps else ""))
        render_videos(videos)
        render_tts_control(answer, key=f"live_{len(st.session_state.messages)}")

        if debug_notes:
            with st.expander("🐞 Debug: raw agent state (no answer key matched)"):
                st.caption(
                    "The agent ran without errors, but the app couldn't find the final answer text in the "
                    "state. This means your graph stores it under a key other than the ones checked "
                    f"({', '.join(['messages'] + list(ANSWER_KEYS))}). Share this with whoever maintains "
                    "`src/graph.py` / `src/states.py` so the extraction logic can target the right key."
                )
                st.code("\n\n---\n\n".join(debug_notes))

        # If a youtube tool call happened but we still found zero videos, show what
        # the tool actually returned so we can see why parsing failed.
        if not videos and any("youtube" in s.lower() for s in seen_steps):
            with st.expander("🐞 Debug: youtube_search_tool returned no usable videos"):
                if video_debug:
                    st.code("\n\n---\n\n".join(video_debug))
                else:
                    st.caption("No ToolMessage named 'youtube_search_tool' was found in the final state at all.")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "ts": datetime.now().strftime("%H:%M"), "videos": videos}
    )
    st.rerun()