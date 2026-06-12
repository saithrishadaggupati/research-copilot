import streamlit as st
import requests

API_URL = "http://localhost:8000/api/v1/research"

st.set_page_config(
    page_title="Research Copilot",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Research Copilot")
st.caption("Ask anything — powered by web search + AI")

with st.form("research_form"):
    query = st.text_input(
        "Your Question",
        placeholder="What is RAG in AI systems?"
    )
    col1, col2 = st.columns(2)
    with col1:
        max_results = st.slider("Number of sources", 1, 10, 5)
    with col2:
        use_web_search = st.toggle("Use web search", value=True)

    submitted = st.form_submit_button("🔍 Research", use_container_width=True)

if submitted and query:
    with st.spinner("Searching and analyzing..."):
        try:
            response = requests.post(API_URL, json={
                "query": query,
                "max_results": max_results,
                "use_web_search": use_web_search
            })
            data = response.json()

            # Confidence Score
            score = data["confidence_score"]
            color = "green" if score > 0.7 else "orange" if score > 0.5 else "red"
            st.markdown(f"### Confidence: :{color}[{score:.0%}]")

            # Answer
            st.markdown("### Answer")
            st.write(data["answer"])

            # Sources
            st.markdown("### Sources")
            for i, source in enumerate(data["sources"], 1):
                with st.expander(f"Source {i} — {source['title']}"):
                    st.write(source["content"])
                    st.caption(f"🔗 {source['url']}")
                    st.caption(f"Relevance: {source['relevance_score']:.2f}")

        except Exception as e:
            st.error(f"Something went wrong: {e}")

elif submitted and not query:
    st.warning("Please enter a question!")