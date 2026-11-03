import base64
import hashlib
import hmac
import json
import time
from functools import wraps
from typing import Any, Callable, Dict

from flask import current_app, g, request


def _sign(payload_b64: str) -> str:
    return hmac.new(
        current_app.config["SECRET_KEY"].encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()


def create_token(user_id: int) -> str:
    """Create a signed token: base64(JSON payload) + "." + HMAC-SHA256 signature."""
    payload = {"user_id": user_id, "exp": int(time.time()) + current_app.config["TOKEN_EXPIRATION"]}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return f"{payload_b64}.{_sign(payload_b64)}"


def verify_token(token: str) -> Dict[str, Any]:
    """Return the token payload, or raise ValueError if it is malformed, forged or expired."""
    try:
        payload_b64, signature = token.split(".")
    except ValueError:
        raise ValueError("Invalid token format") from None
    if not hmac.compare_digest(signature, _sign(payload_b64)):
        raise ValueError("Invalid token")
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        expires_at = int(payload["exp"])
    except (ValueError, KeyError, TypeError):
        raise ValueError("Invalid token format") from None
    if expires_at < int(time.time()):
        raise ValueError("Token has expired")
    return payload


def require_auth(f: Callable) -> Callable:
    """Require an `Authorization: Bearer <token>` header; sets g.user_id."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization", "")
        scheme, _, token = auth_header.partition(" ")
        if not auth_header:
            return {"error": "No authorization header"}, 401
        if scheme.lower() != "bearer" or not token:
            return {"error": "Authorization header must be 'Bearer <token>'"}, 401
        try:
            g.user_id = verify_token(token)["user_id"]
        except ValueError as e:
            return {"error": str(e)}, 401
        return f(*args, **kwargs)

    return decorated_function
