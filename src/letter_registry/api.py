"""Private FastAPI surface for the Digital Letter Registry."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .auth import SupabasePasswordlessAuth
from .detail import SupabaseLetterDetailRepository
from .gemini_embeddings import GeminiEmbeddingProvider
from .hybrid_search import HybridSearchRepository
from .original_access import SupabaseOriginalAccessService
from .search import SearchFilters, SupabaseSearchRepository
from .semantic_search import SupabaseEmbeddingRepository
from .supabase_runtime import SupabasePostgrestTransport


security = HTTPBearer(auto_error=False)


class SearchCard(BaseModel):
    id: str
    title: str
    authority: str | None = None
    category: str | None = None
    issue_date: str | None = None
    status: str
    action_required: str | None = None
    concepts: list[str] = Field(default_factory=list)
    context_snippet: str | None = None
    file_type: str | None = None
    rank: float
    semantic_similarity: float | None = None
    open_original_path: str


class MagicLinkRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class MessageResponse(BaseModel):
    message: str


class LetterDetailResponse(BaseModel):
    id: str
    smart_filename: str | None = None
    title: str | None = None
    authority: str | None = None
    category: str | None = None
    subcategory: str | None = None
    issue_date: str | None = None
    status: str
    action_required: str | None = None
    deadline_at: str | None = None
    concepts: list[str] = Field(default_factory=list)
    structured_context: dict[str, object] = Field(default_factory=dict)
    open_original_path: str


class SearchResponse(BaseModel):
    query: str
    count: int
    mode: str
    results: list[SearchCard]


@dataclass(slots=True)
class ApiDependencies:
    original_access: SupabaseOriginalAccessService | None = None


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required at runtime")
    return value


def _access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated Supabase session required",
        )
    return credentials.credentials


def _transport(access_token: str) -> SupabasePostgrestTransport:
    return SupabasePostgrestTransport(
        base_url=_required_env("SUPABASE_URL"),
        publishable_key=_required_env("SUPABASE_PUBLISHABLE_KEY"),
        access_token=access_token,
    )


def create_app(dependencies: ApiDependencies | None = None) -> FastAPI:
    deps = dependencies or ApiDependencies()
    app = FastAPI(
        title="Official Letter Intelligence Archive",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(Path(__file__).with_name("web") / "index.html")

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/auth/magic-link", response_model=MessageResponse)
    def send_magic_link(payload: MagicLinkRequest) -> MessageResponse:
        redirect_to = _required_env("AUTH_REDIRECT_URL")
        auth = SupabasePasswordlessAuth.from_environment()
        auth.send_magic_link(email=payload.email, redirect_to=redirect_to)
        return MessageResponse(
            message="If this email is authorized, a sign-in link has been sent."
        )

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifest() -> FileResponse:
        return FileResponse(
            Path(__file__).with_name("web") / "manifest.webmanifest",
            media_type="application/manifest+json",
        )

    @app.get("/sw.js", include_in_schema=False)
    def service_worker() -> FileResponse:
        return FileResponse(
            Path(__file__).with_name("web") / "sw.js",
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/api/v1/search", response_model=SearchResponse)
    def search_letters(
        q: str = Query(default="", max_length=500),
        authority: str | None = Query(default=None, max_length=160),
        category: str | None = Query(default=None, max_length=100),
        status_filter: str | None = Query(default=None, alias="status"),
        year: int | None = Query(default=None, ge=1900, le=2100),
        file_type: str | None = Query(default=None, max_length=16),
        limit: int = Query(default=25, ge=1, le=100),
        access_token: str = Depends(_access_token),
    ) -> SearchResponse:
        transport = _transport(access_token)
        text_repo = SupabaseSearchRepository(transport)
        filters = SearchFilters(
            authority=authority,
            category=category,
            status=status_filter,
            year=year,
            file_type=file_type,
        )

        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if q.strip() and gemini_key:
            semantic_repo = SupabaseEmbeddingRepository(
                transport=transport,
                provider=GeminiEmbeddingProvider.from_environment(),
            )
            hybrid = HybridSearchRepository(
                text_search=text_repo,
                semantic_search=semantic_repo,
            )
            hybrid_results = hybrid.search(q, filters=filters, limit=limit)
            cards = [
                SearchCard(
                    id=item.result.record_id,
                    title=item.result.title
                    or item.result.smart_filename
                    or "Untitled letter",
                    authority=item.result.authority,
                    category=item.result.category,
                    issue_date=(
                        item.result.issue_date.isoformat()
                        if item.result.issue_date
                        else None
                    ),
                    status=item.result.status,
                    action_required=item.result.action_required,
                    concepts=list(item.result.concepts),
                    context_snippet=item.result.context_snippet,
                    file_type=item.result.file_type,
                    rank=item.hybrid_rank,
                    semantic_similarity=item.semantic_similarity,
                    open_original_path=f"/api/v1/letters/{item.result.record_id}/original",
                )
                for item in hybrid_results
            ]
            mode = "hybrid"
        else:
            text_results = text_repo.search(q, filters=filters, limit=limit)
            cards = [
                SearchCard(
                    id=item.record_id,
                    title=item.title or item.smart_filename or "Untitled letter",
                    authority=item.authority,
                    category=item.category,
                    issue_date=item.issue_date.isoformat() if item.issue_date else None,
                    status=item.status,
                    action_required=item.action_required,
                    concepts=list(item.concepts),
                    context_snippet=item.context_snippet,
                    file_type=item.file_type,
                    rank=item.combined_rank,
                    open_original_path=f"/api/v1/letters/{item.record_id}/original",
                )
                for item in text_results
            ]
            mode = "text"

        return SearchResponse(
            query=" ".join(q.split()),
            count=len(cards),
            mode=mode,
            results=cards,
        )

    @app.get("/api/v1/letters/{record_id}", response_model=LetterDetailResponse)
    def letter_detail(
        record_id: str,
        access_token: str = Depends(_access_token),
    ) -> LetterDetailResponse:
        repository = SupabaseLetterDetailRepository(_transport(access_token))
        detail = repository.get(record_id)
        if detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found",
            )
        return LetterDetailResponse(
            id=detail.record_id,
            smart_filename=detail.smart_filename,
            title=detail.title,
            authority=detail.authority,
            category=detail.category,
            subcategory=detail.subcategory,
            issue_date=detail.issue_date,
            status=detail.status,
            action_required=detail.action_required,
            deadline_at=detail.deadline_at,
            concepts=list(detail.concepts),
            structured_context=detail.structured_context,
            open_original_path=f"/api/v1/letters/{detail.record_id}/original",
        )

    @app.get("/api/v1/letters/{record_id}/original", include_in_schema=True)
    def open_original(
        record_id: str,
        access_token: str = Depends(_access_token),
    ) -> Response:
        if deps.original_access is None:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Private original-file resolver is not configured yet",
            )

        original = deps.original_access.fetch(
            record_id=record_id,
            database=_transport(access_token),
        )
        if original is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found",
            )

        safe_name = original.filename.replace('"', "")
        return Response(
            content=original.content,
            media_type=original.content_type,
            headers={
                "Content-Disposition": f'inline; filename="{safe_name}"',
                "Cache-Control": "private, no-store",
            },
        )

    return app


app = create_app()
