from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import DocumentUploadResponse, DocumentListResponse
from app.services.document_service import get_document_service

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    try:
        raw_bytes = await file.read()
        service = get_document_service()
        result = service.ingest_file(file.filename, raw_bytes)
        return DocumentUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=DocumentListResponse)
def list_documents():
    service = get_document_service()
    return DocumentListResponse(documents=service.list_documents())


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    service = get_document_service()
    service.delete_document(doc_id)
    return {"status": "deleted", "doc_id": doc_id}