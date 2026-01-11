"""
DATABASE.PY - SQLite ডাটাবেজ ম্যানেজমেন্ট
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_NAME
        self.init_database()
    
    def get_connection(self):
        """ডাটাবেজ কানেকশন তৈরি"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """ডাটাবেজ টেবিল তৈরি"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # ফাইলস টেবিল
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT UNIQUE NOT NULL,
                    original_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    cloudinary_id TEXT NOT NULL,
                    cloudinary_url TEXT NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT,
                    device_name TEXT,
                    is_deleted INTEGER DEFAULT 0
                )
            ''')
            
            # ব্যাকআপ স্ট্যাটাস টেবিল
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backup_status (
                    id INTEGER PRIMARY KEY,
                    total_files INTEGER DEFAULT 0,
                    total_size_mb REAL DEFAULT 0,
                    last_backup_time TIMESTAMP,
                    last_sync_time TIMESTAMP
                )
            ''')
            
            # ডিভাইস টেবিল
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    device_name TEXT,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_files INTEGER DEFAULT 0
                )
            ''')
            
            # লগ টেবিল
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_type TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ব্যাকআপ স্ট্যাটাস ইনিশিয়ালাইজ
            cursor.execute('''
                INSERT OR IGNORE INTO backup_status (id) VALUES (1)
            ''')
            
            conn.commit()
        
        logger.info("✅ ডাটাবেজ ইনিশিয়ালাইজড")
    
    def add_file(self, file_data: Dict) -> bool:
        """নতুন ফাইল ডাটাবেজে অ্যাড"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO files 
                    (file_hash, original_path, filename, file_size, file_type, 
                     cloudinary_id, cloudinary_url, device_name, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_data['file_hash'],
                    file_data['original_path'],
                    file_data['filename'],
                    file_data['file_size'],
                    file_data['file_type'],
                    file_data['cloudinary_id'],
                    file_data['cloudinary_url'],
                    file_data.get('device_name', 'Unknown'),
                    json.dumps(file_data.get('tags', []))
                ))
                
                # স্ট্যাটাস আপডেট
                cursor.execute('''
                    UPDATE backup_status 
                    SET total_files = total_files + 1,
                        total_size_mb = total_size_mb + (? / 1048576.0),
                        last_backup_time = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (file_data['file_size'],))
                
                # লগ এন্ট্রি
                cursor.execute('''
                    INSERT INTO activity_logs (activity_type, details)
                    VALUES (?, ?)
                ''', ('FILE_UPLOAD', f"Uploaded: {file_data['filename']}"))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ ফাইল অ্যাড করার সময় এরর: {e}")
            return False
    
    def get_all_files(self, limit: int = 100) -> List[Dict]:
        """সব ফাইল লিস্ট"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM files 
                WHERE is_deleted = 0 
                ORDER BY upload_date DESC 
                LIMIT ?
            ''', (limit,))
            
            files = []
            for row in cursor.fetchall():
                file_dict = dict(row)
                file_dict['tags'] = json.loads(file_dict['tags'] or '[]')
                files.append(file_dict)
            
            return files
    
    def search_files(self, keyword: str) -> List[Dict]:
        """ফাইল সার্চ"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM files 
                WHERE (filename LIKE ? OR tags LIKE ?) 
                AND is_deleted = 0
            ''', (f'%{keyword}%', f'%{keyword}%'))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_file_by_hash(self, file_hash: str) -> Optional[Dict]:
        """ফাইল হ্যাশ দিয়ে খোঁজা"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM files WHERE file_hash = ?', (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_file(self, file_hash: str) -> bool:
        """ফাইল ডিলিট (সফট ডিলিট)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE files SET is_deleted = 1 
                    WHERE file_hash = ?
                ''', (file_hash,))
                
                cursor.execute('''
                    INSERT INTO activity_logs (activity_type, details)
                    VALUES (?, ?)
                ''', ('FILE_DELETE', f"Deleted file: {file_hash}"))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ ফাইল ডিলিট এরর: {e}")
            return False
    
    def get_backup_stats(self) -> Dict:
        """ব্যাকআপ স্ট্যাটাস"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM backup_status WHERE id = 1')
            row = cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) as total FROM files WHERE is_deleted = 0')
            total_files = cursor.fetchone()['total']
            
            if row:
                stats = dict(row)
                stats['total_files'] = total_files
                return stats
            
            return {}
    
    def log_activity(self, activity_type: str, details: str = ""):
        """অ্যাক্টিভিটি লগ"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activity_logs (activity_type, details)
                VALUES (?, ?)
            ''', (activity_type, details))
            conn.commit()
