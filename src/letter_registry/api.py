"""Private FastAPI surface for the Digital Letter Registry."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .access import ArchiveMembership, ArchiveRole, SupabaseArchiveAccess
from .account_admin import SupabaseArchiveAccountAdmin
from .auth import SupabaseAuthError, SupabaseAuthSession, SupabasePasswordlessAuth
from .channel_intake import ChannelIntakeService, IntakeChannel, IntakeProvenance, SupabaseProvenanceRepository
from .detail import SupabaseLetterDetailRepository
from .gemini_embeddings import GeminiEmbeddingProvider
from .google_drive_reader import GoogleDrivePrivateTransport
from .google_drive_writer import GoogleDrivePrivateWriter
from .hybrid_search import HybridSearchRepository
from .intake import DuplicateSourceError, IntakePolicy, IntakeService
from .jobs import SupabaseProcessingQueue
from .original_access import SupabaseOriginalAccessService
from .relationships import RelationshipReviewStatus, SupabaseRelationshipRepository
from .runtime_readiness import check_runtime_readiness
from .reprocessing import ReprocessingTargets, SupabaseReprocessingPlanner
from .search import SearchFilters, SupabaseSearchRepository
from .semantic_search import SupabaseEmbeddingRepository
from .session import SupabaseSessionError, SupabaseUserSession
from .storage import GoogleDriveOriginalStorage
from .supabase_repository import SupabaseLetterRepository
from .supabase_runtime import (
    ArchiveScopedSupabaseTransport,
    SupabasePostgrestTransport,
    SupabaseRuntimeError,
)
from .versions import current_processing_versions
from .version_registry import ProcessingTargetVersions, SupabaseProcessingVersionRegistry


security = HTTPBearer(auto_error=False)


class SearchCard(BaseModel):
    id: str
    title: str
    summary: str | None = None
    reference_number: str | None = None
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


class PasswordLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=256)


class PasswordChangeRequest(BaseModel):
    password: str = Field(min_length=8, max_length=256)


class CreateAccountRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class RegistrationRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    invite_code: str = Field(min_length=36, max_length=36)


class RegistrationMagicLinkRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    invite_code: str = Field(min_length=36, max_length=36)


class RegistrationResponse(BaseModel):
    authenticated: bool
    confirmation_required: bool
    role: str | None = None
    message: str


class AdminInviteRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: str = Field(default="viewer", min_length=5, max_length=6)


class AdminMemberUpdateRequest(BaseModel):
    role: str = Field(min_length=5, max_length=6)
    status: str = Field(min_length=6, max_length=8)


class ArchiveAccessEntryResponse(BaseModel):
    kind: str
    record_id: str
    user_id: str | None = None
    email: str
    role: str
    status: str
    invite_code: str | None = None
    created_at: str | None = None


class ArchiveAccessListResponse(BaseModel):
    items: list[ArchiveAccessEntryResponse]


class AdminInviteResponse(BaseModel):
    invite_id: str
    email: str
    role: str
    status: str
    invite_code: str
    user_id: str | None = None
    registration_path: str | None = None


class AdminMemberResponse(BaseModel):
    user_id: str
    email: str
    role: str
    status: str


class MessageResponse(BaseModel):
    message: str


class SessionStatusResponse(BaseModel):
    authenticated: bool
    role: str | None = None


class AuthProvidersResponse(BaseModel):
    google: bool
    password: bool = True
    magic_link: bool = True
    registration_mode: str = "invite_only"


class FragmentSessionRequest(BaseModel):
    # Token format/length is owned by Supabase and may change. Keep request
    # validation permissive here; the access token is validated against
    # Supabase immediately before any DLR session cookie is issued.
    access_token: str = Field(min_length=1, max_length=16384)
    refresh_token: str = Field(min_length=1, max_length=8192)
    expires_in: int = Field(default=3600, ge=1, le=604800)


class RuntimeCapabilitiesResponse(BaseModel):
    synthetic_only: bool
    drive_upload_configured: bool
    original_streaming_configured: bool
    semantic_search_configured: bool
    auth_cookie_secure: bool


class RuntimeReadinessCheckResponse(BaseModel):
    name: str
    ready: bool
    detail: str


class RuntimeReadinessResponse(BaseModel):
    ready: bool
    checks: list[RuntimeReadinessCheckResponse]


class LetterDetailResponse(BaseModel):
    id: str
    smart_filename: str | None = None
    title: str | None = None
    summary: str | None = None
    reference_number: str | None = None
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


class RelationshipResponse(BaseModel):
    id: str
    source_letter_id: str
    target_letter_id: str
    relationship_type: str
    confidence: float | None = None
    review_status: str
    relationship_version: str
    rationale: str | None = None
    reviewed_at: str | None = None


class RelationshipReviewRequest(BaseModel):
    decision: str


class ReprocessingPreviewItemResponse(BaseModel):
    letter_id: str
    reasons: list[str]
    current_versions: dict[str, str]
    target_versions: dict[str, str]


class ReprocessingEnqueueRequest(BaseModel):
    confirm: bool = False
    limit: int = Field(default=500, ge=1, le=500)


class ReprocessingEnqueueResponse(BaseModel):
    enqueued: int


class ProcessingVersionsResponse(BaseModel):
    versions: dict[str, str]


class ReprocessingPreviewResponse(BaseModel):
    count: int
    items: list[ReprocessingPreviewItemResponse]


class ProcessingProfileRequest(BaseModel):
    extraction: str
    context: str
    dictionary: str
    filename_rule: str
    category_schema: str
    embedding: str
    status_rule: str


class ProcessingProfileResponse(ProcessingProfileRequest):
    pass


class IntakeResponse(BaseModel):
    record_id: str
    original_filename: str
    sha256: str
    job_id: str
    job_status: str = "pending"
    synthetic_only: bool


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


_ACCESS_COOKIE = "dlr_access_token"
_REFRESH_COOKIE = "dlr_refresh_token"


def _cookie_secure() -> bool:
    value = os.environ.get("AUTH_COOKIE_SECURE", "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _refresh_cookie_max_age() -> int:
    raw = os.environ.get("AUTH_REFRESH_COOKIE_MAX_AGE", "").strip()
    if not raw:
        return 30 * 24 * 60 * 60
    try:
        seconds = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            "AUTH_REFRESH_COOKIE_MAX_AGE must be an integer number of seconds"
        ) from exc
    minimum = 24 * 60 * 60
    maximum = 90 * 24 * 60 * 60
    if seconds < minimum or seconds > maximum:
        raise RuntimeError(
            "AUTH_REFRESH_COOKIE_MAX_AGE must be between 1 and 90 days"
        )
    return seconds


def _set_session_cookies(
    response: Response,
    session: SupabaseAuthSession,
) -> None:
    common = {
        "httponly": True,
        "secure": _cookie_secure(),
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(
        _ACCESS_COOKIE,
        session.access_token,
        max_age=session.expires_in,
        **common,
    )
    response.set_cookie(
        _REFRESH_COOKIE,
        session.refresh_token,
        max_age=_refresh_cookie_max_age(),
        **common,
    )
    response.headers["Cache-Control"] = "private, no-store"


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(_ACCESS_COOKIE, path="/")
    response.delete_cookie(_REFRESH_COOKIE, path="/")
    response.headers["Cache-Control"] = "private, no-store"


def _access_token(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if credentials is not None and credentials.scheme.lower() == "bearer":
        return credentials.credentials

    access_token = request.cookies.get(_ACCESS_COOKIE, "").strip()
    if access_token:
        return access_token

    refresh_token = request.cookies.get(_REFRESH_COOKIE, "").strip()
    if refresh_token:
        try:
            session = SupabasePasswordlessAuth.from_environment().refresh_session(
                refresh_token=refresh_token,
            )
        except (SupabaseAuthError, ValueError) as exc:
            _clear_session_cookies(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase session expired",
            ) from exc
        _set_session_cookies(response, session)
        return session.access_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authenticated Supabase session required",
    )


def _configured_app_origin() -> str:
    configured = os.environ.get("AUTH_APP_ORIGIN", "").strip()
    if configured:
        parsed = urlsplit(configured)
    else:
        redirect = _required_env("AUTH_REDIRECT_URL")
        parsed = urlsplit(redirect)

    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise RuntimeError("Valid AUTH_APP_ORIGIN or AUTH_REDIRECT_URL is required")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise RuntimeError("HTTP app origin is allowed only for local development")
    return f"{parsed.scheme}://{parsed.netloc}"


def _require_same_origin(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    """Protect cookie-authenticated state changes from cross-site requests.

    Explicit Bearer API clients are not vulnerable to browser CSRF because the
    credential is supplied deliberately in the Authorization header.
    """

    if credentials is not None and credentials.scheme.lower() == "bearer":
        return

    origin = request.headers.get("origin", "").strip()
    try:
        expected = _configured_app_origin()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application origin is not configured",
        ) from exc

    if origin != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-site mutation request rejected",
        )


def _archive_id() -> str:
    try:
        return str(UUID(_required_env("DLR_ARCHIVE_ID")))
    except ValueError as exc:
        raise RuntimeError("DLR_ARCHIVE_ID must be a valid UUID") from exc


def _raw_transport(access_token: str) -> SupabasePostgrestTransport:
    return SupabasePostgrestTransport(
        base_url=_required_env("SUPABASE_URL"),
        publishable_key=_required_env("SUPABASE_PUBLISHABLE_KEY"),
        access_token=access_token,
    )


def _archive_membership(
    access_token: str,
    *,
    roles: set[ArchiveRole] | None = None,
) -> ArchiveMembership:
    try:
        user_id = SupabaseUserSession.from_environment(
            access_token=access_token,
        ).user_id()
        return SupabaseArchiveAccess(
            transport=_raw_transport(access_token),
            archive_id=_archive_id(),
        ).require(user_id, roles=roles)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not authorized for the archive",
        ) from exc
    except (SupabaseSessionError, SupabaseRuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired archive session",
        ) from exc


def _transport(
    access_token: str,
    *,
    roles: set[ArchiveRole] | None = None,
) -> ArchiveScopedSupabaseTransport:
    _archive_membership(access_token, roles=roles)
    return ArchiveScopedSupabaseTransport(
        transport=_raw_transport(access_token),
        archive_id=_archive_id(),
    )


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _runtime_intake(access_token: str) -> tuple[str, ChannelIntakeService]:
    folder_reference = _required_env("DRIVE_ORIGINALS_FOLDER_REFERENCE")
    membership = _archive_membership(
        access_token,
        roles={ArchiveRole.ADMIN, ArchiveRole.EDITOR},
    )
    owner_id = membership.user_id
    database = _transport(
        access_token,
        roles={ArchiveRole.ADMIN, ArchiveRole.EDITOR},
    )
    storage = GoogleDriveOriginalStorage(
        transport=GoogleDrivePrivateWriter.from_environment(),
        originals_folder_reference=folder_reference,
    )
    service = ChannelIntakeService(
        intake=IntakeService(
            storage=storage,
            repository=SupabaseLetterRepository(database),
            queue=SupabaseProcessingQueue(database),
            policy=IntakePolicy(
                synthetic_only=not _truthy_env("ENABLE_REAL_INTAKE"),
            ),
        ),
        provenance=SupabaseProvenanceRepository(database),
    )
    return owner_id, service


def _drive_credentials_configured() -> bool:
    if os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "").strip():
        return True
    return all(
        os.environ.get(name, "").strip()
        for name in (
            "GOOGLE_OAUTH_CLIENT_ID",
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "GOOGLE_DRIVE_REFRESH_TOKEN",
        )
    )


def _runtime_dependencies() -> ApiDependencies:
    if _drive_credentials_configured():
        return ApiDependencies(
            original_access=SupabaseOriginalAccessService(
                GoogleDrivePrivateTransport.from_environment()
            )
        )
    return ApiDependencies()


def create_app(dependencies: ApiDependencies | None = None) -> FastAPI:
    deps = dependencies if dependencies is not None else _runtime_dependencies()
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

    @app.get(
        "/api/v1/auth/providers",
        response_model=AuthProvidersResponse,
    )
    def auth_providers() -> AuthProvidersResponse:
        try:
            google = SupabasePasswordlessAuth.from_environment().provider_enabled(
                "google"
            )
        except (SupabaseAuthError, ValueError):
            google = False
        return AuthProvidersResponse(google=google)

    @app.get("/auth/google", include_in_schema=False)
    def google_sign_in() -> Response:
        redirect_to = _required_env("AUTH_REDIRECT_URL")
        auth = SupabasePasswordlessAuth.from_environment()
        try:
            if not auth.provider_enabled("google"):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Google sign-in is not configured yet",
                )
            target = auth.social_authorize_url(
                provider="google",
                redirect_to=redirect_to,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google sign-in configuration is invalid",
            ) from exc
        return RedirectResponse(
            url=target,
            status_code=status.HTTP_303_SEE_OTHER,
            headers={
                "Cache-Control": "private, no-store",
                "Referrer-Policy": "no-referrer",
            },
        )

    @app.post(
        "/api/v1/auth/password/change",
        response_model=MessageResponse,
    )
    def change_password(
        payload: PasswordChangeRequest,
        access_token: str = Depends(_access_token),
        _: None = Depends(_require_same_origin),
    ) -> MessageResponse:
        _archive_membership(access_token)
        try:
            SupabasePasswordlessAuth.from_environment().update_password(
                access_token=access_token,
                password=payload.password,
            )
        except (SupabaseAuthError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password could not be updated",
            ) from exc
        return MessageResponse(message="Password updated")

    @app.post(
        "/api/v1/auth/create-account",
        response_model=RegistrationResponse,
    )
    def create_account(
        payload: CreateAccountRequest,
        _: None = Depends(_require_same_origin),
    ) -> Response:
        auth = SupabasePasswordlessAuth.from_environment()
        try:
            result = auth.sign_up_with_password(
                email=payload.email,
                password=payload.password,
            )
        except (SupabaseAuthError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account creation failed",
            ) from exc

        body = RegistrationResponse(
            authenticated=False,
            confirmation_required=result.confirmation_required,
            role=None,
            message=(
                "Account created. Admin approval is required before archive access."
            ),
        )
        return Response(
            content=body.model_dump_json(),
            media_type="application/json",
            status_code=status.HTTP_201_CREATED,
        )

    @app.post(
        "/api/v1/auth/register",
        response_model=RegistrationResponse,
    )
    def register_with_password(
        payload: RegistrationRequest,
        _: None = Depends(_require_same_origin),
    ) -> Response:
        auth = SupabasePasswordlessAuth.from_environment()
        try:
            valid = auth.validate_archive_invite(
                email=payload.email,
                invite_code=payload.invite_code,
            )
        except (SupabaseAuthError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration invitation is invalid",
            ) from exc
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A valid DLR invitation is required",
            )

        try:
            result = auth.sign_up_with_password(
                email=payload.email,
                password=payload.password,
                invite_code=payload.invite_code,
            )
        except (SupabaseAuthError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account registration failed",
            ) from exc

        if result.session is None:
            body = RegistrationResponse(
                authenticated=False,
                confirmation_required=True,
                message="Account created. Confirm the email, then sign in.",
            )
            return Response(
                content=body.model_dump_json(),
                media_type="application/json",
                status_code=status.HTTP_202_ACCEPTED,
            )

        membership = _archive_membership(result.session.access_token)
        body = RegistrationResponse(
            authenticated=True,
            confirmation_required=False,
            role=membership.role.value,
            message="DLR account created and signed in.",
        )
        response = Response(
            content=body.model_dump_json(),
            media_type="application/json",
        )
        _set_session_cookies(response, result.session)
        return response

    @app.post(
        "/api/v1/auth/register-magic-link",
        response_model=MessageResponse,
    )
    def register_with_magic_link(
        payload: RegistrationMagicLinkRequest,
        _: None = Depends(_require_same_origin),
    ) -> MessageResponse:
        auth = SupabasePasswordlessAuth.from_environment()
        try:
            valid = auth.validate_archive_invite(
                email=payload.email,
                invite_code=payload.invite_code,
            )
            if not valid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="A valid DLR invitation is required",
                )
            auth.send_magic_link(
                email=payload.email,
                redirect_to=_required_env("AUTH_REDIRECT_URL"),
                create_user=True,
                invite_code=payload.invite_code,
            )
        except HTTPException:
            raise
        except SupabaseAuthError as exc:
            if "HTTP 429" in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Sign-in email rate limit reached. Try again shortly.",
                ) from exc
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Registration email provider is temporarily unavailable.",
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration invitation is invalid",
            ) from exc
        return MessageResponse(
            message="Registration link sent to the invited email."
        )

    @app.post(
        "/api/v1/auth/password",
        response_model=SessionStatusResponse,
    )
    def password_sign_in(
        payload: PasswordLoginRequest,
        _: None = Depends(_require_same_origin),
    ) -> Response:
        try:
            session = SupabasePasswordlessAuth.from_environment().sign_in_with_password(
                email=payload.email,
                password=payload.password,
            )
            membership = _archive_membership(session.access_token)
        except HTTPException:
            raise
        except (SupabaseAuthError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is invalid",
            ) from exc

        response = Response(
            content=(
                '{"authenticated":true,"role":"'
                + membership.role.value
                + '"}'
            ),
            media_type="application/json",
        )
        _set_session_cookies(response, session)
        return response

    @app.post("/api/v1/auth/magic-link", response_model=MessageResponse)
    def send_magic_link(
        payload: MagicLinkRequest,
        _: None = Depends(_require_same_origin),
    ) -> MessageResponse:
        redirect_to = _required_env("AUTH_REDIRECT_URL")
        auth = SupabasePasswordlessAuth.from_environment()
        try:
            auth.send_magic_link(email=payload.email, redirect_to=redirect_to)
        except SupabaseAuthError as exc:
            if "HTTP 429" in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Sign-in email rate limit reached. Try again shortly.",
                ) from exc
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Sign-in email provider is temporarily unavailable.",
            ) from exc
        return MessageResponse(
            message="If this email is authorized, a sign-in link has been sent."
        )

    @app.get("/auth/confirm", include_in_schema=False)
    def confirm_magic_link(
        token_hash: str | None = None,
        type: str = "email",
    ) -> Response:
        if not token_hash:
            return FileResponse(
                Path(__file__).with_name("web") / "auth-confirm.html",
                headers={
                    "Cache-Control": "private, no-store",
                    "Referrer-Policy": "no-referrer",
                    "X-Content-Type-Options": "nosniff",
                    "Content-Security-Policy": (
                        "default-src 'self'; "
                        "script-src 'self' 'unsafe-inline'; "
                        "style-src 'self' 'unsafe-inline'; "
                        "connect-src 'self'; "
                        "base-uri 'none'; frame-ancestors 'none'"
                    ),
                },
            )
        try:
            session = SupabasePasswordlessAuth.from_environment().verify_token_hash(
                token_hash=token_hash,
                verification_type=type,
            )
        except (SupabaseAuthError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sign-in link is invalid or expired",
            ) from exc

        _archive_membership(session.access_token)
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        _set_session_cookies(response, session)
        return response

    @app.post(
        "/api/v1/auth/session-from-fragment",
        response_model=SessionStatusResponse,
    )
    def session_from_fragment(
        payload: FragmentSessionRequest,
        _: None = Depends(_require_same_origin),
    ) -> Response:
        try:
            user_id = SupabaseUserSession.from_environment(
                access_token=payload.access_token,
            ).user_id()
        except (SupabaseSessionError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase session",
            ) from exc

        membership = _archive_membership(payload.access_token)
        if membership.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is not authorized for the archive",
            )

        session = SupabaseAuthSession(
            access_token=payload.access_token,
            refresh_token=payload.refresh_token,
            expires_in=payload.expires_in,
        )
        response = Response(
            content=(
                '{"authenticated":true,"role":"'
                + membership.role.value
                + '"}'
            ),
            media_type="application/json",
        )
        _set_session_cookies(response, session)
        return response

    @app.get(
        "/api/v1/admin/access",
        response_model=ArchiveAccessListResponse,
    )
    def list_archive_access(
        access_token: str = Depends(_access_token),
    ) -> ArchiveAccessListResponse:
        _archive_membership(
            access_token,
            roles={ArchiveRole.ADMIN},
        )
        service = SupabaseArchiveAccountAdmin(
            transport=_raw_transport(access_token),
            archive_id=_archive_id(),
        )
        try:
            items = service.list_access()
        except (SupabaseRuntimeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Archive access list is temporarily unavailable",
            ) from exc
        return ArchiveAccessListResponse(
            items=[
                ArchiveAccessEntryResponse(
                    kind=item.kind,
                    record_id=item.record_id,
                    user_id=item.user_id,
                    email=item.email,
                    role=item.role.value,
                    status=item.status,
                    invite_code=item.invite_code,
                    created_at=item.created_at,
                )
                for item in items
            ]
        )

    @app.post(
        "/api/v1/admin/invites",
        response_model=AdminInviteResponse,
    )
    def create_archive_invite(
        payload: AdminInviteRequest,
        access_token: str = Depends(_access_token),
        _: None = Depends(_require_same_origin),
    ) -> AdminInviteResponse:
        _archive_membership(
            access_token,
            roles={ArchiveRole.ADMIN},
        )
        try:
            role = ArchiveRole(payload.role)
            result = SupabaseArchiveAccountAdmin(
                transport=_raw_transport(access_token),
                archive_id=_archive_id(),
            ).invite(email=payload.email, role=role)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account invitation",
            ) from exc
        except SupabaseRuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Account invitation could not be created",
            ) from exc
        registration_path = (
            f"/#invite={result.invite_code}"
            if result.status == "pending"
            else None
        )
        return AdminInviteResponse(
            invite_id=result.invite_id,
            email=result.email,
            role=result.role.value,
            status=result.status,
            invite_code=result.invite_code,
            user_id=result.user_id,
            registration_path=registration_path,
        )

    @app.patch(
        "/api/v1/admin/members/{user_id}",
        response_model=AdminMemberResponse,
    )
    def update_archive_member(
        user_id: str,
        payload: AdminMemberUpdateRequest,
        access_token: str = Depends(_access_token),
        _: None = Depends(_require_same_origin),
    ) -> AdminMemberResponse:
        _archive_membership(
            access_token,
            roles={ArchiveRole.ADMIN},
        )
        try:
            role = ArchiveRole(payload.role)
            result = SupabaseArchiveAccountAdmin(
                transport=_raw_transport(access_token),
                archive_id=_archive_id(),
            ).update_member(
                user_id=user_id,
                role=role,
                status=payload.status,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid member update",
            ) from exc
        except SupabaseRuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Member update was rejected",
            ) from exc
        return AdminMemberResponse(
            user_id=result.user_id,
            email=result.email,
            role=result.role.value,
            status=result.status,
        )

    @app.post(
        "/api/v1/admin/invites/{invite_id}/revoke",
        response_model=MessageResponse,
    )
    def revoke_archive_invite(
        invite_id: str,
        access_token: str = Depends(_access_token),
        _: None = Depends(_require_same_origin),
    ) -> MessageResponse:
        _archive_membership(
            access_token,
            roles={ArchiveRole.ADMIN},
        )
        try:
            revoked = SupabaseArchiveAccountAdmin(
                transport=_raw_transport(access_token),
                archive_id=_archive_id(),
            ).revoke_invite(invite_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitation id",
            ) from exc
        except SupabaseRuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invitation could not be revoked",
            ) from exc
        if not revoked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending invitation not found",
            )
        return MessageResponse(message="Invitation revoked")

    @app.get(
        "/api/v1/readiness",
        response_model=RuntimeReadinessResponse,
    )
    def runtime_readiness(
        access_token: str = Depends(_access_token),
    ) -> RuntimeReadinessResponse:
        _transport(access_token)
        readiness = check_runtime_readiness()
        return RuntimeReadinessResponse(
            ready=readiness.ready,
            checks=[
                RuntimeReadinessCheckResponse(
                    name=item.name,
                    ready=item.ready,
                    detail=item.detail,
                )
                for item in readiness.checks
            ],
        )

    @app.get(
        "/api/v1/capabilities",
        response_model=RuntimeCapabilitiesResponse,
    )
    def capabilities(
        access_token: str = Depends(_access_token),
    ) -> RuntimeCapabilitiesResponse:
        _transport(access_token)
        drive_credentials = _drive_credentials_configured()
        return RuntimeCapabilitiesResponse(
            synthetic_only=not _truthy_env("ENABLE_REAL_INTAKE"),
            drive_upload_configured=(
                drive_credentials
                and bool(
                    os.environ.get(
                        "DRIVE_ORIGINALS_FOLDER_REFERENCE",
                        "",
                    ).strip()
                )
            ),
            original_streaming_configured=drive_credentials,
            semantic_search_configured=bool(
                os.environ.get("GEMINI_API_KEY", "").strip()
            ),
            auth_cookie_secure=_cookie_secure(),
        )

    @app.get("/api/v1/auth/session", response_model=SessionStatusResponse)
    def session_status(
        access_token: str = Depends(_access_token),
    ) -> SessionStatusResponse:
        membership = _archive_membership(access_token)
        return SessionStatusResponse(
            authenticated=True,
            role=membership.role.value,
        )

    @app.post("/api/v1/auth/logout", response_model=MessageResponse)
    def logout(
        _: None = Depends(_require_same_origin),
    ) -> Response:
        response = Response(
            content='{"message":"Signed out"}',
            media_type="application/json",
        )
        _clear_session_cookies(response)
        return response

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

    @app.post(
        "/api/v1/intake",
        response_model=IntakeResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def intake_upload(
        file: UploadFile = File(...),
        access_token: str = Depends(_access_token),
        _: None = Depends(_require_same_origin),
    ) -> IntakeResponse:
        safe_name = Path(file.filename or "").name
        if not safe_name or safe_name in {".", ".."}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid upload filename is required",
            )

        try:
            owner_id, service = _runtime_intake(access_token)
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Private intake runtime is not configured",
            ) from exc

        with TemporaryDirectory() as directory:
            source = Path(directory) / safe_name
            total = 0
            with source.open("wb") as handle:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > service.policy.max_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Upload exceeds configured size limit",
                        )
                    handle.write(chunk)

            try:
                result = service.ingest_path(
                    source,
                    owner_id=owner_id,
                    provenance=IntakeProvenance(
                        channel=IntakeChannel.WEB,
                        filename=safe_name,
                        metadata={
                            "content_type": file.content_type or "",
                        },
                    ),
                )
            except DuplicateSourceError as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This file content is already archived",
                ) from exc
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

        return IntakeResponse(
            record_id=result.record.record_id,
            original_filename=result.record.original_filename,
            sha256=result.record.original_sha256,
            job_id=result.job.job_id,
            synthetic_only=service.policy.synthetic_only,
        )

    @app.get(
        "/api/v1/processing/versions",
        response_model=ProcessingVersionsResponse,
    )
    def processing_versions(
        access_token: str = Depends(_access_token),
    ) -> ProcessingVersionsResponse:
        _transport(access_token)
        return ProcessingVersionsResponse(
            versions=current_processing_versions().to_dict()
        )

    @app.get(
        "/api/v1/reprocessing/preview",
        response_model=ReprocessingPreviewResponse,
    )
    def preview_reprocessing(
        ocr_version: str | None = Query(default=None, min_length=1),
        context_version: str | None = Query(default=None, min_length=1),
        dictionary_version: str | None = Query(default=None, min_length=1),
        filename_rule_version: str | None = Query(default=None, min_length=1),
        category_schema_version: str | None = Query(default=None, min_length=1),
        embedding_version: str | None = Query(default=None, min_length=1),
        status_rule_version: str | None = Query(default=None, min_length=1),
        access_token: str = Depends(_access_token),
    ) -> ReprocessingPreviewResponse:
        _archive_membership(
            access_token,
            roles={ArchiveRole.ADMIN},
        )
        current = current_processing_versions().reprocessing_targets()
        targets = ReprocessingTargets(
            ocr_version=ocr_version or current.ocr_version,
            context_version=context_version or current.context_version,
            dictionary_version=dictionary_version or current.dictionary_version,
            filename_rule_version=(
                filename_rule_version or current.filename_rule_version
            ),
            category_schema_version=(
                category_schema_version or current.category_schema_version
            ),
            embedding_version=embedding_version or current.embedding_version,
            status_rule_version=status_rule_version or current.status_rule_version,
        )
        items = SupabaseReprocessingPlanner(
            _transport(access_token)
        ).preview(targets)
        return ReprocessingPreviewResponse(
            count=len(items),
            items=[
                ReprocessingPreviewItemResponse(
                    letter_id=item.letter_id,
                    reasons=list(item.reasons),
                    current_versions=item.current_versions,
                    target_versions=item.target_versions,
                )
                for item in items
            ],
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
                    summary=item.result.summary,
                    reference_number=item.result.reference_number,
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
                    summary=item.summary,
                    reference_number=item.reference_number,
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
            summary=detail.summary,
            reference_number=detail.reference_number,
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

    @app.get(
        "/api/v1/letters/{record_id}/relationships",
        response_model=list[RelationshipResponse],
    )
    def letter_relationships(
        record_id: str,
        access_token: str = Depends(_access_token),
    ) -> list[RelationshipResponse]:
        rows = SupabaseRelationshipRepository(
            _transport(access_token)
        ).list_for_letter(record_id)
        return [
            RelationshipResponse(
                id=str(row["id"]),
                source_letter_id=str(row["source_letter_id"]),
                target_letter_id=str(row["target_letter_id"]),
                relationship_type=str(row["relationship_type"]),
                confidence=(
                    float(row["confidence"])
                    if row.get("confidence") is not None
                    else None
                ),
                review_status=str(row["review_status"]),
                relationship_version=str(row["relationship_version"]),
                rationale=(
                    str(row["rationale"])
                    if row.get("rationale") is not None
                    else None
                ),
                reviewed_at=(
                    str(row["reviewed_at"])
                    if row.get("reviewed_at") is not None
                    else None
                ),
            )
            for row in rows
        ]

    @app.post(
        "/api/v1/relationships/{relationship_id}/review",
        response_model=MessageResponse,
    )
    def review_relationship(
        relationship_id: str,
        payload: RelationshipReviewRequest,
        access_token: str = Depends(_access_token),
        _: None = Depends(_require_same_origin),
    ) -> MessageResponse:
        _archive_membership(
            access_token,
            roles={ArchiveRole.ADMIN},
        )
        try:
            decision = RelationshipReviewStatus(payload.decision)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="decision must be confirmed or rejected",
            ) from exc

        if decision is RelationshipReviewStatus.SUGGESTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="decision must be confirmed or rejected",
            )

        ok = SupabaseRelationshipRepository(
            _transport(access_token)
        ).review(
            relationship_id,
            decision=decision,
        )
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship not found",
            )
        return MessageResponse(
            message=f"Relationship {decision.value}."
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
