import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from werkzeug.security import check_password_hash, generate_password_hash

EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
MIN_PASSWORD_LENGTH = 8


@dataclass
class Member:
    id: Optional[int]
    name: str
    email: str
    password: str  # always the hash, never the plain-text password

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "email": self.email}

    @staticmethod
    def hash_password(password: str) -> str:
        return generate_password_hash(password)

    @staticmethod
    def validate_password(password: Any) -> Optional[str]:
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            return f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Member":
        return cls(
            id=data.get("id"),
            name=data["name"],
            email=data["email"],
            password=cls.hash_password(data["password"]),
        )

    def check_password(self, password: str) -> bool:
        # Accounts created before the switch to Werkzeug hashes stored a bare SHA-256 hex digest.
        if re.fullmatch(r"[0-9a-f]{64}", self.password):
            legacy = hashlib.sha256(password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, password)

    @staticmethod
    def validate_name(name: Any) -> Optional[str]:
        if not isinstance(name, str) or not name.strip():
            return "Name is required"
        return None

    def validate(self) -> Optional[str]:
        error = self.validate_name(self.name)
        if error:
            return error
        if not isinstance(self.email, str) or not re.match(EMAIL_PATTERN, self.email):
            return "Valid email is required"
        return None
