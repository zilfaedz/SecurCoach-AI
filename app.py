import streamlit as st
from datetime import datetime
from pathlib import Path

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
    "Quiz me": "Sure — here is a 5-question mini quiz on your selected domain. I’ll grade each answer and give hints before revealing the final explanation.",
    "Explain a concept": "**Symmetric encryption** uses one shared key for both locking and unlocking information, while **asymmetric encryption** uses a public key and a private key. One is faster for bulk data, while the other is useful for secure exchange and identity verification.",
    "Run a scenario": "Scenario: A help desk employee reports repeated login failures followed by a successful login from a new location. Your first step should be to verify whether this activity is legitimate, review the account logs, and assess whether the account may be compromised.",
}

st.sidebar.markdown("## 🛡️   SecurCoach AI")
st.sidebar.caption("Interactive cybersecurity study partner")

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
    elif "explain" in lowered or "difference" in lowered:
        st.session_state.quiz_started = False
        reply = sample_outputs["Explain a concept"]
    elif "scenario" in lowered or "incident" in lowered:
        st.session_state.quiz_started = False
        reply = sample_outputs["Run a scenario"]
    elif "hack" in lowered or "bypass" in lowered or "exploit" in lowered:
        reply = "I am an educational tool. I cannot provide instructions for unauthorized access or unethical hacking."
    else:
        reply = f"You’re currently in **{selected_domain}**. I can quiz you, explain a concept, or run a basic cybersecurity scenario based on this domain."

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

st.markdown("---")
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(
        "<div class='foot-note'>Draft prepared for demo purposes — suitable for initial proposal presentation and iterative refinement next week.</div>",
        unsafe_allow_html=True,
    )
with col2:
    st.caption(f"Last opened: {datetime.now().strftime('%b %d, %Y %I:%M %p')}")
