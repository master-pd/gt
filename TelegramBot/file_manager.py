"""
FILE_MANAGER.PY - ফাইল ম্যানেজমেন্ট ইউটিলিটি
"""

import os
import shutil
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import json

from config import Config

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self):
        self.config = Config
        self.processed_files = set()
        self.load_processed_files()
    
    def load_processed_files(self):
        """প্রসেস করা ফাইল লোড"""
        try:
            processed_file = Path("processed_files.json")
            if processed_file.exists():
                with open(processed_file, 'r') as f:
                    self.processed_files = set(json.load(f))
        except Exception as e:
            logger.error(f"❌ প্রসেসড ফাইল লোড এরর: {e}")
    
    def save_processed_files(self):
        """প্রসেস করা ফাইল সেভ"""
        try:
            with open("processed_files.json", 'w') as f:
                json.dump(list(self.processed_files), f)
        except Exception as e:
            logger.error(f"❌ প্রসেসড ফাইল সেভ এরর: {e}")
    
    def calculate_hash(self, file_path: str) -> str:
        """ফাইল হ্যাশ"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()
    
    def get_new_files(self, folder_path: str) -> List[Dict]:
        """নতুন ফাইল খোঁজা"""
        new_files = []
        folder = Path(folder_path)
        
        if not folder.exists():
            logger.warning(f"❌ ফোল্ডার নেই: {folder_path}")
            return new_files
        
        for pattern in self.get_file_patterns():
            for file_path in folder.rglob(pattern):
                if file_path.is_file():
                    file_hash = self.calculate_hash(str(file_path))
                    
                    if file_hash not in self.processed_files:
                        file_info = {
                            'path': str(file_path),
                            'name': file_path.name,
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                            'hash': file_hash,
                            'folder': folder_path
                        }
                        
                        # ফাইল টাইপ চেক
                        ext = file_path.suffix.lower()
                        if ext in self.config.ALLOWED_EXTENSIONS:
                            new_files.append(file_info)
                            self.processed_files.add(file_hash)
        
        self.save_processed_files()
        return new_files
    
    def get_file_patterns(self) -> List[str]:
        """ফাইল প্যাটার্ন"""
        patterns = []
        for ext in self.config.ALLOWED_EXTENSIONS:
            patterns.append(f"*{ext}")
        return patterns
    
    def organize_files_by_type(self, files: List[Dict]) -> Dict[str, List]:
        """ফাইল টাইপ অনুযায়ী অর্গানাইজ"""
        organized = {
            'images': [],
            'videos': [],
            'documents': [],
            'audio': [],
            'archives': [],
            'others': []
        }
        
        for file in files:
            ext = Path(file['name']).suffix.lower()
            
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                organized['images'].append(file)
            elif ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']:
                organized['videos'].append(file)
            elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']:
                organized['documents'].append(file)
            elif ext in ['.mp3', '.wav', '.aac', '.flac', '.m4a']:
                organized['audio'].append(file)
            elif ext in ['.zip', '.rar', '.7z']:
                organized['archives'].append(file)
            else:
                organized['others'].append(file)
        
        return organized
    
    def get_storage_info(self) -> Dict:
        """স্টোরেজ ইনফো"""
        total_size = 0
        total_files = 0
        
        for folder in self.config.MONITOR_FOLDERS:
            folder_path = Path(folder)
            if folder_path.exists():
                for pattern in self.get_file_patterns():
                    for file in folder_path.rglob(pattern):
                        if file.is_file():
                            total_size += file.stat().st_size
                            total_files += 1
        
        return {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'monitored_folders': len(self.config.MONITOR_FOLDERS)
        }
