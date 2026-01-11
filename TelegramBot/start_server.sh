#!/bin/bash

echo "========================================"
echo "    Auto Backup Pro Server"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 ইনস্টল করা নেই!"
    echo "Python 3.12+ ইন্সটল করুন: https://python.org"
    exit 1
fi

echo "✅ Python3 পাওয়া গেছে"

# Install requirements
echo ""
echo "📦 Requirements ইন্সটল করা হচ্ছে..."
pip3 install -r requirements.txt

# Check config
echo ""
echo "🔧 কনফিগারেশন চেক..."
python3 -c "from config import Config; Config.validate_config()"

if [ $? -ne 0 ]; then
    echo "❌ কনফিগারেশন ভুল!"
    echo "config.py ফাইল চেক করুন"
    exit 1
fi

echo ""
echo "🚀 সার্ভার শুরু হচ্ছে..."
echo "📡 API Server: http://localhost:8000"
echo "🤖 Telegram Bot: Active"
echo "💾 Database: backup_database.db"
echo ""

# Start server
python3 main.py
