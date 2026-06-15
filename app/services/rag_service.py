from langsmith import traceable
from groq import Groq
from app.models.schemas import SearchResult
from app.core.config import get_settings
from app.core.prompts import RESEARCH_SYSTEM_PROMPT, RESEARCH_USER_PROMPT

COST_PER_INPUT_TOKEN = 0.59 / 1_000_000
COST_PER_OUTPUT_TOKEN = 0.79 / 1_000_000


class RAGService:
    def __init__(self):
        self.settings = get_settings()
        self.client = Groq(api_key=self.settings.groq_api_key)

    def _build_context(self, sources: list[SearchResult]) -> str:
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(
                f"[{i}] {source.title}\n"
                f"URL: {source.url}\n"
                f"Content: {source.content}\n"
            )
        return "\n---\n".join(context_parts)

    @traceable(name="generate_answer_stream")
    def generate_answer_stream(self, query: str, sources: list[SearchResult]):
        context = self._build_context(sources)
        stream = self.client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": RESEARCH_USER_PROMPT.format(query=query, context=context)}
            ],
            temperature=0.3,
            stream=True
        )
        usage = None
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta, None
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage
        yield "", usage

    @traceable(name="generate_answer")
    def generate_answer(self, query: str, sources: list[SearchResult]) -> tuple[str, int, float]:
        context = self._build_context(sources)
        response = self.client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": RESEARCH_USER_PROMPT.format(query=query, context=context)}
            ],
            temperature=0.3
        )
        answer = response.choices[0].message.content
        usage = response.usage
        tokens = usage.total_tokens if usage else 0
        cost = (
            (usage.prompt_tokens * COST_PER_INPUT_TOKEN) +
            (usage.completion_tokens * COST_PER_OUTPUT_TOKEN)
        ) if usage else 0.0
        return answer, tokens, cost


def get_rag_service() -> RAGService:
    return RAGService()
