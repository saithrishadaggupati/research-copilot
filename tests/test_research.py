import pytest
from unittest.mock import MagicMock, patch
from app.models.schemas import SearchResult, ResearchRequest
from app.services.rag_service import RAGService
from app.services.confidence_service import ConfidenceService
from app.services.search_service import SearchService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_sources():
    return [
        SearchResult(
            title="What is RAG?",
            url="https://example.com/rag",
            content="RAG stands for Retrieval-Augmented Generation. It combines LLMs with external knowledge bases.",
            relevance_score=0.95
        ),
        SearchResult(
            title="RAG explained",
            url="https://example.com/rag-explained",
            content="RAG retrieves relevant documents and feeds them into the LLM as context.",
            relevance_score=0.90
        )
    ]


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.groq_api_key = "fake-key"
    settings.groq_model = "llama-3.3-70b-versatile"
    settings.tavily_api_key = "fake-tavily-key"
    return settings


# ── Search Service Tests ───────────────────────────────────────────────────────

class TestSearchService:
    @patch("app.services.search_service.TavilyClient")
    @patch("app.services.search_service.get_settings")
    def test_search_returns_results(self, mock_get_settings, mock_tavily, mock_settings, mock_sources):
        mock_get_settings.return_value = mock_settings
        mock_client = MagicMock()
        mock_tavily.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "What is RAG?",
                    "url": "https://example.com/rag",
                    "content": "RAG stands for Retrieval-Augmented Generation.",
                    "score": 0.95
                }
            ]
        }

        service = SearchService()
        results = service.search("what is RAG", max_results=1)

        assert len(results) == 1
        assert results[0].title == "What is RAG?"
        assert results[0].relevance_score == 0.95

    @patch("app.services.search_service.TavilyClient")
    @patch("app.services.search_service.get_settings")
    def test_search_empty_results(self, mock_get_settings, mock_tavily, mock_settings):
        mock_get_settings.return_value = mock_settings
        mock_client = MagicMock()
        mock_tavily.return_value = mock_client
        mock_client.search.return_value = {"results": []}

        service = SearchService()
        results = service.search("unknown query")

        assert results == []


# ── RAG Service Tests ──────────────────────────────────────────────────────────

class TestRAGService:
    @patch("app.services.rag_service.Groq")
    @patch("app.services.rag_service.get_settings")
    def test_generate_answer(self, mock_get_settings, mock_groq, mock_settings, mock_sources):
        mock_get_settings.return_value = mock_settings
        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="RAG is a framework that combines LLMs with external knowledge."))]
        )

        service = RAGService()
        answer = service.generate_answer("what is RAG", mock_sources)

        assert isinstance(answer, str)
        assert len(answer) > 0

    @patch("app.services.rag_service.Groq")
    @patch("app.services.rag_service.get_settings")
    def test_build_context(self, mock_get_settings, mock_groq, mock_settings, mock_sources):
        mock_get_settings.return_value = mock_settings
        mock_groq.return_value = MagicMock()

        service = RAGService()
        context = service._build_context(mock_sources)

        assert "Source 1" in context
        assert "Source 2" in context
        assert "example.com" in context


# ── Confidence Service Tests ───────────────────────────────────────────────────

class TestConfidenceService:
    @patch("app.services.confidence_service.Groq")
    @patch("app.services.confidence_service.get_settings")
    def test_score_returns_float(self, mock_get_settings, mock_groq, mock_settings, mock_sources):
        mock_get_settings.return_value = mock_settings
        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"confidence_score": 0.92, "reasoning": "Sources directly support the answer"}'))]
        )

        service = ConfidenceService()
        score = service.score("what is RAG", "RAG is a framework", mock_sources)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @patch("app.services.confidence_service.Groq")
    @patch("app.services.confidence_service.get_settings")
    def test_score_fallback_on_bad_json(self, mock_get_settings, mock_groq, mock_settings, mock_sources):
        mock_get_settings.return_value = mock_settings
        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="not valid json at all"))]
        )

        service = ConfidenceService()
        score = service.score("what is RAG", "RAG is a framework", mock_sources)

        assert score == 0.5