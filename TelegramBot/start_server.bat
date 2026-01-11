@echo off
echo ========================================
echo     Auto Backup Pro Server
echo ========================================
echo.

REM Python environment check
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python ইনস্টল করা নেই!
    echo Python 3.12+ ইন্সটল করুন: https://python.org
    pause
    exit /b 1
)

echo ✅ Python পাওয়া গেছে

REM Install requirements
echo.
echo 📦 Requirements ইন্সটল করা হচ্ছে...
pip install -r requirements.txt

echo.
echo 🔧 কনফিগারেশন চেক...
python -c "from config import Config; Config.validate_config()"

if errorlevel 1 (
    echo ❌ কনফিগারেশন ভুল!
    echo config.py ফাইল চেক করুন
    pause
    exit /b 1
)

echo.
echo 🚀 সার্ভার শুরু হচ্ছে...
echo 📡 API Server: http://localhost:8000
echo 🤖 Telegram Bot: Active
echo 💾 Database: backup_database.db
echo.

REM Start server
python main.py

pause
