"""
CLOUDINARY_HANDLER.PY - Cloudinary ফাইল আপলোড/ম্যানেজমেন্ট
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
import mimetypes

from config import Config

# Cloudinary কনফিগার
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET,
    secure=True
)

logger = logging.getLogger(__name__)

class CloudinaryManager:
    def __init__(self):
        self.config = Config
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
        self.max_file_size = Config.get_max_file_size()
    
    def calculate_file_hash(self, file_path: str) -> str:
        """ফাইল হ্যাশ ক্যালকুলেট"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_file_type(self, filename: str) -> str:
        """ফাইল টাইপ ডিটেক্ট"""
        ext = Path(filename).suffix.lower()
        
        if ext in self.config.ALLOWED_EXTENSIONS[:6]:  # Images
            return "image"
        elif ext in self.config.ALLOWED_EXTENSIONS[6:12]:  # Videos
            return "video"
        elif ext in self.config.ALLOWED_EXTENSIONS[12:20]:  # Documents
            return "document"
        elif ext in self.config.ALLOWED_EXTENSIONS[20:25]:  # Audio
            return "audio"
        elif ext in self.config.ALLOWED_EXTENSIONS[25:28]:  # Archives
            return "archive"
        elif ext == '.apk':
            return "app"
        else:
            return "other"
    
    def upload_file(self, file_path: str, tags: list = None) -> Dict:
        """ফাইল Cloudinary-তে আপলোড"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"ফাইল পাওয়া যায়নি: {file_path}")
            
            # ফাইল সাইজ চেক
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise ValueError(f"ফাইল সাইজ বড়: {file_size/1024/1024:.2f}MB > {self.max_file_size/1024/1024:.2f}MB")
            
            # এক্সটেনশন চেক
            ext = file_path.suffix.lower()
            if ext not in self.allowed_extensions:
                raise ValueError(f"অনুমোদিত নয়: {ext}")
            
            # ফাইল হ্যাশ
            file_hash = self.calculate_file_hash(str(file_path))
            
            # Cloudinary-তে আপলোড
            upload_result = cloudinary.uploader.upload(
                str(file_path),
                public_id=f"personal_backup/{file_hash}",
                resource_type="auto",
                tags=tags or ["auto_backup"],
                folder="personal_backup",
                use_filename=True,
                unique_filename=False,
                overwrite=False
            )
            
            return {
                'success': True,
                'file_hash': file_hash,
                'filename': file_path.name,
                'file_size': file_size,
                'file_type': self.get_file_type(file_path.name),
                'cloudinary_id': upload_result['public_id'],
                'cloudinary_url': upload_result['secure_url'],
                'original_path': str(file_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Cloudinary আপলোড এরর: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': Path(file_path).name
            }
    
    def delete_file(self, public_id: str) -> bool:
        """Cloudinary থেকে ফাইল ডিলিট"""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            logger.error(f"❌ Cloudinary ডিলিট এরর: {e}")
            return False
    
    def get_file_info(self, public_id: str) -> Optional[Dict]:
        """ফাইল ইনফো"""
        try:
            result = cloudinary.api.resource(public_id)
            return {
                'public_id': result['public_id'],
                'url': result['secure_url'],
                'format': result['format'],
                'size': result['bytes'],
                'created_at': result['created_at']
            }
        except Exception as e:
            logger.error(f"❌ ফাইল ইনফো এরর: {e}")
            return None
    
    def list_files(self, max_results: int = 100) -> list:
        """Cloudinary ফাইল লিস্ট"""
        try:
            result = cloudinary.api.resources(
                type="upload",
                prefix="personal_backup/",
                max_results=max_results,
                tags=True
            )
            return result.get('resources', [])
        except Exception as e:
            logger.error(f"❌ ফাইল লিস্ট এরর: {e}")
            return []
