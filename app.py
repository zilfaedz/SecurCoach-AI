import html
import json
import os
import time
from datetime import datetime
from pathlib import Path
import tomllib
from urllib import error, request
from urllib.parse import quote
from uuid import uuid4

import streamlit as st


DOMAINS = [
    "General Security",
    "Network Security",
    "Web App Security",
    "Cloud Security",
    "Cryptography",
    "Incident Response",
]
MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]


st.set_page_config(page_title="SecurCoach AI", page_icon="S", layout="wide", initial_sidebar_state="collapsed")


def load_root_secrets():
    path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_secret_value(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return load_root_secrets().get(key, os.getenv(key, default)) or default


def get_react_app_url():
    return get_secret_value("REACT_APP_URL", "http://localhost:3000")


def get_gemini_api_key():
    return get_secret_value("GEMINI_API_KEY", "")


def get_supabase_url():
    return get_secret_value("SUPABASE_URL", "")


def get_supabase_key():
    return get_secret_value("SUPABASE_KEY", "")


def get_supabase_chat_history_table():
    return get_secret_value("SUPABASE_CHAT_HISTORY_TABLE", "chat_history")


def ensure_auth_session_state():
    st.session_state.setdefault("is_authenticated", False)
    st.session_state.setdefault("auth_user_email", "")
    st.session_state.setdefault("conversation_loaded", False)
    st.session_state.setdefault("current_conversation_id", "")
    st.session_state.setdefault("conversation_summaries", [])


def apply_query_auth():
    auth_email = st.query_params.get("auth_email", "").strip().lower()
    if auth_email:
        st.session_state.is_authenticated = True
        st.session_state.auth_user_email = auth_email
        st.session_state.conversation_loaded = False


def get_user_id():
    return st.session_state.get("auth_user_email", "").strip().lower()


def supabase_request(method, path, payload=None, query="", extra_headers=None):
    supabase_url = get_supabase_url().rstrip("/")
    supabase_key = get_supabase_key()
    if not supabase_url or not supabase_key:
        return None
    url = f"{supabase_url}/rest/v1/{path}"
    if query:
        url = f"{url}?{query}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except Exception as exc:
        st.session_state.supabase_error = str(exc)
        return None


def load_conversation_summaries(user_id):
    query = (
        "select=conversation_id,message,created_at"
        f"&user_id=eq.{quote(user_id, safe='')}"
        "&order=created_at.desc"
    )
    rows = supabase_request("GET", get_supabase_chat_history_table(), query=query)
    if not isinstance(rows, list):
        return []
    seen = set()
    counts = {}
    for row in rows:
        cid = str(row.get("conversation_id", "")).strip()
        if cid:
            counts[cid] = counts.get(cid, 0) + 1
    summaries = []
    for row in rows:
        cid = str(row.get("conversation_id", "")).strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        message = str(row.get("message", "")).strip()
        summaries.append(
            {
                "conversation_id": cid,
                "title": message[:32] + ("..." if len(message) > 32 else "") or "New Conversation",
                "created_at": str(row.get("created_at", "")).strip(),
                "message_count": counts.get(cid, 0),
            }
        )
    return summaries


def load_messages_for_conversation(user_id, conversation_id):
    query = (
        "select=sender,message,created_at"
        f"&user_id=eq.{quote(user_id, safe='')}"
        f"&conversation_id=eq.{quote(conversation_id, safe='')}"
        "&order=created_at.asc"
    )
    rows = supabase_request("GET", get_supabase_chat_history_table(), query=query)
    if not isinstance(rows, list):
        return []
    messages = []
    for row in rows:
        created_at = str(row.get("created_at", "")).strip()
        messages.append(
            {
                "role": "user" if str(row.get("sender", "")).strip().lower() == "user" else "assistant",
                "content": str(row.get("message", "")),
                "timestamp": created_at[11:16] if "T" in created_at else created_at[-5:],
            }
        )
    return messages


def save_message(role, content):
    user_id = get_user_id()
    conversation_id = st.session_state.get("current_conversation_id", "")
    if not user_id or not conversation_id:
        return
    payload = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "sender": "user" if role == "user" else "ai",
        "message": content,
        "created_at": datetime.now().isoformat(),
    }
    supabase_request("POST", get_supabase_chat_history_table(), payload=payload, extra_headers={"Prefer": "return=minimal"})


def delete_conversation(conversation_id):
    user_id = get_user_id()
    if not user_id:
        return
    query = f"user_id=eq.{quote(user_id, safe='')}&conversation_id=eq.{quote(conversation_id, safe='')}"
    supabase_request("DELETE", get_supabase_chat_history_table(), query=query, extra_headers={"Prefer": "return=minimal"})


def append_message(role, content, timestamp=None):
    st.session_state.messages.append({"role": role, "content": content, "timestamp": timestamp or datetime.now().strftime("%H:%M")})
    save_message(role, content)


def create_new_conversation():
    st.session_state.current_conversation_id = str(uuid4())
    st.session_state.messages = []
    st.session_state.conversation_loaded = True


def select_conversation(conversation_id):
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = load_messages_for_conversation(get_user_id(), conversation_id)
    st.session_state.conversation_loaded = True


def refresh_conversations():
    user_id = get_user_id()
    if user_id:
        st.session_state.conversation_summaries = load_conversation_summaries(user_id)


def initialize_session_state():
    ensure_auth_session_state()
    apply_query_auth()
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("total_tokens", 0)
    st.session_state.setdefault("total_interactions", 0)
    st.session_state.setdefault("session_start", datetime.now())
    st.session_state.setdefault("supabase_error", None)
    st.session_state.setdefault("pending_prompt", None)
    st.session_state.setdefault("is_generating", False)
    st.session_state.setdefault("sidebar_open", True)
    st.session_state.setdefault("selected_model", MODELS[0])
    st.session_state.setdefault("selected_domain", DOMAINS[0])
    user_id = get_user_id()
    if st.session_state.is_authenticated and user_id:
        refresh_conversations()
        if not st.session_state.current_conversation_id:
            if st.session_state.conversation_summaries:
                select_conversation(st.session_state.conversation_summaries[0]["conversation_id"])
            else:
                create_new_conversation()
        elif not st.session_state.conversation_loaded:
            st.session_state.messages = load_messages_for_conversation(user_id, st.session_state.current_conversation_id)
        st.session_state.conversation_loaded = True


def load_dashboard_css():
    css = (Path(__file__).with_name("dashboard.css")).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_chat_input_layout_css():
    if st.session_state.sidebar_open:
        left = "calc(25% + 1.6rem)"
        width = "calc(75% - 2.2rem)"
    else:
        left = "1.2rem"
        width = "calc(100% - 2.4rem)"
    st.markdown(
        f"""
        <style>
        [data-testid="stChatInput"] {{
            left: {left} !important;
            width: {width} !important;
            right: auto !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_login_redirect_notice():
    react_url = get_react_app_url().rstrip("/")
    st.markdown(
        f"""
        <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;padding:32px;background:#222831;">
            <div style="width:min(520px,92vw);padding:36px;border-radius:20px;background:rgba(34,40,49,.92);border:1px solid rgba(148,137,121,.28);box-shadow:0 28px 64px rgba(0,0,0,.35);text-align:center;">
                <div style="font-family:'Montserrat',sans-serif;font-size:28px;font-weight:700;color:#dfd0b8;margin-bottom:10px;">SecurCoach AI</div>
                <div style="font-family:'Poppins',sans-serif;font-size:18px;font-weight:600;color:#948979;margin-bottom:12px;">Login starts in React</div>
                <p style="font-size:14px;line-height:1.7;color:rgba(223,208,184,.72);margin:0 0 22px;">Sign in through the React app first. After successful login, you will be redirected here automatically.</p>
                <a href="{react_url}" style="display:inline-block;padding:14px 22px;border-radius:12px;text-decoration:none;background:#948979;color:#222831;font-weight:600;">Open React Login</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def generate_response(model, system_prompt, api_messages):
    api_key = get_gemini_api_key()
    if not api_key:
        return "Gemini is not configured. Add `GEMINI_API_KEY` to Streamlit secrets or your environment.", 0
    contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in api_messages]
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    for candidate_model in [model, "gemini-flash-latest", "gemini-2.0-flash"]:
        req = request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{candidate_model}:generateContent?key={api_key}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(2):
            try:
                with request.urlopen(req, timeout=60) as response:
                    data = json.loads(response.read().decode("utf-8"))
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                text = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip() or "Gemini returned an empty answer."
                return text, data.get("usageMetadata", {}).get("totalTokenCount", 0)
            except error.HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace")
                if exc.code == 503 and attempt == 0:
                    time.sleep(1.2)
                    continue
                if exc.code != 503:
                    return f"Gemini request failed ({exc.code}). {details}", 0
            except Exception as exc:
                return f"Gemini request failed. {exc}", 0
    return "Gemini is temporarily unavailable. Please try again in a few moments.", 0


def process_pending_prompt():
    pending = st.session_state.get("pending_prompt")
    if not pending:
        return
    reply, usage_tokens = generate_response(pending["model"], pending["system_prompt"], pending["api_messages"])
    append_message("assistant", reply, datetime.now().strftime("%H:%M"))
    st.session_state.total_tokens += usage_tokens
    st.session_state.total_interactions += 1
    st.session_state.pending_prompt = None
    st.session_state.is_generating = False
    refresh_conversations()
    st.rerun()


def render_topbar():
    return


def render_sidebar_panel():
    if not st.session_state.sidebar_open:
        if st.button(">", key="toggle_sidebar_closed", help="Open sidebar", use_container_width=True):
            st.session_state.sidebar_open = True
            st.rerun()
        return
    header_cols = st.columns([1, 5])
    with header_cols[0]:
        if st.button("<", key="toggle_sidebar_open", help="Collapse sidebar", use_container_width=True):
            st.session_state.sidebar_open = False
            st.rerun()
    with header_cols[1]:
        st.markdown("<div class='brand-row'><div class='brand-icon'>SC</div><div><div class='brand-name'>SecurCoach AI</div><div class='brand-sub'>Security Training</div></div></div>", unsafe_allow_html=True)
    if st.button("+ New Conversation", key="new_conv", use_container_width=True):
        create_new_conversation()
        refresh_conversations()
        st.rerun()
    st.markdown("<div class='history-label'>Chat History</div>", unsafe_allow_html=True)
    if st.session_state.conversation_summaries:
        for index, summary in enumerate(st.session_state.conversation_summaries):
            cid = summary["conversation_id"]
            created_at = summary["created_at"].replace("T", " ")[:16] if summary["created_at"] else ""
            cols = st.columns([6, 1])
            with cols[0]:
                if st.button(summary["title"], key=f"conv_{cid}", use_container_width=True, help=f"{created_at} · {summary['message_count']} messages"):
                    select_conversation(cid)
                    st.rerun()
                meta = f"{created_at} · {summary['message_count']} messages".strip(" ·")
                if meta:
                    st.markdown(f"<div class='conv-meta'>{html.escape(meta)}</div>", unsafe_allow_html=True)
            with cols[1]:
                if st.button("X", key=f"del_{cid}", help="Delete"):
                    delete_conversation(cid)
                    if cid == st.session_state.current_conversation_id:
                        st.session_state.current_conversation_id = ""
                        st.session_state.messages = []
                    refresh_conversations()
                    if not st.session_state.current_conversation_id:
                        if st.session_state.conversation_summaries:
                            select_conversation(st.session_state.conversation_summaries[0]["conversation_id"])
                        else:
                            create_new_conversation()
                    st.rerun()
    else:
        st.markdown("<div class='chat-rail-empty'>No past conversations yet.</div>", unsafe_allow_html=True)


def render_messages():
    if not st.session_state.messages:
        st.markdown(
            f"<div class='empty-wrap'><div class='empty-icon'>SC</div><div class='empty-title'>Start a conversation</div><div class='empty-hint'>Ask anything about <strong style='color:#dfd0b8;'>{html.escape(st.session_state.selected_domain)}</strong><br>or choose a topic to get started.</div></div>",
            unsafe_allow_html=True,
        )
        return
    for msg in st.session_state.messages:
        is_user = msg["role"] == "user"
        row_cls = "user-row" if is_user else "ai-row"
        av_cls = "user-av" if is_user else "ai-av"
        av_lbl = "ME" if is_user else "AI"
        bub_cls = "user-bubble" if is_user else "ai-bubble"
        safe = html.escape(msg["content"]).replace("\n", "<br>")
        st.markdown(
            f"<div class='msg-row {row_cls}'><div class='avatar {av_cls}'>{av_lbl}</div><div class='bubble {bub_cls}'>{safe}<div class='bubble-ts'>{html.escape(msg.get('timestamp', ''))}</div></div></div>",
            unsafe_allow_html=True,
        )


def render_loading_message():
    st.markdown(
        "<div class='msg-row ai-row'><div class='avatar ai-av'>AI</div><div class='bubble ai-bubble'>Thinking<span style=\"opacity:0.3;font-family:'JetBrains Mono',monospace;\"> |</span></div></div>",
        unsafe_allow_html=True,
    )


def handle_prompt(prompt):
    if not st.session_state.current_conversation_id:
        create_new_conversation()
    append_message("user", prompt, datetime.now().strftime("%H:%M"))
    refresh_conversations()
    st.session_state.pending_prompt = {
        "model": st.session_state.selected_model,
        "system_prompt": (
            f"You are SecurCoach AI, an expert in cybersecurity training focused on {st.session_state.selected_domain}. "
            "Be clear, accurate, and educational. Use examples and concrete analogies when helpful."
        ),
        "api_messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
    }
    st.session_state.is_generating = True
    st.rerun()


def render_dashboard():
    load_dashboard_css()
    render_chat_input_layout_css()
    if st.session_state.sidebar_open:
        col_sidebar, col_chat = st.columns([1, 3], gap="small")
    else:
        col_sidebar, col_chat = st.columns([0.001, 1], gap="small")
    with col_sidebar:
        render_sidebar_panel()
    with col_chat:
        if st.session_state.get("supabase_error"):
            st.caption("Supabase sync failed on the last request.")
        render_messages()
        if st.session_state.is_generating:
            render_loading_message()
            with st.spinner("SecurCoach AI is generating a response..."):
                process_pending_prompt()
            return
        prompt = st.chat_input("Ask a security question...", key="chat_input")
        if prompt:
            handle_prompt(prompt)


initialize_session_state()

if not st.session_state.is_authenticated:
    render_login_redirect_notice()
else:
    render_dashboard()
