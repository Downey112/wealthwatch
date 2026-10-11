"""Identify the caller from the Supabase access token on the request.

The frontend signs in with Supabase Auth and sends the session's JWT as a
bearer token. Projects sign those tokens either with an asymmetric key
published at the project's JWKS endpoint (the default for new projects) or
with the legacy shared secret, so both are accepted.
"""
import os
from functools import lru_cache

import jwt

ASYMMETRIC_ALGORITHMS = ("ES256", "RS256")


class AuthError(Exception):
    pass


@lru_cache(maxsize=2)
def jwks_client(url):
    return jwt.PyJWKClient(url)


def signing_key(token, supabase_url):
    algorithm = jwt.get_unverified_header(token).get("alg")
    if algorithm in ASYMMETRIC_ALGORITHMS and supabase_url:
        jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        return jwks_client(jwks_url).get_signing_key_from_jwt(token).key, algorithm

    secret = os.environ.get("SUPABASE_JWT_SECRET")
    if algorithm == "HS256" and secret:
        return secret, algorithm

    raise AuthError(f"Unsupported token algorithm: {algorithm}")


def email_from_token(token):
    supabase_url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    try:
        key, algorithm = signing_key(token, supabase_url)
        claims = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=f"{supabase_url}/auth/v1" if supabase_url else None,
        )
    except jwt.PyJWTError as e:
        raise AuthError(str(e)) from e

    email = claims.get("email")
    if not email:
        raise AuthError("Token has no email claim")
    return email
