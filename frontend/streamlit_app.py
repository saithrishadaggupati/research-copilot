import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000/api/v1/research"

st.set_page_config(
    page_title="Research Copilot",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Base - Dark Theme */
    .stApp { background-color: #0F0F1A; }
    
    /* Hide default header */
    header[data-testid="stHeader"] { background: transparent; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1A1A2E;
        border-right: 1px solid #2A2A4A;
    }
    
    /* Main container */
    .main .block-container { 
        padding-top: 2rem; 
        max-width: 950px;
    }
    
    /* App title */
    .app-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.85rem;
        color: #6B6B8A;
        margin-bottom: 2rem;
        margin-top: 0.3rem;
    }

    /* Status badge */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: rgba(108, 99, 255, 0.15);
        color: #6C63FF;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid rgba(108, 99, 255, 0.3);
        margin-bottom: 1rem;
    }

    /* Confidence bar */
    .confidence-container {
        background: #1E2A45;
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #2A2A4A;
        margin-bottom: 1rem;
    }
    .confidence-label {
        font-size: 0.72rem;
        color: #6B6B8A;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
    }
    .confidence-value {
        font-size: 2rem;
        font-weight: 800;
        color: #6C63FF;
        margin-bottom: 0.5rem;
    }
    .confidence-bar-bg {
        background: #2A2A4A;
        border-radius: 99px;
        height: 6px;
        width: 100%;
    }
    .confidence-bar-fill {
        background: linear-gradient(90deg, #6C63FF, #A78BFA);
        border-radius: 99px;
        height: 6px;
    }

    /* Answer card */
    .answer-card {
        background: #1A1A2E;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #2A2A4A;
        border-left: 4px solid #6C63FF;
        color: #D0D0E8;
        font-size: 0.95rem;
        line-height: 1.7;
        margin-bottom: 1.5rem;
    }

    /* Source card */
    .source-card {
        background: #16213E;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        border: 1px solid #3A3A6A;
        margin-bottom: 0.8rem;
        transition: border-color 0.2s;
    }
    .source-card:hover { border-color: #6C63FF; }
    .source-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 0.3rem;
    }
    .source-content {
        font-size: 0.8rem;
        color: #9090B8;
        line-height: 1.5;
        margin-bottom: 0.5rem;
    }
    .source-url {
        font-size: 0.72rem;
        color: #A78BFA;
    }
    .source-score {
        font-size: 0.72rem;
        color: #6B6B8A;
    }

    /* Section header */
    .section-header {
        font-size: 0.72rem;
        font-weight: 700;
        color: #6B6B8A;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1.5rem 0 0.8rem 0;
    }

    /* Input */
    .stTextInput input {
        background: #1A1A2E !important;
        border: 1.5px solid #2A2A4A !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
        font-size: 0.95rem !important;
        padding: 0.8rem 1rem !important;
    }
    .stTextInput input:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 3px rgba(108,99,255,0.15) !important;
    }
    .stTextInput input::placeholder { color: #4A4A6A !important; }

    /* Button */
    .stButton button {
        background: linear-gradient(135deg, #6C63FF, #5A52E0) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.7rem 2rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(108,99,255,0.4) !important;
    }

    /* Slider */
    .stSlider { padding: 0 !important; }

    /* Sidebar text */
    [data-testid="stSidebar"] * { color: #A0A0C0 !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔬 Research Copilot")
    st.markdown('<span class="badge">● Powered by Groq + Tavily</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Search Settings**")

    max_results = st.slider("Number of sources", 1, 10, 5)
    use_web_search = st.toggle("Use web search", value=True)

    st.markdown("---")
    st.markdown("**How it works**")
    st.caption("1. Searches the web in real time")
    st.caption("2. Retrieves top sources as context")
    st.caption("3. Generates a grounded answer")
    st.caption("4. Scores confidence based on source coverage")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-title">Research Copilot</div>
<div class="app-subtitle">Real-time web search · Grounded answers · Confidence scoring</div>
""", unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────────
query = st.text_input(
    "Query",
    placeholder="What is retrieval-augmented generation?",
    label_visibility="collapsed"
)

search = st.button("Search →", use_container_width=True)

# ── Results ───────────────────────────────────────────────────────────────────
if search and query:
    with st.spinner("Searching and analyzing..."):
        try:
            response = requests.post(API_URL, json={
                "query": query,
                "max_results": max_results,
                "use_web_search": use_web_search
            }, timeout=30)

            if response.status_code != 200:
                st.error(f"Error {response.status_code}: {response.text}")
            else:
                data = response.json()
                score = data.get("confidence_score", 0)
                fill_width = int(score * 100)

                # Confidence
                st.markdown('<div class="section-header">Confidence Score</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="confidence-container">
                    <div class="confidence-label">How well sources support this answer</div>
                    <div class="confidence-value">{score:.0%}</div>
                    <div class="confidence-bar-bg">
                        <div class="confidence-bar-fill" style="width:{fill_width}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Answer
                st.markdown('<div class="section-header">Answer</div>', unsafe_allow_html=True)
                import re
                answer_text = data.get("answer", "No answer returned")
                answer_clean = re.sub(r'Source \d+: https?://\S+,?\s*', '', answer_text).strip()
                st.markdown(f'<div class="answer-card">{answer_clean}</div>', unsafe_allow_html=True)

                # Sources
                sources = data.get("sources", [])
                if sources:
                    st.markdown(f'<div class="section-header">Sources — {len(sources)} retrieved</div>', unsafe_allow_html=True)
                    for i, source in enumerate(sources, 1):
                        relevance = source.get("relevance_score", 0)
                        st.markdown(f"""
                        <div class="source-card">
                            <div class="source-title">{i}. {source.get("title", "Untitled")}</div>
                            <div class="source-content">{source.get("content", "")[:180].replace("#", "").replace("*", "").strip()}...</div>
                            <div class="source-meta">
                                <span class="source-url">🔗 {source.get("url", "")[:60]}</span>
                                <span class="source-score">Relevance: {relevance:.2f}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # Model info
                st.markdown(f'<div class="section-header" style="margin-top:2rem">Model: {data.get("model_used", "")}</div>', unsafe_allow_html=True)

        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

elif search and not query:
    st.warning("Please enter a question first.")