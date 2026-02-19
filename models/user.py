from datetime import datetime
from dataclasses import dataclass, field
from typing import List
import bcrypt

@dataclass
class User:
    """User model for authentication"""
    id: str
    email: str
    password_hash: str
    full_name: str
    role: str = "viewer"  # admin, manager, viewer
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime = None
    reset_token: str = None
    reset_token_expiry: datetime = None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def to_dict(self):
        """Convert user to dictionary (safe for JSON)"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }