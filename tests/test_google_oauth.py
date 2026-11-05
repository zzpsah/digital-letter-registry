from __future__ import annotations

import jwt
import pytest

from letter_registry.google_oauth import GoogleOAuthError, complete_google_oauth, start_google_oauth


def test_google_oauth_start_uses_state_nonce_and_pkce():
    secret = "g" * 48
    url, signed_state, verifier = start_google_oauth(
        client_id="client-id", redirect_uri="https://archive.example.org/auth/google/callback",
        jwt_secret=secret,
    )
    claims = jwt.decode(signed_state, secret, algorithms=["HS256"],
                        issuer="digital-letter-registry", audience="google-oauth-state")
    assert claims["state"] in url
    assert claims["nonce"]
    assert "code_challenge_method=S256" in url
    assert verifier


def test_google_oauth_callback_rejects_state_mismatch_before_token_exchange():
    secret = "g" * 48
    _, signed_state, verifier = start_google_oauth(
        client_id="client-id", redirect_uri="https://archive.example.org/auth/google/callback",
        jwt_secret=secret,
    )
    with pytest.raises(GoogleOAuthError, match="state mismatch"):
        complete_google_oauth(
            code="not-used", returned_state="tampered", signed_state=signed_state,
            code_verifier=verifier, client_id="client-id", client_secret="secret",
            redirect_uri="https://archive.example.org/auth/google/callback", jwt_secret=secret,
        )


def test_google_oauth_callback_rejects_forged_signed_state():
    with pytest.raises(GoogleOAuthError, match="invalid or expired"):
        complete_google_oauth(
            code="not-used", returned_state="state", signed_state="forged",
            code_verifier="verifier", client_id="client-id", client_secret="secret",
            redirect_uri="https://archive.example.org/auth/google/callback", jwt_secret="g" * 48,
        )
