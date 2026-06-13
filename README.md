# Research Copilot

I built Research Copilot because I was frustrated with how often AI tools give confident answers without showing where the information came from.

Instead of relying solely on a language model, this project first searches the web for relevant sources, then generates an answer based on those sources, and finally estimates how reliable the answer is based on the information retrieved.

The goal isn't to eliminate mistakes completely—it's to make the system more transparent about what it knows and how well the available sources support the answer.

## Screenshots



![Home](images/research-copilot-home.png)





![Result](images/research-copilot-result.png)

## How it works

1. A user submits a question through the Streamlit interface.
2. Tavily searches the web and retrieves the most relevant sources.
3. The retrieved content is formatted into a context window.
4. Llama 3.3 70B (via Groq) generates an answer using only the retrieved information.
5. A second evaluation step analyzes source coverage and produces a confidence score.
6. The UI displays the answer, confidence score, and the sources used during generation.

I chose a two-step approach because answer generation and answer evaluation are different problems. Separating them produced more consistent results than trying to handle both tasks in a single prompt.

## Tech Stack

- FastAPI + Uvicorn — backend API
- Streamlit — frontend
- Groq (Llama 3.3 70B) — answer generation
- Tavily — real-time web search
- Pydantic v2 — data validation
- pytest — testing

## Project Structure

```
app/
  core/
    config.py              # environment config, validated at startup
    prompts.py             # all prompts stored as constants
  models/
    schemas.py             # request and response shapes
  routers/
    research.py            # API route, delegates to services
  services/
    search_service.py      # web search
    rag_service.py         # answer generation
    confidence_service.py  # confidence scoring
frontend/
  streamlit_app.py         # UI
tests/
  test_research.py         # 6 tests, no API key needed
```

## Running Locally

```bash
git clone https://github.com/saithrishadaggupati/research-copilot
cd research-copilot

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Add your GROQ_API_KEY and TAVILY_API_KEY

uvicorn app.main:app --reload --port 8000
streamlit run frontend/streamlit_app.py
```

## Testing

```bash
pytest tests/ -v
```

All external API calls are mocked, so tests run without API keys.

## What I'd add next

- Document upload support for combining web search with personal files
- Query caching to reduce repeated API calls
- Streaming responses for a better user experience
- SQLite-based query history
- Source citations directly within generated answers
- Additional confidence signals beyond LLM-based evaluation