@'
# Research Copilot

I built Research Copilot because I was frustrated with how often AI tools give confident answers without showing where the information comes from.

Instead of relying solely on a language model, this project first expands the user's query into multiple variants, searches the web for all of them, fuses the results using Reciprocal Rank Fusion, streams the answer token by token, and cites every claim inline. A second evaluation step scores how well the sources actually support the answer.

## Screenshots



![Home](images/research-copilot-home.png)





![Result](images/research-copilot-result.png)



## How it works

1. A user submits a question through the Streamlit interface.
2. Llama 3.3 70B generates 3 alternative search queries from the original question.
3. Tavily searches the web for all 4 queries in parallel.
4. Results are fused using Reciprocal Rank Fusion (RRF) to surface the most consistently relevant sources.
5. Llama 3.3 70B streams an answer using only the retrieved content, with inline citations like [1][2].
6. A second LLM call scores how well the sources support the answer.
7. Token usage and cost per query are tracked and displayed in the sidebar dashboard.

I separated query expansion, retrieval, generation, and evaluation into distinct steps because each is a different problem. Combining them into a single prompt produced worse results across all four.

## Tech Stack

- FastAPI + Uvicorn - backend API
- SlowAPI - rate limiting (10 requests/minute)
- Streamlit - frontend with SSE streaming
- Groq (Llama 3.3 70B) - query expansion, answer generation, confidence scoring
- Tavily - real-time web search
- Reciprocal Rank Fusion - multi-query result merging
- LangSmith - request tracing and observability
- Pydantic v2 - data validation
- pytest - testing

## Project Structure

app/
  core/
    config.py              # environment config, validated at startup
    prompts.py             # all prompts stored as constants
  models/
    schemas.py             # request and response shapes
  routers/
    research.py            # /research and /research/stream endpoints
  services/
    search_service.py      # query expansion + RRF search
    rag_service.py         # streaming answer generation
    confidence_service.py  # confidence scoring
    cost_tracker.py        # per-query token and cost logging
frontend/
  streamlit_app.py         # streaming UI with cost dashboard
tests/
  test_research.py         # 6 tests, no API key needed

## Running Locally

git clone https://github.com/saithrishadaggupati/research-copilot
cd research-copilot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
streamlit run frontend/streamlit_app.py

## API Endpoints

- POST /api/v1/research - standard JSON response
- POST /api/v1/research/stream - SSE streaming response
- GET /api/v1/costs - cost dashboard data

## Testing

pytest tests/ -v

All external API calls are mocked, so tests run without API keys.
'@ | Set-Content "C:\Users\ASUS\research_copilot\README.md" -Encoding UTF8; git add .; git commit -m "feat: upgrade research copilot with RRF search, inline citations, SSE streaming, rate limiting, cost tracking"; git push