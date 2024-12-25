from typing import Optional
from dataclasses import dataclass
import os

@dataclass
class Config:
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    DATABASE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'library.db')
    TOKEN_EXPIRATION: int = 3600  
    PAGE_SIZE: int = 10