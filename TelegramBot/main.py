"""
MAIN.PY - মেইন সার্ভার ফাইল
"""

import asyncio
import logging
import signal
import sys
from threading import Thread
from typing import Optional

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import uvicorn

from config import Config
from bot_commands import (
    start_command, status_command, files_command,
    stats_command, help_command, handle_callback
)
from api_routes import app as fastapi_app

# লগিং সেটআপ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupServer:
    def __init__(self):
        self.telegram_app: Optional[Application] = None
        self.fastapi_server: Optional[Thread] = None
        self.is_running = False
    
    async def start_telegram_bot(self):
        """Telegram বট শুরু"""
        try:
            Config.validate_config()
            
            # Telegram Application তৈরি
            self.telegram_app = Application.builder().token(Config.BOT_TOKEN).build()
            
            # কমান্ড হ্যান্ডলার অ্যাড
            self.telegram_app.add_handler(CommandHandler("start", start_command))
            self.telegram_app.add_handler(CommandHandler("status", status_command))
            self.telegram_app.add_handler(CommandHandler("files", files_command))
            self.telegram_app.add_handler(CommandHandler("stats", stats_command))
            self.telegram_app.add_handler(CommandHandler("help", help_command))
            
            # কলব্যাক হ্যান্ডলার
            self.telegram_app.add_handler(CallbackQueryHandler(handle_callback))
            
            # বট শুরু
            await self.telegram_app.initialize()
            await self.telegram_app.start()
            await self.telegram_app.updater.start_polling()
            
            logger.info("✅ Telegram বট শুরু হয়েছে")
            
        except Exception as e:
            logger.error(f"❌ Telegram বট শুরু করতে ব্যর্থ: {e}")
            raise
    
    def start_fastapi_server(self):
        """FastAPI সার্ভার শুরু"""
        try:
            uvicorn.run(
                fastapi_app,
                host=Config.SERVER_HOST,
                port=Config.SERVER_PORT,
                log_level="info"
            )
        except Exception as e:
            logger.error(f"❌ FastAPI সার্ভার শুরু করতে ব্যর্থ: {e}")
            raise
    
    async def start(self):
        """সার্ভার শুরু"""
        logger.info("🚀 Auto Backup Pro সার্ভার শুরু হচ্ছে...")
        logger.info(f"📱 Owner ID: {Config.YOUR_TELEGRAM_USER_ID}")
        logger.info(f"🌐 API Server: http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
        
        self.is_running = True
        
        # FastAPI সার্ভার আলাদা থ্রেডে শুরু
        self.fastapi_server = Thread(target=self.start_fastapi_server, daemon=True)
        self.fastapi_server.start()
        
        # Telegram বট শুরু
        await self.start_telegram_bot()
        
        logger.info("✅ সব সার্ভিস সক্রিয়!")
        logger.info("📊 কমান্ড ব্যবহার করুন: /start, /status, /files")
        
        # শাটডাউন সিগনাল হ্যান্ডলিং
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum, frame):
        """সার্ভার বন্ধ"""
        logger.info("🛑 সার্ভার বন্ধ হচ্ছে...")
        self.is_running = False
        
        if self.telegram_app:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.telegram_app.stop())
            loop.run_until_complete(self.telegram_app.shutdown())
        
        logger.info("👋 সার্ভার বন্ধ হয়েছে")
        sys.exit(0)
    
    async def run_forever(self):
        """মেইন লুপ"""
        while self.is_running:
            await asyncio.sleep(1)

async def main():
    """মেইন ফাংশন"""
    server = BackupServer()
    
    try:
        await server.start()
        await server.run_forever()
    except KeyboardInterrupt:
        server.shutdown(None, None)
    except Exception as e:
        logger.error(f"❌ মেইন ফাংশন এরর: {e}")
        server.shutdown(None, None)

if __name__ == "__main__":
    # ASCII আর্ট
    print("""
    ╔══════════════════════════════════════╗
    ║     🤖 AUTO BACKUP PRO v1.0         ║
    ║     📱 Personal Backup System       ║
    ║     🔒 Private & Secure            ║
    ╚══════════════════════════════════════╝
    """)
    
    asyncio.run(main())
