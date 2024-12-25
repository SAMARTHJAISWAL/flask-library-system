from functools import wraps
from typing import Callable, Any, Dict
from flask import request, current_app
import base64
import json
import hmac
import hashlib
import time

def create_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'exp': int(time.time()) + current_app.config['TOKEN_EXPIRATION']
    }
    payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(
        current_app.config['SECRET_KEY'].encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{signature}"

def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload_b64, signature = token.split('.')
        expected_signature = hmac.new(
            current_app.config['SECRET_KEY'].encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token")
        payload = json.loads(base64.b64decode(payload_b64))
        if payload['exp'] < int(time.time()):
            raise ValueError("Token has expired")
        return payload
    except Exception:
        raise ValueError("Invalid token format")

def require_auth(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {"error": "No authorization header"}, 401
        try:
            token = auth_header.split(" ")[1]
            payload = verify_token(token)
            request.user_id = payload['user_id']
        except (IndexError, ValueError) as e:
            return {"error": str(e)}, 401
        return f(*args, **kwargs)
    return decorated_function

