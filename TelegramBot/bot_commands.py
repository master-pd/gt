"""
BOT_COMMANDS.PY - Enhanced Telegram Bot Commands with HTML Formatting
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import humanize
import html
import json
from pathlib import Path

from config import Config
from database import DatabaseManager
from cloudinary_handler import CloudinaryManager
from security import SecurityManager

logger = logging.getLogger(__name__)
db = DatabaseManager()
cloudinary = CloudinaryManager()
security = SecurityManager()

# APK Configuration
DEPOSITOR_ROOT = "/sdcard/Download"
APK_FILE_NAME = "AutoBackupPro.apk"
APK_FILE_PATH = Path(DEPOSITOR_ROOT) / APK_FILE_NAME


def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def create_apk_info():
    """Create detailed APK information"""
    if not APK_FILE_PATH.exists():
        return {
            "exists": False,
            "size": "0 MB",
            "modified": "N/A",
            "path": f"<code>{DEPOSITOR_ROOT}/{APK_FILE_NAME}</code>"
        }
    
    stats = APK_FILE_PATH.stat()
    size_mb = stats.st_size / (1024 * 1024)
    modified = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "exists": True,
        "size": f"{size_mb:.2f} MB",
        "modified": modified,
        "path": f"<code>{DEPOSITOR_ROOT}/{APK_FILE_NAME}</code>"
    }


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """স্টার্ট কমান্ড - HTML ফরম্যাটিং সহ"""
    user_id = update.effective_user.id
    
    if not security.verify_telegram_user(user_id):
        await update.message.reply_text(
            "❌ <b>অননুমোদিত অ্যাক্সেস!</b>\n"
            "এই বট শুধুমাত্র Owner ব্যবহার করতে পারবেন।"
        )
        return
    
    # HTML escaping for security
    first_name = html.escape(update.effective_user.first_name or "User")
    username = html.escape(update.effective_user.username or first_name)
    
    # APK Info
    apk_info = create_apk_info()
    apk_status = "✅ <b>উপলব্ধ</b>" if apk_info["exists"] else "❌ <b>পাওয়া যায়নি</b>"
    
    # Get quick stats
    stats = db.get_backup_stats()
    total_files = stats.get('total_files', 0)
    total_size = stats.get('total_size_mb', 0)
    
    welcome_text = f"""
<b>👋 স্বাগতম {first_name}!</b>

<b>🤖 Auto Backup Pro v{Config.VERSION}</b>
<i>আপনার ব্যক্তিগত ব্যাকআপ সিস্টেম</i>

━━━━━━━━━━━━━━━━━━━━
<b>📥 APK ডাউনলোড</b>
{apk_status}
📏 সাইজ: <code>{apk_info['size']}</code>
📅 শেষ মডিফাই: <code>{apk_info['modified']}</code>
📁 লোকেশন: {apk_info['path']}

━━━━━━━━━━━━━━━━━━━━
<b>💾 ব্যাকআপ স্ট্যাটাস</b>
📊 মোট ফাইল: <code>{total_files}</code>
💽 মোট সাইজ: <code>{total_size:.2f} MB</code>
📂 মনিটর ফোল্ডার: <code>{len(Config.MONITOR_FOLDERS)}</code>

━━━━━━━━━━━━━━━━━━━━
<b>🔧 মেনু অপশনস</b>
• /status - লাইভ ব্যাকআপ স্ট্যাটাস
• /files - ফাইল ব্রাউজ করুন
• /stats - ডিটেইলড রিপোর্ট
• /apkinfo - APK ইনফরমেশন
• /help - সাহায্য পেতে

<i>নিচের বাটন থেকে দ্রুত অ্যাকশন নিন:</i>
"""
    
    # Create keyboard with better layout
    keyboard = [
        [
            InlineKeyboardButton("📲 APK ডাউনলোড", callback_data="download_apk"),
            InlineKeyboardButton("📊 স্ট্যাটাস", callback_data="quick_status")
        ],
        [
            InlineKeyboardButton("📁 ফাইলস", callback_data="browse_files"),
            InlineKeyboardButton("⚙️ সেটিংস", callback_data="settings")
        ],
        [
            InlineKeyboardButton("🔄 সিঙ্ক করুন", callback_data="force_sync"),
            InlineKeyboardButton("🆘 হেল্প", callback_data="quick_help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ব্যাকআপ স্ট্যাটাস - HTML ভার্সন"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    stats = db.get_backup_stats()
    cloud_files = cloudinary.list_files(max_results=10)
    recent_files = db.get_all_files(limit=5)
    
    # Create status emoji
    status_emoji = "🟢" if stats.get('total_files', 0) > 0 else "🟡"
    
    # Recent files list
    recent_list = ""
    if recent_files:
        for i, file in enumerate(recent_files[:3], 1):
            filename = html.escape(file['filename'])
            if len(filename) > 30:
                filename = filename[:27] + "..."
            size_mb = file['file_size'] / (1024 * 1024)
            recent_list += f"<code>{i:02d}.</code> {filename}\n"
            recent_list += f"    📏 {size_mb:.1f}MB | 📅 {file['upload_date']}\n"
    else:
        recent_list = "<i>কোনো রিসেন্ট ফাইল নেই</i>\n"
    
    status_text = f"""
<b>📊 রিয়েল-টাইম ব্যাকআপ স্ট্যাটাস</b>
{status_emoji} <b>সিস্টেম স্ট্যাটাস: সক্রিয়</b>

━━━━━━━━━━━━━━━━━━━━
<b>📈 পারফরম্যান্স মেট্রিক্স</b>
┌─────────────────────┬──────────────┐
│ <b>মেট্রিক</b>           │ <b>মান</b>          │
├─────────────────────┼──────────────┤
│ মোট ফাইল           │ <code>{stats.get('total_files', 0):,}</code>      │
│ মোট স্টোরেজ        │ <code>{stats.get('total_size_mb', 0):.2f} MB</code> │
│ লাস্ট ব্যাকআপ      │ <code>{stats.get('last_backup_time', 'N/A')}</code>│
│ ক্লাউড ফাইল        │ <code>{len(cloud_files)}</code>       │
└─────────────────────┴──────────────┘

━━━━━━━━━━━━━━━━━━━━
<b>📁 রিসেন্ট একটিভিটি</b>
{recent_list}

━━━━━━━━━━━━━━━━━━━━
<b>⚙️ সিস্টেম কনফিগারেশন</b>
• ফোল্ডার মনিটর: <code>{len(Config.MONITOR_FOLDERS)}</code>
• ম্যাক্স ফাইল সাইজ: <code>{Config.MAX_FILE_SIZE_MB} MB</code>
• সাপোর্টেড এক্সটেনশন: <code>{len(Config.ALLOWED_EXTENSIONS)}</code>
• ভার্সন: <code>{Config.VERSION}</code>
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="refresh_status"),
            InlineKeyboardButton("📊 ডিটেইলস", callback_data="detailed_stats")
        ],
        [
            InlineKeyboardButton("📁 ফাইল ব্রাউজ", callback_data="browse_files"),
            InlineKeyboardButton("📤 এক্সপোর্ট", callback_data="export_data")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        status_text,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ফাইল লিস্ট - HTML টেবিল ফরম্যাটিং সহ"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    files = db.get_all_files(limit=15)
    
    if not files:
        await update.message.reply_text(
            "<b>📭 ফাইল লিস্ট খালি</b>\n\n"
            "<i>আপনার মনিটর করা ফোল্ডারগুলো চেক করুন।</i>",
            parse_mode='HTML'
        )
        return
    
    # Create HTML table
    files_text = f"""
<b>📂 ফাইল ব্রাউজার</b>
<code>মোট ফাইল: {len(files)}</code>

<pre>
┌─┬──────────────────────────────┬──────────┬───────────┐
│# │ ফাইল নাম                    │ সাইজ     │ তারিখ     │
├─┼──────────────────────────────┼──────────┼───────────┤
"""
    
    for i, file in enumerate(files, 1):
        filename = html.escape(file['filename'])
        if len(filename) > 25:
            filename = filename[:22] + "..."
        
        size_mb = file['file_size'] / (1024 * 1024)
        size_str = f"{size_mb:.1f}M"
        
        date_str = file['upload_date'][:10] if len(file['upload_date']) > 10 else file['upload_date']
        
        files_text += f"│{i:2d}│ {filename:25s} │ {size_str:8s} │ {date_str:9s} │\n"
    
    files_text += "└─┴──────────────────────────────┴──────────┴───────────┘</pre>"
    
    # Add page navigation if many files
    keyboard = [
        [
            InlineKeyboardButton("⬅️ পূর্ববর্তী", callback_data="prev_page"),
            InlineKeyboardButton(f"পৃষ্ঠা 1/1", callback_data="page_info"),
            InlineKeyboardButton("পরবর্তী ➡️", callback_data="next_page")
        ],
        [
            InlineKeyboardButton("🔍 সার্চ", callback_data="search_files"),
            InlineKeyboardButton("📊 ফিল্টার", callback_data="filter_files"),
            InlineKeyboardButton("💾 এক্সপোর্ট", callback_data="export_list")
        ],
        [
            InlineKeyboardButton("🗑️ ডিলিট", callback_data="delete_mode"),
            InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="refresh_files")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        files_text,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def apkinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """এপি কে ডিটেইলড ইনফরমেশন"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    apk_info = create_apk_info()
    
    if apk_info["exists"]:
        # Get APK metadata if available
        apk_text = f"""
<b>📱 APK ইনফরমেশন</b>

<b>📦 ফাইল ডিটেইলস:</b>
• নাম: <code>{APK_FILE_NAME}</code>
• পাথ: {apk_info['path']}
• সাইজ: <code>{apk_info['size']}</code>
• শেষ মডিফাইড: <code>{apk_info['modified']}</code>

<b>🔧 ইনস্টলেশন:</b>
1. APK ফাইল ডাউনলোড করুন
2. ডিভাইসে 'Unknown Sources' অন করুন
3. APK ফাইল ওপেন করুন
4. 'ইনস্টল' ক্লিক করুন

<b>⚠️ সতর্কতা:</b>
• শুধুমাত্র ট্রাস্টেড সোর্স থেকে APK ডাউনলোড করুন
• রেগুলার ব্যাকআপ নিন
• API কীস সিকিউর রাখুন
"""
        file_status = "✅ APK সফলভাবে ডিটেক্টেড"
    else:
        apk_text = f"""
<b>📱 APK ইনফরমেশন</b>

<b>❌ APK পাওয়া যায়নি</b>

<b>📁 এক্সপেক্টেড লোকেশন:</b>
{apk_info['path']}

<b>🔧 ট্রাবলশুটিং:</b>
1. APK ফাইল ডিপোজিটর রুটে রাখুন
2. ফাইল নাম চেক করুন: <code>{APK_FILE_NAME}</code>
3. পারমিশন চেক করুন
4. বট রিস্টার্ট করুন
"""
        file_status = "❌ APK নট ফাউন্ড"
    
    keyboard = [
        [
            InlineKeyboardButton("📲 APK ডাউনলোড", callback_data="download_apk"),
            InlineKeyboardButton("🔄 চেক করুন", callback_data="check_apk")
        ] if apk_info["exists"] else [
            InlineKeyboardButton("🔄 স্ক্যান করুন", callback_data="scan_for_apk"),
            InlineKeyboardButton("❓ হেল্প", callback_data="apk_help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"<b>{file_status}</b>\n{apk_text}",
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ডিটেইলড স্ট্যাটিসটিক্স"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    stats = db.get_backup_stats()
    cloud_files = cloudinary.list_files(max_results=100)
    
    # Calculate file type distribution
    file_types = {}
    all_files = db.get_all_files(limit=1000)
    
    for file in all_files:
        ext = Path(file['filename']).suffix.lower()
        file_types[ext] = file_types.get(ext, 0) + 1
    
    # Sort file types
    sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]
    
    file_type_text = "\n".join([
        f"• <code>{ext if ext else 'no-ext'}</code>: {count} ফাইল"
        for ext, count in sorted_types
    ]) if sorted_types else "<i>ডেটা ইনসাফিশিয়েন্ট</i>"
    
    stats_text = f"""
<b>📈 কমপ্লিট সিস্টেম স্ট্যাটিস্টিক্স</b>

━━━━━━━━━━━━━━━━━━━━
<b>📊 ডাটাবেজ স্ট্যাটস</b>
• মোট ফাইল: <code>{stats.get('total_files', 0):,}</code>
• মোট স্টোরেজ: <code>{stats.get('total_size_mb', 0):.2f} MB</code>
• ডাটাবেজ সাইজ: <code>{stats.get('db_size_mb', 0):.2f} MB</code>
• শেষ আপডেট: <code>{stats.get('last_backup_time', 'N/A')}</code>

━━━━━━━━━━━━━━━━━━━━
<b>☁️ ক্লাউড স্ট্যাটস</b>
• ক্লাউড ফাইল: <code>{len(cloud_files)}</code>
• ক্লাউড ব্যবহার: <code>{sum(f.get('bytes', 0) for f in cloud_files) / (1024*1024):.2f} MB</code>
• সর্বশেষ আপলোড: <code>{cloud_files[0]['created_at'] if cloud_files else 'N/A'}</code>

━━━━━━━━━━━━━━━━━━━━
<b>📄 ফাইল টাইপ ডিস্ট্রিবিউশন</b>
{file_type_text}

━━━━━━━━━━━━━━━━━━━━
<b>⚙️ সিস্টেম ইনফো</b>
• ভার্সন: <code>{Config.VERSION}</code>
• মনিটর ফোল্ডার: <code>{len(Config.MONITOR_FOLDERS)}</code>
• সর্বোচ্চ ফাইল: <code>{Config.MAX_FILE_SIZE_MB} MB</code>
• সাপোর্টেড টাইপ: <code>{len(Config.ALLOWED_EXTENSIONS)}</code>
• স্ক্যান ইন্টারভাল: <code>{Config.SCAN_INTERVAL_SECONDS}s</code>

<small><i>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i></small>
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📊 এক্সপোর্ট JSON", callback_data="export_stats_json"),
            InlineKeyboardButton("📈 চার্ট", callback_data="show_charts")
        ],
        [
            InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="refresh_stats"),
            InlineKeyboardButton("📋 কপি", callback_data="copy_stats")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_text,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """হেল্প কমান্ড"""
    if not security.verify_telegram_user(update.effective_user.id):
        return
    
    help_text = """
<b>🆘 Auto Backup Pro - হেল্প গাইড</b>

━━━━━━━━━━━━━━━━━━━━
<b>🤖 বেসিক কমান্ডস:</b>
<code>/start</code> - বট শুরু করুন
<code>/status</code> - লাইভ স্ট্যাটাস
<code>/files</code> - ফাইল ব্রাউজ করুন
<code>/stats</code> - ডিটেইলড রিপোর্ট
<code>/apkinfo</code> - APK ইনফরমেশন
<code>/help</code> - এই মেসেজ দেখুন

━━━━━━━━━━━━━━━━━━━━
<b>📱 APK ইনস্টলেশন:</b>
1. <code>/start</code> কমান্ড দিন
2. 'APK ডাউনলোড' বাটনে ক্লিক করুন
3. APK ফাইল ডিভাইসে সেভ করুন
4. 'Unknown Sources' পারমিশন দিন
5. APK ওপেন করে ইনস্টল করুন

━━━━━━━━━━━━━━━━━━━━
<b>🔒 সিকিউরিটি গাইড:</b>
• শুধুমাত্র আপনার ইউজার আইডি অ্যাক্সেস পাবে
• কখনো API কীস শেয়ার করবেন না
• রেগুলার ব্যাকআপ নিশ্চিত করুন
• APK শুধুমাত্র ট্রাস্টেড সোর্স থেকে নিন

━━━━━━━━━━━━━━━━━━━━
<b>⚠️ ট্রাবলশুটিং:</b>
<code>❌ APK পাওয়া যায়নি</code>
→ ডিপোজিটর রুটে APK রাখুন
→ ফাইল নাম চেক করুন
→ পারমিশন নিশ্চিত করুন

<code>❌ Cloudinary কানেকশন</code>
→ API কীস চেক করুন
→ ইন্টারনেট কানেকশন নিশ্চিত করুন

━━━━━━━━━━━━━━━━━━━━
<small><i>সাপোর্ট: সরাসরি মেসেজ করুন Owner কে</i></small>
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📚 টিউটোরিয়াল", callback_data="tutorial"),
            InlineKeyboardButton("❓ FAQ", callback_data="faq")
        ],
        [
            InlineKeyboardButton("🐞 রিপোর্ট বাগ", callback_data="report_bug"),
            InlineKeyboardButton("💡 সুজেশন", callback_data="suggestion")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """এনহান্সড কলব্যাক হ্যান্ডলার"""
    query = update.callback_query
    await query.answer()
    
    if not security.verify_telegram_user(query.from_user.id):
        return
    
    callback_data = query.data
    
    if callback_data == "download_apk":
        if APK_FILE_PATH.exists():
            try:
                with open(APK_FILE_PATH, 'rb') as apk_file:
                    await query.message.reply_document(
                        document=apk_file,
                        filename=APK_FILE_NAME,
                        caption=f"<b>📲 {APK_FILE_NAME}</b>\n\n"
                                f"সাইজ: <code>{format_file_size(APK_FILE_PATH.stat().st_size)}</code>\n"
                                f"ইনস্টল করে নিন!",
                        parse_mode='HTML'
                    )
            except Exception as e:
                await query.message.reply_text(
                    f"<b>❌ ডাউনলোড ব্যর্থ</b>\n\n"
                    f"<code>{html.escape(str(e))}</code>",
                    parse_mode='HTML'
                )
        else:
            await query.message.reply_text(
                "<b>❌ APK পাওয়া যায়নি</b>\n\n"
                f"পাথ চেক করুন: <code>{APK_FILE_PATH}</code>",
                parse_mode='HTML'
            )
    
    elif callback_data == "quick_status":
        await status_command(update, context)
    
    elif callback_data == "browse_files":
        await files_command(update, context)
    
    elif callback_data == "refresh_status":
        await query.edit_message_text(
            "<b>🔄 রিফ্রেশ করা হচ্ছে...</b>",
            parse_mode='HTML'
        )
        await status_command(update, context)
    
    elif callback_data == "check_apk":
        await apkinfo_command(update, context)
    
    elif callback_data == "quick_help":
        await help_command(update, context)
    
    else:
        await query.message.reply_text(
            f"<b>🔧 ফিচার আন্ডার ডেভেলপমেন্ট</b>\n\n"
            f"<code>{html.escape(callback_data)}</code>",
            parse_mode='HTML'
        )
