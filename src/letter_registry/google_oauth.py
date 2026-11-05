"""Direct Google OpenID Connect flow for native DLR authentication."""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from urllib import parse, request

import jwt
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token


class GoogleOAuthError(RuntimeError):
    pass


def start_google_oauth(*, client_id: str, redirect_uri: str, jwt_secret: str) -> tuple[str, str, str]:
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = __import__("base64").urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    signed_state = jwt.encode({
        "state": state, "nonce": nonce, "iss": "digital-letter-registry",
        "aud": "google-oauth-state", "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }, jwt_secret, algorithm="HS256")
    query = parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect_uri,
        "response_type": "code", "scope": "openid email profile",
        "state": state, "nonce": nonce, "code_challenge": challenge,
        "code_challenge_method": "S256", "prompt": "select_account",
    })
    return "https://accounts.google.com/o/oauth2/v2/auth?" + query, signed_state, verifier


def complete_google_oauth(*, code: str, returned_state: str, signed_state: str,
                          code_verifier: str, client_id: str, client_secret: str,
                          redirect_uri: str, jwt_secret: str) -> dict[str, object]:
    try:
        state_claims = jwt.decode(
            signed_state, jwt_secret, algorithms=["HS256"],
            issuer="digital-letter-registry", audience="google-oauth-state",
        )
    except jwt.InvalidTokenError as exc:
        raise GoogleOAuthError("OAuth state is invalid or expired") from exc
    if not secrets.compare_digest(str(state_claims.get("state", "")), returned_state):
        raise GoogleOAuthError("OAuth state mismatch")
    payload = parse.urlencode({
        "code": code, "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect_uri, "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }).encode("ascii")
    req = request.Request("https://oauth2.googleapis.com/token", data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with request.urlopen(req, timeout=15) as response:
            token_response = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise GoogleOAuthError("Google token exchange failed") from exc
    encoded_id_token = str(token_response.get("id_token") or "")
    if not encoded_id_token:
        raise GoogleOAuthError("Google did not return an identity token")
    try:
        claims = id_token.verify_oauth2_token(encoded_id_token, GoogleRequest(), audience=client_id)
    except Exception as exc:
        raise GoogleOAuthError("Google identity token could not be verified") from exc
    if not secrets.compare_digest(str(claims.get("nonce", "")), str(state_claims.get("nonce", ""))):
        raise GoogleOAuthError("Google identity nonce mismatch")
    if claims.get("email_verified") is not True or not claims.get("sub") or not claims.get("email"):
        raise GoogleOAuthError("Google identity is incomplete or its email is not verified")
    return claims
