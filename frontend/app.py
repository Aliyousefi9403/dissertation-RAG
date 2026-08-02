from pathlib import Path
from typing import Any

import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/chat"
HEALTH_URL = "http://127.0.0.1:8000/health"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = PROJECT_ROOT / "frontend" / "assets" / "aegisrag-logo.png"


st.set_page_config(
    page_title="AegisRAG",
    page_icon=str(LOGO_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
    --bg: #06080d;
    --panel: rgba(14, 20, 30, 0.72);
    --panel-strong: rgba(13, 18, 27, 0.92);
    --border: rgba(133, 174, 214, 0.16);
    --border-hover: rgba(60, 203, 255, 0.50);
    --text: #f4f7fb;
    --muted: #8f9bad;
    --cyan: #3ccbff;
    --cyan-soft: rgba(60, 203, 255, 0.10);
}

/* Animated background */
.stApp {
    background:
        radial-gradient(
            circle at 72% -10%,
            rgba(35, 160, 255, 0.16),
            transparent 30%
        ),
        radial-gradient(
            circle at 18% 80%,
            rgba(26, 90, 180, 0.08),
            transparent 34%
        ),
        linear-gradient(
            180deg,
            #05070b 0%,
            #070a10 48%,
            #05070b 100%
        );
    background-size: 130% 130%;
    animation: ambientGlow 15s ease-in-out infinite alternate;
}

@keyframes ambientGlow {
    0% {
        background-position: 0% 0%;
    }

    100% {
        background-position: 100% 80%;
    }
}

/* Soft moving grid */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: 0.14;
    background-image:
        linear-gradient(
            rgba(82, 133, 180, 0.06) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(82, 133, 180, 0.05) 1px,
            transparent 1px
        );
    background-size: 54px 54px;
    mask-image: linear-gradient(
        to bottom,
        rgba(0, 0, 0, 0.85),
        transparent 82%
    );
    animation: gridDrift 28s linear infinite;
}

@keyframes gridDrift {
    from {
        transform: translateY(0);
    }

    to {
        transform: translateY(54px);
    }
}

/* Sidebar glass */
[data-testid="stSidebar"] {
    background: rgba(7, 11, 17, 0.84);
    border-right: 1px solid var(--border);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
}

[data-testid="stSidebarContent"] {
    padding-top: 1.2rem;
}

/* Top bar */
[data-testid="stHeader"] {
    background: rgba(5, 8, 13, 0.58);
    border-bottom: 1px solid rgba(110, 160, 205, 0.08);
    backdrop-filter: blur(22px);
    -webkit-backdrop-filter: blur(22px);
}

/* Main width */
.block-container {
    max-width: 1040px;
    padding-top: 1.7rem;
    padding-bottom: 8rem;
}

/* Hero */
.hero {
    text-align: center;
    margin: 0 auto 2.4rem;
    animation: heroEnter 0.75s ease-out both;
}

@keyframes heroEnter {
    from {
        opacity: 0;
        transform: translateY(14px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.hero img {
    filter:
        drop-shadow(0 0 20px rgba(45, 195, 255, 0.24))
        drop-shadow(0 20px 45px rgba(0, 0, 0, 0.4));
    animation: logoFloat 5s ease-in-out infinite;
}

@keyframes logoFloat {
    0%, 100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-7px);
    }
}

.hero-title {
    color: var(--text);
    font-size: 3.1rem;
    font-weight: 760;
    letter-spacing: -0.055em;
    margin-top: 0.25rem;
    text-shadow: 0 0 38px rgba(75, 190, 255, 0.11);
}

.hero-subtitle {
    color: var(--muted);
    font-size: 1rem;
    margin-top: 0.45rem;
    letter-spacing: -0.01em;
}

.mode-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 1rem;
    padding: 0.48rem 0.85rem;
    border-radius: 999px;
    border: 1px solid rgba(60, 203, 255, 0.22);
    background: rgba(12, 20, 30, 0.62);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        0 10px 30px rgba(0, 0, 0, 0.22);
    color: #99e5ff;
    font-size: 0.78rem;
    font-weight: 670;
    backdrop-filter: blur(14px);
}

/* Chat message glass cards */
[data-testid="stChatMessage"] {
    background:
        linear-gradient(
            145deg,
            rgba(20, 27, 39, 0.78),
            rgba(10, 15, 23, 0.72)
        );
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.05rem 1.2rem;
    margin-bottom: 0.9rem;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.025),
        0 18px 50px rgba(0, 0, 0, 0.26);
    backdrop-filter: blur(22px);
    -webkit-backdrop-filter: blur(22px);
    animation: messageEnter 0.38s ease-out both;
}

@keyframes messageEnter {
    from {
        opacity: 0;
        transform: translateY(9px) scale(0.992);
    }

    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

[data-testid="stChatMessage"]:hover {
    border-color: rgba(60, 203, 255, 0.25);
}

/* Chat input: ChatGPT-style floating bar */
[data-testid="stChatInput"] {
    background: rgba(14, 20, 30, 0.86);
    border: 1px solid rgba(120, 165, 205, 0.22);
    border-radius: 23px;
    box-shadow:
        0 24px 70px rgba(0, 0, 0, 0.52),
        inset 0 1px 0 rgba(255, 255, 255, 0.035);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    transition:
        border-color 180ms ease,
        box-shadow 180ms ease,
        transform 180ms ease;
}

[data-testid="stChatInput"]:focus-within {
    border-color: rgba(60, 203, 255, 0.62);
    box-shadow:
        0 0 0 3px rgba(60, 203, 255, 0.08),
        0 26px 80px rgba(0, 0, 0, 0.55);
    transform: translateY(-1px);
}

/* Evidence panels */
[data-testid="stExpander"] {
    background: rgba(8, 13, 20, 0.68);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
    backdrop-filter: blur(18px);
}

[data-testid="stExpander"]:hover {
    border-color: rgba(60, 203, 255, 0.28);
}

/* Sidebar cards */
.status-card {
    padding: 0.95rem 1rem;
    border-radius: 17px;
    border: 1px solid var(--border);
    background:
        linear-gradient(
            145deg,
            rgba(16, 23, 34, 0.68),
            rgba(8, 13, 20, 0.62)
        );
    margin-bottom: 0.72rem;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.025),
        0 12px 34px rgba(0, 0, 0, 0.17);
    backdrop-filter: blur(18px);
    transition:
        transform 180ms ease,
        border-color 180ms ease;
}

.status-card:hover {
    transform: translateY(-2px);
    border-color: rgba(60, 203, 255, 0.27);
}

.status-label {
    color: #718096;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.11em;
    font-weight: 700;
}

.status-value {
    color: var(--text);
    font-size: 0.93rem;
    font-weight: 650;
    margin-top: 0.3rem;
}

.online-dot {
    color: #4ade80;
    text-shadow: 0 0 12px rgba(74, 222, 128, 0.44);
}

/* Buttons */
.stButton > button {
    width: 100%;
    min-height: 2.65rem;
    border-radius: 14px;
    border: 1px solid var(--border);
    background: rgba(15, 22, 32, 0.72);
    color: #dfe9f4;
    font-weight: 640;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.025);
    transition:
        transform 170ms ease,
        border-color 170ms ease,
        background 170ms ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(60, 203, 255, 0.52);
    background: rgba(20, 31, 45, 0.86);
    color: #bdeeff;
}

/* Code blocks */
[data-testid="stCode"] {
    border-radius: 13px;
    border: 1px solid rgba(120, 165, 205, 0.12);
}

/* Hide Streamlit chrome */
#MainMenu,
footer,
[data-testid="stToolbar"] {
    visibility: hidden;
}

/* Better scrollbar */
::-webkit-scrollbar {
    width: 9px;
}

::-webkit-scrollbar-track {
    background: #070a0f;
}

::-webkit-scrollbar-thumb {
    background: #202b39;
    border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
    background: #2c3d50;
}
    </style>
    """,
    unsafe_allow_html=True,
)


def call_rag_api(question: str) -> dict[str, Any]:
    try:
        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()

    except requests.ConnectionError as error:
        raise RuntimeError(
            "The AegisRAG backend is not running."
        ) from error

    except requests.Timeout as error:
        raise RuntimeError(
            "The request timed out."
        ) from error

    except requests.HTTPError as error:
        raise RuntimeError(
            f"The backend returned an error: {response.text}"
        ) from error


def display_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        return

    with st.expander(f"Retrieved evidence · {len(sources)} sources"):
        for source in sources:
            source_name = Path(source["source"]).name
            score = float(source["score"])

            st.markdown(
                f"**Source {source['source_number']} — {source_name}**"
            )
            st.caption(f"Similarity score: {score:.4f}")
            st.code(source["content"], language="markdown")
            st.divider()


if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.image(str(LOGO_PATH), width=120)

    st.markdown("## AegisRAG")
    st.caption("Secure knowledge intelligence")

    try:
        health_response = requests.get(
            HEALTH_URL,
            timeout=5,
        )
        backend_online = health_response.ok
    except requests.RequestException:
        backend_online = False

    backend_status = (
        '<span class="online-dot">● Online</span>'
        if backend_online
        else "● Offline"
    )

    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-label">System status</div>
            <div class="status-value">{backend_status}</div>
        </div>

        <div class="status-card">
            <div class="status-label">Research mode</div>
            <div class="status-value">Clean baseline</div>
        </div>

        <div class="status-card">
            <div class="status-label">Language model</div>
            <div class="status-value">GPT-4o-mini</div>
        </div>

        <div class="status-card">
            <div class="status-label">Vector store</div>
            <div class="status-value">Qdrant</div>
        </div>

        <div class="status-card">
            <div class="status-label">Embedding model</div>
            <div class="status-value">all-MiniLM-L6-v2</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()


st.markdown(
    f"""
    <div class="hero">
        <img
            src="data:image/png;base64,{__import__('base64').b64encode(
                LOGO_PATH.read_bytes()
            ).decode()}"
            width="150"
        />
        <div class="hero-title">AegisRAG</div>
        <div class="hero-subtitle">
            Evidence-grounded cybersecurity intelligence.
        </div>
        <div class="mode-badge">
            Baseline Environment · Integrity Monitoring Offline
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            display_sources(message.get("sources", []))


question = st.chat_input(
    "Ask AegisRAG a cybersecurity question..."
)

if question:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving and validating evidence..."):
            try:
                result = call_rag_api(question)
                answer = result["answer"]
                sources = result.get("sources", [])

                st.markdown(answer)
                display_sources(sources)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )

            except RuntimeError as error:
                st.error(str(error))