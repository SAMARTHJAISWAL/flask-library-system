from dataclasses import dataclass
from typing import Optional, Dict, Any
import hashlib
import re

@dataclass
class Member:
    id: Optional[int]
    name: str
    email: str
    password: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Member':
        return cls(
            id=data.get('id'),
            name=data['name'],
            email=data['email'],
            password=cls.hash_password(data['password'])
        )

    def check_password(self, password: str) -> bool:
        return self.password == self.hash_password(password)

    def validate(self) -> Optional[str]:
        if not self.name or len(self.name.strip()) == 0:
            return "Name is required"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not self.email or not re.match(email_pattern, self.email):
            return "Valid email is required"
        
        if not hasattr(self, 'id') or self.id is None:
            if not self.password or len(self.password) < 8:
                return "Password must be at least 8 characters long"
        
        return None

