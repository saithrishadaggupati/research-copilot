import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import ResearchRequest, ResearchResponse, ErrorResponse
from app.services.search_service import get_search_service
from app.services.rag_service import get_rag_service, COST_PER_INPUT_TOKEN, COST_PER_OUTPUT_TOKEN
from app.services.confidence_service import get_confidence_service
from app.services.cost_tracker import get_cost_tracker
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/research",
    response_model=ResearchResponse,
    responses={500: {"model": ErrorResponse}}
)
@limiter.limit("10/minute")
def research(request: Request, body: ResearchRequest):
    try:
        search_service = get_search_service()
        sources, query_variants = search_service.search(
            query=body.query,
            max_results=body.max_results
        )

        rag_service = get_rag_service()
        answer, tokens_used, cost_usd = rag_service.generate_answer(
            query=body.query,
            sources=sources
        )

        confidence_service = get_confidence_service()
        confidence_score = confidence_service.score(
            query=body.query,
            answer=answer,
            sources=sources
        )

        cost_tracker = get_cost_tracker()
        cost_tracker.record(
            query=body.query,
            tokens_used=tokens_used,
            cost_usd=cost_usd
        )

        return ResearchResponse(
            query=body.query,
            answer=answer,
            confidence_score=confidence_score,
            sources=sources,
            model_used=settings.groq_model,
            query_variants=query_variants,
            cost_usd=cost_usd,
            tokens_used=tokens_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/stream")
@limiter.limit("10/minute")
async def research_stream(request: Request, body: ResearchRequest):
    """
    SSE streaming endpoint. Yields server-sent events:
      data: {"type": "chunk", "content": "..."}
      data: {"type": "sources", "sources": [...], "variants": [...]}
      data: {"type": "meta", "confidence": 0.87, "cost_usd": 0.0012, "tokens": 1234}
      data: {"type": "done"}
    """
    async def event_generator():
        try:
            search_service = get_search_service()
            sources, query_variants = search_service.search(
                query=body.query,
                max_results=body.max_results
            )

            sources_payload = json.dumps({
                "type": "sources",
                "sources": [s.model_dump() for s in sources],
                "variants": query_variants
            })
            yield f"data: {sources_payload}\n\n"

            rag_service = get_rag_service()
            full_answer = ""
            final_usage = None

            for chunk, usage in rag_service.generate_answer_stream(
                query=body.query, sources=sources
            ):
                if chunk:
                    full_answer += chunk
                    payload = json.dumps({"type": "chunk", "content": chunk})
                    yield f"data: {payload}\n\n"
                if usage:
                    final_usage = usage

            tokens_used = final_usage.total_tokens if final_usage else 0
            cost_usd = 0.0
            if final_usage:
                cost_usd = (
                    final_usage.prompt_tokens * COST_PER_INPUT_TOKEN +
                    final_usage.completion_tokens * COST_PER_OUTPUT_TOKEN
                )

            confidence_service = get_confidence_service()
            confidence_score = confidence_service.score(
                query=body.query,
                answer=full_answer,
                sources=sources
            )

            cost_tracker = get_cost_tracker()
            cost_tracker.record(
                query=body.query,
                tokens_used=tokens_used,
                cost_usd=cost_usd
            )

            meta_payload = json.dumps({
                "type": "meta",
                "confidence": confidence_score,
                "cost_usd": round(cost_usd, 6),
                "tokens": tokens_used,
                "model": settings.groq_model
            })
            yield f"data: {meta_payload}\n\n"
            yield "data: {\"type\": \"done\"}\n\n"

        except Exception as e:
            error_payload = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/costs")
def get_costs():
    """Dashboard data: all cost records + totals."""
    tracker = get_cost_tracker()
    records = tracker.load()
    return {
        "records": records,
        "total_cost_usd": round(tracker.total_cost(), 6),
        "total_tokens": tracker.total_tokens(),
        "total_queries": len(records)
    }
