"""
API_ROUTES.PY - FastAPI রাউটস (Android App এর জন্য)
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
import logging
import json

from config import Config
from database import DatabaseManager
from cloudinary_handler import CloudinaryManager
from security import SecurityManager
from file_manager import FileManager

app = FastAPI(title="Auto Backup Pro API")
db = DatabaseManager()
cloudinary = CloudinaryManager()
security = SecurityManager()
file_manager = FileManager()

logger = logging.getLogger(__name__)

# Dependency for API key verification
def verify_api_key(x_api_key: str = Header(...)):
    if not security.verify_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True

@app.get("/")
async def root():
    """রুট এন্ডপয়েন্ট"""
    return {
        "app": Config.APP_NAME,
        "version": Config.VERSION,
        "status": "running",
        "owner": Config.YOUR_TELEGRAM_USER_ID
    }

@app.get("/api/status")
async def get_status(verified: bool = Depends(verify_api_key)):
    """সিস্টেম স্ট্যাটাস"""
    stats = db.get_backup_stats()
    return {
        "status": "active",
        "total_files": stats.get('total_files', 0),
        "total_size_mb": stats.get('total_size_mb', 0),
        "last_backup": stats.get('last_backup_time')
    }

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    device_id: str = Header(...),
    verified: bool = Depends(verify_api_key)
):
    """ফাইল আপলোড"""
    try:
        # টেম্প ফাইল সেভ
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Cloudinary-তে আপলোড
        upload_result = cloudinary.upload_file(temp_path, tags=[f"device:{device_id}"])
        
        if not upload_result['success']:
            raise HTTPException(status_code=500, detail=upload_result['error'])
        
        # ডাটাবেজে সেভ
        file_data = {
            'file_hash': upload_result['file_hash'],
            'filename': upload_result['filename'],
            'file_size': upload_result['file_size'],
            'file_type': upload_result['file_type'],
            'cloudinary_id': upload_result['cloudinary_id'],
            'cloudinary_url': upload_result['cloudinary_url'],
            'original_path': upload_result['original_path'],
            'device_name': device_id
        }
        
        db.add_file(file_data)
        
        # টেম্প ফাইল ডিলিট
        import os
        os.remove(temp_path)
        
        return {
            "success": True,
            "message": "ফাইল আপলোড সফল",
            "file_id": upload_result['cloudinary_id'],
            "download_url": upload_result['cloudinary_url']
        }
        
    except Exception as e:
        logger.error(f"❌ API আপলোড এরর: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def get_files(
    limit: int = 50,
    offset: int = 0,
    verified: bool = Depends(verify_api_key)
):
    """ফাইল লিস্ট"""
    files = db.get_all_files(limit=100)[offset:offset+limit]
    return {
        "files": files,
        "count": len(files),
        "total": db.get_backup_stats()['total_files']
    }

@app.get("/api/search")
async def search_files(
    query: str,
    verified: bool = Depends(verify_api_key)
):
    """ফাইল সার্চ"""
    results = db.search_files(query)
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }

@app.delete("/api/file/{file_hash}")
async def delete_file(
    file_hash: str,
    verified: bool = Depends(verify_api_key)
):
    """ফাইল ডিলিট"""
    file_info = db.get_file_by_hash(file_hash)
    if not file_info:
        raise HTTPException(status_code=404, detail="ফাইল পাওয়া যায়নি")
    
    # Cloudinary থেকে ডিলিট
    cloudinary.delete_file(file_info['cloudinary_id'])
    
    # ডাটাবেজ থেকে ডিলিট
    db.delete_file(file_hash)
    
    return {"success": True, "message": "ফাইল ডিলিট সফল"}

@app.get("/api/device/register")
async def register_device(
    device_name: str,
    verified: bool = Depends(verify_api_key)
):
    """ডিভাইস রেজিস্টার"""
    device_id = security.generate_device_id()
    return {
        "device_id": device_id,
        "device_name": device_name,
        "api_key": Config.API_ACCESS_TOKEN,
        "server_url": f"http://{Config.SERVER_HOST}:{Config.SERVER_PORT}"
    }

@app.get("/api/scan")
async def scan_new_files(
    device_id: str = Header(...),
    verified: bool = Depends(verify_api_key)
):
    """নতুন ফাইল স্ক্যান"""
    new_files = []
    
    for folder in Config.MONITOR_FOLDERS:
        files = file_manager.get_new_files(folder)
        new_files.extend(files)
    
    return {
        "new_files": new_files,
        "count": len(new_files),
        "folders_scanned": len(Config.MONITOR_FOLDERS)
    }
