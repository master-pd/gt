"""
BOT_COMMANDS.PY - Telegram বট কমান্ড
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import humanize

from config import Config
from database import DatabaseManager
from cloudinary_handler import CloudinaryManager
from security import SecurityManager

logger = logging.getLogger(__name__)
db = DatabaseManager()
cloudinary = CloudinaryManager()
security = SecurityManager()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """স্টার্ট কমান্ড"""
    user_id = update.effective_user.id
    
    if not security.verify_telegram_user(user_id):
        await update.message.reply_text(
            "❌ **অননুমোদিত অ্যাক্সেস!**\n"
            "এই বট শুধুমাত্র Owner ব্যবহার করতে পারবেন।"
        )
        return
    
    welcome_text = f"""
👋 **স্বাগতম {update.effective_user.first_name}!**

🤖 **Auto Backup Pro v{Config.VERSION}**
📱 **আপনার ব্যক্তিগত ব্যাকআপ সিস্টেম**

💾 **স্ট্যাটাস:**
• সক্রিয়
• Cloudinary সংযুক্ত
• অটো ব্যাকআপ সক্রিয়

📂 **মনিটর করা ফোল্ডার:**
{chr(10).join(f'• {folder}' for folder in Config.MONITOR_FOLDERS)}

🔧 **কমান্ড লিস্ট:**
/status - ব্যাকআপ স্ট্যাটাস
/files - ফাইল লিস্ট
/stats - ডিটেইলড স্ট্যাটিসটিক্স
/help - সাহায্য
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ব্যাকআপ স্ট্যাটাস"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    stats = db.get_backup_stats()
    
    status_text = f"""
📊 **ব্যাকআপ স্ট্যাটাস**

✅ **সর্বমোট ফাইল:** {stats.get('total_files', 0)}
💾 **সর্বমোট সাইজ:** {stats.get('total_size_mb', 0):.2f} MB
🕐 **শেষ ব্যাকআপ:** {stats.get('last_backup_time', 'কখনো না')}

📁 **মনিটর করা ফোল্ডার:** {len(Config.MONITOR_FOLDERS)}
🔒 **সিকিউরিটি:** সক্রিয়
☁️ **Cloudinary:** সংযুক্ত
"""
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ফাইল লিস্ট"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    files = db.get_all_files(limit=10)
    
    if not files:
        await update.message.reply_text("📭 **কোনো ফাইল নেই**")
        return
    
    files_text = "📂 **সর্বশেষ ১০ ফাইল:**\n\n"
    
    for i, file in enumerate(files[:10], 1):
        file_size_mb = file['file_size'] / (1024 * 1024)
        files_text += f"{i}. **{file['filename']}**\n"
        files_text += f"   📏 {file_size_mb:.2f} MB | 📅 {file['upload_date']}\n"
        files_text += f"   🔗 [ডাউনলোড]({file['cloudinary_url']})\n\n"
    
    keyboard = [
        [InlineKeyboardButton("📊 সব ফাইল দেখুন", callback_data="all_files")],
        [InlineKeyboardButton("🔍 সার্চ করুন", callback_data="search_files")],
        [InlineKeyboardButton("🗑️ ডিলিট মোড", callback_data="delete_mode")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        files_text,
        parse_mode='Markdown',
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ডিটেইলড স্ট্যাটিসটিক্স"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    stats = db.get_backup_stats()
    cloud_files = cloudinary.list_files(max_results=50)
    
    stats_text = f"""
📈 **ডিটেইলড স্ট্যাটিসটিক্স**

📊 **লোকাল ডাটাবেজ:**
• সর্বমোট ফাইল: {stats.get('total_files', 0)}
• সর্বমোট সাইজ: {stats.get('total_size_mb', 0):.2f} MB
• শেষ আপডেট: {stats.get('last_backup_time', 'N/A')}

☁️ **Cloudinary:**
• ফাইল সংখ্যা: {len(cloud_files)}
• সর্বশেষ আপলোড: {cloud_files[0]['created_at'] if cloud_files else 'N/A'}

⚙️ **সিস্টেম:**
• মনিটর করা ফোল্ডার: {len(Config.MONITOR_FOLDERS)}
• সর্বোচ্চ ফাইল সাইজ: {Config.MAX_FILE_SIZE_MB} MB
• অনুমোদিত ফাইল টাইপ: {len(Config.ALLOWED_EXTENSIONS)}
"""
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """হেল্প কমান্ড"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    help_text = """
🆘 **সাহায্য - Auto Backup Pro**

🤖 **বট কমান্ড:**
/start - বট শুরু করুন
/status - ব্যাকআপ স্ট্যাটাস দেখুন
/files - ফাইল লিস্ট দেখুন
/stats - ডিটেইলড স্ট্যাটিসটিক্স
/help - এই মেসেজ দেখুন

📱 **Android অ্যাপ:**
• অটোমেটিক ব্যাকআপ
• ব্যাকগ্রাউন্ড সার্ভিস
• রিয়েল-টাইম সিঙ্ক

🔒 **সিকিউরিটি:**
• শুধুমাত্র আপনার অ্যাক্সেস
• এন্ড-টু-এন্ড এনক্রিপশন
• সিকিউর ক্লাউড স্টোরেজ

⚠️ **সতর্কতা:**
• এই বট শেয়ার করবেন না
• API Keys সিকিউর রাখুন
• রেগুলার ব্যাকআপ নিন
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """কলব্যাক হ্যান্ডলার"""
    query = update.callback_query
    await query.answer()
    
    if not security.verify_telegram_user(query.from_user.id):
        return
    
    callback_data = query.data
    
    if callback_data == "all_files":
        files = db.get_all_files(limit=50)
        files_text = "📂 **সব ফাইল:**\n\n"
        
        for i, file in enumerate(files, 1):
            files_text += f"{i}. {file['filename']}\n"
        
        await query.edit_message_text(files_text[:4000])
    
    elif callback_data == "search_files":
        await query.edit_message_text(
            "🔍 **ফাইল সার্চ**\n\n"
            "সার্চ করতে ফাইল নাম টাইপ করুন।\n"
            "উদাহরণ: `vacation` বা `invoice.pdf`"
        )
