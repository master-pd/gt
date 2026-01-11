# ⚠️ IMPORTANT SAFETY AND SECURITY GUIDE

## 🛡️ SECURITY WARNINGS

### 1. **NEVER SHARE THIS APPLICATION**
   - This is for YOUR PERSONAL USE ONLY
   - Do not share APK with anyone
   - Do not share Telegram Bot token
   - Do not share Cloudinary credentials

### 2. **PROTECT YOUR API KEYS**
   - Bot Token
   - Cloudinary API Key & Secret
   - Your Telegram User ID
   
### 3. **REGULAR BACKUPS**
   - Export Cloudinary data monthly
   - Backup SQLite database
   - Keep local copies of important files

## 🔧 SETUP INSTRUCTIONS

### Step 1: Telegram Bot
1. Open Telegram, search for `@BotFather`
2. Send `/newbot` command
3. Choose a name: `My Auto Backup`
4. Copy the Bot Token
5. Get your User ID from `@userinfobot`

### Step 2: Cloudinary Account
1. Go to `cloudinary.com`
2. Create free account
3. Get: Cloud Name, API Key, API Secret

### Step 3: Configure `config.py`
```python
# Fill these values:
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
YOUR_TELEGRAM_USER_ID = 1234567890
CLOUDINARY_CLOUD_NAME = "your-cloud"
CLOUDINARY_API_KEY = "your-api-key"
CLOUDINARY_API_SECRET = "your-api-secret"
