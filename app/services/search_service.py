import json
import os
import hashlib
from collections import defaultdict
from tavily import TavilyClient
from groq import Groq
from app.models.schemas import SearchResult
from app.core.config import get_settings
from app.core.prompts import QUERY_EXPANSION_SYSTEM_PROMPT, QUERY_EXPANSION_USER_PROMPT

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


class HybridSearchEngine:
    """BM25 (keyword) + ChromaDB (semantic) hybrid search."""

    def __init__(self):
        self.chroma_client = None
        self.ef = None

        if CHROMA_AVAILABLE:
            try:
                self.chroma_client = chromadb.EphemeralClient()
                self.ef = embedding_functions.DefaultEmbeddingFunction()
            except Exception:
                self.chroma_client = None

    def rank(self, query: str, docs: list[dict], top_k: int = 10) -> list[dict]:
        if not docs:
            return docs

        contents = [d.get("content", "") for d in docs]
        urls = [d.get("url", "") for d in docs]

        bm25_scores = self._bm25_scores(query, contents, urls)
        vector_scores = self._vector_scores(query, contents, urls)

        for doc in docs:
            url = doc.get("url", "")
            doc["hybrid_score"] = (
                0.4 * bm25_scores.get(url, 0) +
                0.6 * vector_scores.get(url, 0)
            )

        return sorted(docs, key=lambda d: d["hybrid_score"], reverse=True)[:top_k]

    def _bm25_scores(self, query: str, contents: list[str], urls: list[str]) -> dict[str, float]:
        if not BM25_AVAILABLE or not contents:
            return {}
        tokenized = [_tokenize(c) for c in contents]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(_tokenize(query))
        max_score = max(scores) if max(scores) > 0 else 1
        return {urls[i]: float(scores[i] / max_score) for i in range(len(urls))}

    def _vector_scores(self, query: str, contents: list[str], urls: list[str]) -> dict[str, float]:
        if not CHROMA_AVAILABLE or not self.chroma_client:
            return {}
        try:
            collection_name = "search_" + hashlib.md5(query.encode()).hexdigest()[:8]
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.ef
            )
            ids = [f"doc_{i}" for i in range(len(contents))]
            collection.upsert(documents=contents, ids=ids)
            results = collection.query(query_texts=[query], n_results=min(len(contents), 10))
            result_ids = results["ids"][0]
            distances = results["distances"][0]
            scores = {urls[i]: 0.0 for i in range(len(urls))}
            for rid, dist in zip(result_ids, distances):
                idx = int(rid.split("_")[1])
                if idx < len(urls):
                    scores[urls[idx]] = 1.0 - min(dist, 1.0)
            return scores
        except Exception:
            return {}


class CohereReranker:
    def __init__(self):
        self.client = None
        api_key = os.getenv("COHERE_API_KEY", "")
        if COHERE_AVAILABLE and api_key:
            try:
                self.client = cohere.Client(api_key)
            except Exception:
                pass

    def rerank(self, query: str, docs: list[dict], top_n: int = 5) -> list[dict]:
        if not self.client or not docs:
            return docs[:top_n]
        try:
            texts = [d.get("content", "")[:512] for d in docs]
            results = self.client.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=texts,
                top_n=top_n
            )
            reranked = []
            for r in results.results:
                doc = docs[r.index].copy()
                doc["rerank_score"] = r.relevance_score
                reranked.append(doc)
            return reranked
        except Exception:
            return docs[:top_n]

    def is_available(self) -> bool:
        return self.client is not None


class SearchService:
    def __init__(self):
        self.settings = get_settings()
        self.tavily = TavilyClient(api_key=self.settings.tavily_api_key)
        self.groq = Groq(api_key=self.settings.groq_api_key)
        self.hybrid_engine = HybridSearchEngine()
        self.reranker = CohereReranker()

    def expand_query(self, query: str) -> list[str]:
        try:
            response = self.groq.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {"role": "system", "content": QUERY_EXPANSION_SYSTEM_PROMPT},
                    {"role": "user", "content": QUERY_EXPANSION_USER_PROMPT.format(query=query)}
                ],
                temperature=0.7
            )
            raw = response.choices[0].message.content.strip()
            clean = raw.replace("```json", "").replace("```", "").strip()
            variants = json.loads(clean)
            return variants if isinstance(variants, list) else []
        except Exception:
            return []

    def _tavily_search(self, query: str, max_results: int) -> list[dict]:
        try:
            response = self.tavily.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            return response.get("results", [])
        except Exception:
            return []

    def _reciprocal_rank_fusion(self, result_lists: list[list[dict]], k: int = 60) -> list[dict]:
        scores: dict[str, float] = defaultdict(float)
        docs: dict[str, dict] = {}
        for results in result_lists:
            for rank, item in enumerate(results, start=1):
                url = item.get("url", "")
                if not url:
                    continue
                scores[url] += 1.0 / (k + rank)
                if url not in docs:
                    docs[url] = item
        sorted_urls = sorted(scores.keys(), key=lambda u: scores[u], reverse=True)
        fused = []
        for url in sorted_urls:
            doc = docs[url]
            doc["rrf_score"] = scores[url]
            fused.append(doc)
        return fused

    def search(self, query: str, max_results: int = 5) -> tuple[list[SearchResult], list[str]]:
        """
        Pipeline:
        1. Query expansion — LLM generates 3 variants
        2. Tavily search for all variants (fetch 3x candidates)
        3. RRF fusion
        4. Hybrid re-ranking — BM25 + ChromaDB vector similarity
        5. Cohere re-ranker — if COHERE_API_KEY set, else use hybrid scores
        6. Return top N
        """
        variants = self.expand_query(query)
        all_queries = [query] + variants

        candidate_count = max(max_results * 3, 15)
        result_lists = [self._tavily_search(q, max_results=candidate_count) for q in all_queries]

        fused = self._reciprocal_rank_fusion(result_lists)
        reranked = self.hybrid_engine.rank(query, fused, top_k=max(max_results * 2, 10))

        if self.reranker.is_available():
            final = self.reranker.rerank(query, reranked, top_n=max_results)
            score_key = "rerank_score"
        else:
            final = reranked[:max_results]
            score_key = "hybrid_score"

        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                relevance_score=item.get(score_key, item.get("rrf_score", 0.0))
            )
            for item in final
        ], variants


def get_search_service() -> SearchService:
    return SearchService()
