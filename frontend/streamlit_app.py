import streamlit as st
import requests
import json

API_BASE = "http://localhost:8000/api/v1"
STREAM_URL = f"{API_BASE}/research/stream"
COSTS_URL  = f"{API_BASE}/costs"

st.set_page_config(
    page_title="Research Copilot",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0F0F1A; }
    header[data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background-color: #1A1A2E;
        border-right: 1px solid #2A2A4A;
    }
    .main .block-container { padding-top: 2rem; max-width: 950px; }

    .app-title {
        font-size: 1.8rem; font-weight: 700; color: #FFFFFF;
        margin: 0; letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.85rem; color: #6B6B8A;
        margin-bottom: 2rem; margin-top: 0.3rem;
    }
    .badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(108,99,255,0.15); color: #6C63FF;
        padding: 3px 10px; border-radius: 20px; font-size: 0.72rem;
        font-weight: 600; border: 1px solid rgba(108,99,255,0.3);
        margin-bottom: 1rem;
    }
    .confidence-container {
        background: #1E2A45; border-radius: 16px;
        padding: 1.2rem 1.5rem; border: 1px solid #2A2A4A; margin-bottom: 1rem;
    }
    .confidence-label {
        font-size: 0.72rem; color: #6B6B8A; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;
    }
    .confidence-value { font-size: 2rem; font-weight: 800; color: #6C63FF; margin-bottom: 0.5rem; }
    .confidence-bar-bg { background: #2A2A4A; border-radius: 99px; height: 6px; width: 100%; }
    .confidence-bar-fill { background: linear-gradient(90deg,#6C63FF,#A78BFA); border-radius: 99px; height: 6px; }

    .answer-card {
        background: #1A1A2E; border-radius: 16px; padding: 1.5rem;
        border: 1px solid #2A2A4A; border-left: 4px solid #6C63FF;
        color: #D0D0E8; font-size: 0.95rem; line-height: 1.7; margin-bottom: 1.5rem;
    }
    .source-card {
        background: #16213E; border-radius: 12px; padding: 1rem 1.2rem;
        border: 1px solid #3A3A6A; margin-bottom: 0.8rem;
    }
    .source-card:hover { border-color: #6C63FF; }
    .source-title { font-size: 0.88rem; font-weight: 600; color: #FFFFFF; margin-bottom: 0.3rem; }
    .source-content { font-size: 0.8rem; color: #9090B8; line-height: 1.5; margin-bottom: 0.5rem; }
    .source-url { font-size: 0.72rem; color: #A78BFA; }
    .source-score { font-size: 0.72rem; color: #6B6B8A; }

    .variant-pill {
        display: inline-block; background: rgba(167,139,250,0.12);
        color: #A78BFA; border: 1px solid rgba(167,139,250,0.3);
        border-radius: 20px; padding: 3px 12px; font-size: 0.75rem;
        margin: 3px 4px 3px 0;
    }
    .section-header {
        font-size: 0.72rem; font-weight: 700; color: #6B6B8A;
        text-transform: uppercase; letter-spacing: 0.1em; margin: 1.5rem 0 0.8rem 0;
    }
    .cost-card {
        background: #12192B; border-radius: 12px; padding: 1rem 1.2rem;
        border: 1px solid #2A2A4A; text-align: center;
    }
    .cost-value { font-size: 1.4rem; font-weight: 800; color: #6C63FF; }
    .cost-label { font-size: 0.7rem; color: #6B6B8A; text-transform: uppercase; letter-spacing: 0.08em; }

    .stTextInput input {
        background: #1A1A2E !important; border: 1.5px solid #2A2A4A !important;
        border-radius: 12px !important; color: #FFFFFF !important;
        font-size: 0.95rem !important; padding: 0.8rem 1rem !important;
    }
    .stTextInput input:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 3px rgba(108,99,255,0.15) !important;
    }
    .stTextInput input::placeholder { color: #4A4A6A !important; }
    .stButton button {
        background: linear-gradient(135deg,#6C63FF,#5A52E0) !important;
        color: white !important; border: none !important;
        border-radius: 12px !important; padding: 0.7rem 2rem !important;
        font-weight: 600 !important; font-size: 0.9rem !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(108,99,255,0.4) !important;
    }
    [data-testid="stSidebar"] * { color: #A0A0C0 !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔬 Research Copilot")
    st.markdown('<span class="badge">● Powered by Groq + Tavily</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Search Settings**")
    max_results = st.slider("Number of sources", 1, 10, 5)
    use_web_search = st.toggle("Use web search", value=True)

    st.markdown("---")
    st.markdown("**How it works**")
    st.caption("1. LLM expands your query × 3")
    st.caption("2. Searches all variants via Tavily")
    st.caption("3. Fuses results with RRF ranking")
    st.caption("4. Streams grounded answer with [citations]")
    st.caption("5. Scores confidence & tracks cost")

    st.markdown("---")
    st.markdown("**💰 Cost Dashboard**")
    if st.button("Refresh Stats", use_container_width=True):
        st.session_state["refresh_costs"] = True

    try:
        cost_data = requests.get(COSTS_URL, timeout=5).json()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="cost-card">
                <div class="cost-value">${cost_data['total_cost_usd']:.4f}</div>
                <div class="cost-label">Total Cost</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="cost-card">
                <div class="cost-value">{cost_data['total_queries']}</div>
                <div class="cost-label">Queries</div>
            </div>""", unsafe_allow_html=True)
        st.caption(f"Tokens used: {cost_data['total_tokens']:,}")
    except Exception:
        st.caption("Start the backend to see stats.")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-title">Research Copilot</div>
<div class="app-subtitle">Multi-query expansion · RRF ranking · Streaming answers · Inline citations</div>
""", unsafe_allow_html=True)

# ── Input ────────────────────────────────────────────────────────────────────
query = st.text_input(
    "Query",
    placeholder="What is retrieval-augmented generation?",
    label_visibility="collapsed"
)
search = st.button("Search →", use_container_width=True)

# ── Results ──────────────────────────────────────────────────────────────────
if search and query:
    sources_data    = []
    query_variants  = []
    answer_chunks   = []
    confidence      = None
    cost_usd        = None
    tokens_used     = None
    model_used      = None

    answer_placeholder    = st.empty()
    sources_placeholder   = st.empty()
    meta_placeholder      = st.empty()
    variants_placeholder  = st.empty()

    with st.spinner("Expanding query and searching..."):
        try:
            with requests.post(
                STREAM_URL,
                json={"query": query, "max_results": max_results, "use_web_search": use_web_search},
                stream=True,
                timeout=60
            ) as resp:
                if resp.status_code != 200:
                    st.error(f"Error {resp.status_code}: {resp.text}")
                else:
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        line = line.decode("utf-8")
                        if not line.startswith("data: "):
                            continue
                        payload = json.loads(line[6:])
                        t = payload.get("type")

                        if t == "sources":
                            sources_data   = payload.get("sources", [])
                            query_variants = payload.get("variants", [])

                            pills = "".join(
                                f'<span class="variant-pill">🔍 {v}</span>'
                                for v in query_variants
                            )
                            variants_placeholder.markdown(
                                f'<div class="section-header">Query Variants</div>{pills}',
                                unsafe_allow_html=True
                            )

                        elif t == "chunk":
                            answer_chunks.append(payload.get("content", ""))
                            partial = "".join(answer_chunks)
                            answer_placeholder.markdown(
                                f'<div class="section-header">Answer</div>'
                                f'<div class="answer-card">{partial}▌</div>',
                                unsafe_allow_html=True
                            )

                        elif t == "meta":
                            confidence = payload.get("confidence")
                            cost_usd   = payload.get("cost_usd")
                            tokens_used = payload.get("tokens")
                            model_used  = payload.get("model")

                        elif t == "error":
                            st.error(payload.get("message"))

        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

    # ── Final render ──────────────────────────────────────────────────────────
    if answer_chunks:
        final_answer = "".join(answer_chunks)
        answer_placeholder.markdown(
            f'<div class="section-header">Answer</div>'
            f'<div class="answer-card">{final_answer}</div>',
            unsafe_allow_html=True
        )

    if confidence is not None:
        fill = int(confidence * 100)
        meta_placeholder.markdown(f"""
        <div class="section-header">Confidence Score</div>
        <div class="confidence-container">
            <div class="confidence-label">How well sources support this answer</div>
            <div class="confidence-value">{confidence:.0%}</div>
            <div class="confidence-bar-bg">
                <div class="confidence-bar-fill" style="width:{fill}%"></div>
            </div>
        </div>
        <div style="font-size:0.75rem;color:#6B6B8A;margin-top:0.3rem;">
            Model: {model_used} &nbsp;·&nbsp; Tokens: {tokens_used:,} &nbsp;·&nbsp; Cost: ${cost_usd:.5f}
        </div>
        """, unsafe_allow_html=True)

    if sources_data:
        sources_html = f'<div class="section-header">Sources — {len(sources_data)} retrieved</div>'
        for i, source in enumerate(sources_data, 1):
            relevance = source.get("relevance_score", 0)
            content   = source.get("content", "")[:180].replace("#", "").replace("*", "").strip()
            url       = source.get("url", "")[:60]
            title     = source.get("title", "Untitled")
            sources_html += f"""
            <div class="source-card">
                <div class="source-title">[{i}] {title}</div>
                <div class="source-content">{content}...</div>
                <div>
                    <span class="source-url">🔗 {url}</span>
                    <span class="source-score" style="margin-left:1rem;">RRF: {relevance:.4f}</span>
                </div>
            </div>"""
        sources_placeholder.markdown(sources_html, unsafe_allow_html=True)

elif search and not query:
    st.warning("Please enter a question first.")
