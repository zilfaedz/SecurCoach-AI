import json
import os
from datetime import datetime
from pathlib import Path
from urllib import error, request, parse


import streamlit as st

st.set_page_config(
    page_title="SecurCoach AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css(file_name: str) -> None:
    css_path = Path(__file__).parent / file_name
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


load_css("styles.css")

DEFAULT_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash",
]


def get_gemini_api_key() -> str:
    secrets = getattr(st, "secrets", {})
    return secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")


def get_gemini_models() -> list[str]:
    secrets = getattr(st, "secrets", {})
    configured = secrets.get("GEMINI_MODEL") or os.getenv("GEMINI_MODEL", "")
    if configured:
        return [configured]
    return DEFAULT_GEMINI_MODELS


def get_supabase_config() -> dict[str, str]:
    secrets = getattr(st, "secrets", {})
    return {
        "url": secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL", ""),
        "key": secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY", ""),
    }


def log_chat_to_supabase(user_message: str, assistant_reply: str, domain: str) -> None:
    config = get_supabase_config()
    if not config["url"] or not config["key"] or "your_supabase" in config["url"]:
        return

    # Using Supabase REST API (PostgREST)
    table_url = f"{config['url'].rstrip('/')}/rest/v1/chat_history"
    payload = {
        "timestamp": datetime.now().isoformat(),
        "domain": domain,
        "user_message": user_message,
        "assistant_reply": assistant_reply,
    }

    req = request.Request(
        table_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "apikey": config["key"],
            "Authorization": f"Bearer {config['key']}",
            "Prefer": "return=minimal",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=10) as _:
            pass
    except Exception as e:
        # Silently fail or log to console for debugging
        print(f"Supabase logging failed: {e}")


def build_system_prompt(domain: str) -> str:
    return (
        "You are SecurCoach AI, a cybersecurity study partner for students. "
        f"The active study domain is {domain}. "
        "Keep answers concise, educational, and safe. "
        "Refuse instructions that would enable unauthorized access, malware, exploitation, or evasion. "
        "When possible, steer the user toward defensive learning, incident response, risk reduction, or exam preparation."
    )


def generate_gemini_reply(user_message: str, domain: str) -> str:
    api_key = get_gemini_api_key()
    if not api_key:
        return (
            "Gemini is not configured yet. Add `GEMINI_API_KEY` to Streamlit secrets or your environment, "
            "then rerun the app."
        )

    payload = {
        "system_instruction": {"parts": [{"text": build_system_prompt(domain)}]},
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 500,
        },
    }

    last_error = "Gemini returned no answer."
    for model_name in get_gemini_models():
        req = request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            if exc.code == 404:
                last_error = f"Model `{model_name}` is unavailable. Trying another model."
                continue
            return f"Gemini request failed ({exc.code}) on `{model_name}`. {details}"
        except Exception as exc:
            return f"Gemini request failed. {exc}"

        candidates = data.get("candidates", [])
        if not candidates:
            last_error = f"Model `{model_name}` returned no answer."
            continue

        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        if text_parts:
            return "\n".join(text_parts).strip()

        last_error = f"Model `{model_name}` returned an empty answer."

    return last_error


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome to **SecurCoach AI**. Choose a study domain, then ask for a quiz, a concept explanation, or a scenario simulation.",
        }
    ]

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None

quiz_bank = {
    "Network Security": {
        "question": "What is the primary function of a firewall?",
        "options": [
            "A) Encrypt all stored data",
            "B) Filter and control network traffic",
            "C) Manage user passwords",
            "D) Physically secure servers",
        ],
        "answer": "B",
        "hint": "Think about which control sits between trusted and untrusted networks.",
        "explanation": "A **firewall** primarily monitors and filters incoming and outgoing **network traffic** based on defined security rules.",
    },
    "Security Operations": {
        "question": "You detect unusual outbound traffic on port 4444 from a workstation. What is the best first step?",
        "options": [
            "A) Shut down the whole company network immediately",
            "B) Ignore it unless users complain",
            "C) Validate the alert and isolate the affected host if needed",
            "D) Delete all system logs",
        ],
        "answer": "C",
        "hint": "In incident response, confirm what is happening before expanding your actions.",
        "explanation": "A strong first step is to **validate the alert**, gather context, and **contain the affected system** if the activity appears malicious.",
    },
    "Access Controls": {
        "question": "Which principle gives users only the access needed to do their job?",
        "options": [
            "A) Defense in Depth",
            "B) Least Privilege",
            "C) Business Continuity",
            "D) Nonrepudiation",
        ],
        "answer": "B",
        "hint": "It reduces unnecessary permissions and limits damage if an account is compromised.",
        "explanation": "**Least Privilege** means giving each user, process, or system only the minimum permissions required to perform its role.",
    },
    "General Review": {
        "question": "Which part of the CIA Triad focuses on making sure data is accurate and not improperly altered?",
        "options": [
            "A) Confidentiality",
            "B) Accessibility",
            "C) Integrity",
            "D) Authorization",
        ],
        "answer": "C",
        "hint": "Think about trustworthiness and correctness of information.",
        "explanation": "**Integrity** ensures data remains accurate, complete, and protected from unauthorized modification.",
    },
}

sample_outputs = {
    "Quiz me": "Sure - here is a 5-question mini quiz on your selected domain. I will grade each answer and give hints before revealing the final explanation.",
    "Explain a concept": "**Symmetric encryption** uses one shared key for both locking and unlocking information, while **asymmetric encryption** uses a public key and a private key. One is faster for bulk data, while the other is useful for secure exchange and identity verification.",
    "Run a scenario": "Scenario: A help desk employee reports repeated login failures followed by a successful login from a new location. Your first step should be to verify whether this activity is legitimate, review the account logs, and assess whether the account may be compromised.",
}

st.sidebar.markdown("## 🛡️   SecurCoach AI")
st.sidebar.caption("Interactive cybersecurity study partner")
st.sidebar.caption("Gemini status: connected" if get_gemini_api_key() else "Gemini status: missing API key")

selected_domain = st.sidebar.selectbox(
    "Select Study Domain",
    ["Network Security", "Security Operations", "Access Controls", "General Review"],
)

uploaded_file = st.sidebar.file_uploader(
    "Upload PDF study guides or syllabus",
    type=["pdf"],
    help="Initial draft only: upload is for UI demonstration and future document-grounded study support.",
)

if uploaded_file is not None:
    st.session_state.uploaded_file_name = uploaded_file.name

st.sidebar.markdown("---")

st.markdown("<div class='section-title'>Quick study actions</div>", unsafe_allow_html=True)
q1, q2, q3 = st.columns(3)

with q1:
    if st.button("📝 Start quiz", use_container_width=True):
        st.session_state.quiz_started = True
        st.session_state.messages.append(
            {
                "role": "user",
                "content": f"Quiz me on {selected_domain}.",
            }
        )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": sample_outputs["Quiz me"],
            }
        )

with q2:
    if st.button("📘 Explain concept", use_container_width=True):
        st.session_state.quiz_started = False
        st.session_state.messages.append(
            {
                "role": "user",
                "content": "Explain the difference between symmetric and asymmetric encryption like I'm 5.",
            }
        )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": sample_outputs["Explain a concept"],
            }
        )

with q3:
    if st.button("🚨 Run scenario", use_container_width=True):
        st.session_state.quiz_started = False
        st.session_state.messages.append(
            {
                "role": "user",
                "content": "Give me a basic incident response scenario.",
            }
        )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": sample_outputs["Run a scenario"],
            }
        )

st.markdown("<div class='section-title'>Study chat</div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.quiz_started:
    current_quiz = quiz_bank[selected_domain]
    st.markdown(
        f"""
        <div class="quiz-card">
            <div class="quiz-label">QUIZ QUESTION</div>
            <div class="quiz-question">{current_quiz['question']}</div>
            <div class="quiz-option">{current_quiz['options'][0]}</div>
            <div class="quiz-option">{current_quiz['options'][1]}</div>
            <div class="quiz-option">{current_quiz['options'][2]}</div>
            <div class="quiz-option">{current_quiz['options'][3]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_answer = st.radio(
        "Select your answer:",
        ["A", "B", "C", "D"],
        horizontal=True,
        key=f"quiz_answer_{selected_domain}",
    )

    if st.button("Check answer", use_container_width=False):
        if selected_answer == current_quiz["answer"]:
            st.success(f"Correct. {current_quiz['explanation']}")
        else:
            st.warning(f"Hint: {current_quiz['hint']}")
            st.info(f"Correct answer: {current_quiz['answer']}. {current_quiz['explanation']}")

user_input = st.chat_input("Type your answer or question here...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    lowered = user_input.lower()
    if "quiz" in lowered:
        st.session_state.quiz_started = True
        reply = f"Absolutely. I can quiz you on **{selected_domain}** and guide you with hints before revealing the answer."
    elif "hack" in lowered or "bypass" in lowered or "exploit" in lowered:
        reply = "I am an educational tool. I cannot provide instructions for unauthorized access or unethical hacking."
    else:
        st.session_state.quiz_started = False
        with st.spinner("Thinking..."):
            reply = generate_gemini_reply(user_input, selected_domain)
            log_chat_to_supabase(user_input, reply, selected_domain)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

st.markdown("---")
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(
        "<div class='foot-note'>Draft prepared for demo purposes - suitable for initial proposal presentation and iterative refinement next week.</div>",
        unsafe_allow_html=True,
    )
with col2:
    st.caption(f"Last opened: {datetime.now().strftime('%b %d, %Y %I:%M %p')}")
