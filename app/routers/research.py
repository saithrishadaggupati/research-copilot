from fastapi import APIRouter, HTTPException
from app.models.schemas import ResearchRequest, ResearchResponse, ErrorResponse
from app.services.search_service import get_search_service
from app.services.rag_service import get_rag_service
from app.services.confidence_service import get_confidence_service
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post(
    "/research",
    response_model=ResearchResponse,
    responses={500: {"model": ErrorResponse}}
)
def research(request: ResearchRequest):
    try:
        # Step 1 — Search the web
        search_service = get_search_service()
        sources = search_service.search(
            query=request.query,
            max_results=request.max_results
        )

        # Step 2 — Generate answer from sources
        rag_service = get_rag_service()
        answer = rag_service.generate_answer(
            query=request.query,
            sources=sources
        )

        # Step 3 — Score confidence
        confidence_service = get_confidence_service()
        confidence_score = confidence_service.score(
            query=request.query,
            answer=answer,
            sources=sources
        )

        return ResearchResponse(
            query=request.query,
            answer=answer,
            confidence_score=confidence_score,
            sources=sources,
            model_used=settings.openai_model
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))