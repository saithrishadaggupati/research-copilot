import os
import uuid
import shutil
from pathlib import Path

import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from app.models.schemas import SearchResult

PERSIST_DIR = os.getenv("DOCUMENT_INDEX_DIR", "./data/document_index")
UPLOAD_DIR = os.getenv("DOCUMENT_UPLOAD_DIR", "./data/uploads")
COLLECTION_NAME = "user_documents"

_embed_model = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _embed_model


def _load_file_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="ignore")


class DocumentService:
    def __init__(self):
        Path(PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(path=PERSIST_DIR)
        self.collection = self.chroma_client.get_or_create_collection(COLLECTION_NAME)
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.embed_model = _get_embed_model()
        self.splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)

        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store, embed_model=self.embed_model
        )

    def ingest_file(self, filename: str, raw_bytes: bytes) -> dict:
        doc_id = str(uuid.uuid4())
        dest = Path(UPLOAD_DIR) / f"{doc_id}_{filename}"
        dest.write_bytes(raw_bytes)

        text = _load_file_text(dest)
        if not text.strip():
            raise ValueError("No extractable text found in file")

        document = Document(
            text=text,
            doc_id=doc_id,
            metadata={"filename": filename, "doc_id": doc_id},
        )
        nodes = self.splitter.get_nodes_from_documents([document])
        self.index.insert_nodes(nodes)

        return {"doc_id": doc_id, "filename": filename, "chunks": len(nodes)}

    def list_documents(self) -> list[dict]:
        data = self.collection.get(include=["metadatas"])
        seen = {}
        for meta in data.get("metadatas", []) or []:
            if not meta:
                continue
            did = meta.get("doc_id")
            if did and did not in seen:
                seen[did] = {"doc_id": did, "filename": meta.get("filename", "unknown")}
        return list(seen.values())

    def delete_document(self, doc_id: str) -> bool:
        self.collection.delete(where={"doc_id": doc_id})
        return True

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if self.collection.count() == 0:
            return []
        query_engine = self.index.as_retriever(similarity_top_k=top_k)
        nodes = query_engine.retrieve(query)
        results = []
        for n in nodes:
            filename = n.node.metadata.get("filename", "document")
            results.append(
                SearchResult(
                    title=filename,
                    url=f"doc://{n.node.metadata.get('doc_id', '')}",
                    content=n.node.get_content(),
                    relevance_score=float(n.score) if n.score is not None else 0.0,
                )
            )
        return results


def get_document_service() -> DocumentService:
    return DocumentService()