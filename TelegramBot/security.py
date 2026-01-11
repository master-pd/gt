"""
SECURITY.PY - সিকিউরিটি ফাংশন
"""

import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from cryptography.fernet import Fernet

from config import Config

class SecurityManager:
    def __init__(self):
        self.secret_key = Config.SECRET_KEY.encode()
        self.fernet = Fernet(base64.urlsafe_b64encode(
            hashlib.sha256(Config.ENCRYPTION_KEY).digest()
        ))
    
    def generate_token(self, user_id: int, device_id: str = "") -> str:
        """JWT টোকেন জেনারেট"""
        payload = {
            'user_id': user_id,
            'device_id': device_id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """JWT টোকেন ভেরিফাই"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def encrypt_data(self, data: str) -> str:
        """ডেটা এনক্রিপ্ট"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """ডেটা ডিক্রিপ্ট"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def hash_password(self, password: str) -> str:
        """পাসওয়ার্ড হ্যাশ"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str) -> bool:
        """API কি ভেরিফাই"""
        return hmac.compare_digest(api_key, Config.API_ACCESS_TOKEN)
    
    def verify_telegram_user(self, user_id: int) -> bool:
        """Telegram ইউজার ভেরিফাই"""
        return user_id == Config.YOUR_TELEGRAM_USER_ID
    
    def generate_device_id(self) -> str:
        """ডিভাইস আইডি জেনারেট"""
        import uuid
        return str(uuid.uuid4())
