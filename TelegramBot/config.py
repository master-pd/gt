"""
CONFIG.PY - কনফিগারেশন ফাইল
.env ছাড়াই সবকিছু এখানে
"""

class Config:
    # ==================== YOUR PERSONAL SETTINGS ====================
    # এখানে আপনার তথ্য দিন
    TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # @BotFather থেকে নিন
    YOUR_TELEGRAM_USER_ID = 1234567890  # আপনার Telegram User ID
    YOUR_PHONE_NUMBER = "+8801847634486"  # আপনার ফোন নাম্বার
    
    # Cloudinary Settings (cloudinary.com থেকে নিন)
    CLOUDINARY_CLOUD_NAME = "your-cloud-name"
    CLOUDINARY_API_KEY = "your-api-key"
    CLOUDINARY_API_SECRET = "your-api-secret"
    
    # ==================== SERVER SETTINGS ====================
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 800  
    SECRET_KEY = "your-32-character-secret-key-change-this-now"
    
    # ==================== BACKUP SETTINGS ====================
    # কোন ফোল্ডারগুলো ব্যাকআপ হবে
    MONITOR_FOLDERS = [
        "/DCIM/Camera",      # ক্যামেরার ছবি
        "/DCIM/Screenshots", # স্ক্রিনশট
        "/Download",         # ডাউনলোড ফাইল
        "/Documents",        # ডকুমেন্টস
        "/Pictures",         # পিকচার্স
        "/Music",           # মিউজিক
        "/Movies"           # মুভিজ
    ]
    
    # কোন ফাইল টাইপ ব্যাকআপ হবে
    ALLOWED_EXTENSIONS = [
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
        # Videos
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.txt', '.rtf',
        # Audio
        '.mp3', '.wav', '.aac', '.flac', '.m4a',
        # Archives
        '.zip', '.rar', '.7z',
        # Apps
        '.apk'
    ]
    
    # ম্যাক্সিমাম ফাইল সাইজ (MB)
    MAX_FILE_SIZE_MB = 100
    
    # ==================== DATABASE SETTINGS ====================
    DATABASE_NAME = "backup_database.db"
    
    # ==================== SECURITY SETTINGS ====================
    # এনক্রিপশন কি (পরিবর্তন করুন)
    ENCRYPTION_KEY = b"your-encryption-key-32bytes!!"
    
    # API Access Token (Android App ব্যবহার করবে)
    API_ACCESS_TOKEN = "your-api-access-token-12345"
    
    # ==================== NOTIFICATION SETTINGS ====================
    SEND_NOTIFICATIONS = True
    NOTIFICATION_CHAT_ID = YOUR_TELEGRAM_USER_ID
    
    @classmethod
    def get_max_file_size(cls):
        return cls.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @classmethod
    def validate_config(cls):
        """কনফিগারেশন ভ্যালিডেশন"""
        errors = []
        
        if cls.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            errors.append("TELEGRAM_BOT_TOKEN সেট করুন")
        
        if cls.YOUR_TELEGRAM_USER_ID == 1234567890:
            errors.append("YOUR_TELEGRAM_USER_ID সেট করুন")
        
        if cls.CLOUDINARY_CLOUD_NAME == "your-cloud-name":
            errors.append("Cloudinary কনফিগার করুন")
        
        if errors:
            raise ValueError(f"কনফিগারেশন এরর: {', '.join(errors)}")
        
        print("✅ কনফিগারেশন ভ্যালিডেশন সফল!")
        return True
