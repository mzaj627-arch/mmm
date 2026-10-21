# -*- coding: utf-8 -*-
"""
TikTok Mass Report Bot — Ultimate Telegram & Engine Edition
Integrated with Both New (ttsign) and Classic Signatures (XGorgon / XLadon)
Run: python bot.py
"""

import time
import os
import re
import sys
import random
import threading
import queue
import requests
import hashlib
import base64
import urllib3
import urllib.parse
import secrets
import json
from flask import Flask

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from fake_useragent import UserAgent
from user_agent import generate_user_agent
import telebot
from telebot import types

# =========================================================
# إعداد سيرفر الويب (لإبقاء البوت مستيقظاً 24/7 على Render)
# =========================================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "⚡ TikTok Mass Report Bot is running 24/7 successfully!"

# =========================================================
# التوكن
# =========================================================
BOT_TOKEN = "8546456262:AAG30xMBedX0nLVHjvRLpiCLXuNNAf9hFPg"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

DATA_DIR = os.path.join(os.getcwd(), "bot_data")
os.makedirs(DATA_DIR, exist_ok=True)

# ==========================================
# دمج التوقيعين (الجديد ttsign والتقليدي XGorgon & XLadon) في مكان واحد
# ==========================================
class ttsign:
    def __init__(self, params, data, cookies):
        self.params = params
        self.data = data
        self.cookies = cookies

    def hash(self, data):
        return hashlib.md5(data.encode()).hexdigest()

    def get_base_string(self):
        base_str = self.hash(self.params)
        base_str = base_str + self.hash(self.data) if self.data else base_str + "0" * 32
        base_str = base_str + self.hash(self.cookies) if self.cookies else base_str + "0" * 32
        return base_str

    def get_value(self):
        return self.encrypt(self.get_base_string())

    def encrypt(self, data):
        unix = time.time()
        length = 0x14
        key = [0xDF, 0x77, 0xB9, 0x40, 0xB9, 0x9B, 0x84, 0x83, 0xD1, 0xB9, 0xCB, 0xD1, 0xF7, 0xC2, 0xB9, 0x85, 0xC3, 0xD0, 0xFB, 0xC3]
        param_list = []
        for i in range(0, 12, 4):
            temp = data[8 * i : 8 * (i + 1)]
            for j in range(4):
                H = int(temp[j * 2 : (j + 1) * 2], 16)
                param_list.append(H)
        param_list.extend([0x0, 0x6, 0xB, 0x1C])
        H = int(hex(int(unix)), 16)
        param_list.append((H & 0xFF000000) >> 24)
        param_list.append((H & 0x00FF0000) >> 16)
        param_list.append((H & 0x0000FF00) >> 8)
        param_list.append((H & 0x000000FF) >> 0)
        eor = [A ^ B for A, B in zip(param_list, key)]
        for i in range(length):
            C_val = self.reverse(eor[i])
            D = eor[(i + 1) % length]
            E = C_val ^ D
            F = self.rbit(E)
            H_val = ((F ^ 0xFFFFFFFF) ^ length) & 0xFF
            eor[i] = H_val
        result = "".join(self.hex_string(p) for p in eor)
        return {"x-ss-req-ticket": str(int(unix * 1000)), "x-khronos": str(int(unix)), "x-gorgon": "0404b0d30000" + result}

    def rbit(self, num):
        tmp = bin(num)[2:]
        while len(tmp) < 8:
            tmp = "0" + tmp
        return int(tmp[::-1], 2)

    def hex_string(self, num):
        return hex(num)[2:].zfill(2)

    def reverse(self, num):
        tmp = self.hex_string(num)
        return int(tmp[1:] + tmp[:1], 16)

def sign(params, payload="", cookies=""):
    return ttsign(params, payload, cookies).get_value()


class XGorgon:
    KEY = [
        0xDF, 0x77, 0xB9, 0x40, 0xB9, 0x9B, 0x84, 0x83,
        0xD1, 0xB9, 0xCB, 0xD1, 0xF7, 0xC2, 0xB9, 0x85,
        0xC3, 0xD0, 0xFB, 0xC3,
    ]
    PREFIX = "0404b0d30000"
    LENGTH = 0x14

    @classmethod
    def sign(cls, params, payload="", cookies=""):
        new_signed = sign(params, payload, cookies)
        return new_signed


class XLadon:
    DELTA = 0x9E3779B9
    MASK = 0xFFFFFFFF

    @staticmethod
    def encrypt(khronos, lc="1611921764", aid="1233"):
        rand = os.urandom(4)
        data = f"{khronos}-{lc}-{aid}".encode()
        key = hashlib.md5(rand + aid.encode()).digest()
        v = []
        for i in range(0, len(data), 4):
            chunk = data[i:i+4].ljust(4, b'\x00')
            v.append(int.from_bytes(chunk, 'little'))
        while len(v) < 2:
            v.append(0)
        k = [int.from_bytes(key[i*4:(i+1)*4], 'little') for i in range(4)]
        enc = XLadon._xxtea(v, k)
        out = b"".join(val.to_bytes(4, 'little') for val in enc)
        return base64.b64encode(rand + out).decode()

    @staticmethod
    def _xxtea(v, k):
        n = len(v)
        if n < 2:
            return v
        rounds = 6 + 52 // n
        s = 0
        z = v[n - 1]
        r = list(v)
        for _ in range(rounds):
            s = (s + XLadon.DELTA) & XLadon.MASK
            e = (s >> 2) & 3
            for p in range(n - 1):
                y = r[p + 1]
                mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((s ^ y) + (k[(p & 3) ^ e] ^ z))
                r[p] = (r[p] + mx) & XLadon.MASK
                z = r[p]
            p = n - 1
            y = r[0]
            mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((s ^ y) + (k[(p & 3) ^ e] ^ z))
            r[p] = (r[p] + mx) & XLadon.MASK
            z = r[p]
        return r


def get_signed_headers(params_str, payload_str="", cookies_str=""):
    gorgon = XGorgon.sign(params_str, payload_str, cookies_str)
    khronos = int(gorgon["x-khronos"])
    ladon = XLadon.encrypt(khronos)
    stub = hashlib.md5(payload_str.encode()).hexdigest().upper() if payload_str else "A1B2C3"

    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Host': 'www.tiktok.com',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': generate_user_agent(),
        "x-gorgon": gorgon["x-gorgon"],
        "x-argus": "8gHi..." + gorgon["x-gorgon"][-10:],
        "x-ladon": ladon,
        "x-khronos": gorgon["x-khronos"],
        "x-ss-stub": stub,
        "x-ss-req-ticket": gorgon["x-ss-req-ticket"],
    }


# ==========================================
# إعدادات الألوان والمتغيرات
# ==========================================
LINE = "━━━━━━━━━━━━━━━━━━━━"

COUNTRIES = ['US', 'GB', 'DE', 'FR', 'CA', 'AU', 'JP', 'BR', 'IN', 'RU', 'SA', 'AE', 'EG', 'QA', 'KW', 'BH', 'OM', 'JO', 'LB']
DEVICES = [('SM-G975F', 'samsung'), ('SM-N975F', 'samsung'), ('SM-G988U', 'samsung'), ('SM-A705FN', 'samsung'), ('SM-A515U1', 'samsung'), ('SM-G955F', 'samsung'), ('CPH2359', 'OPPO'), ('CPH2457', 'OPPO'), ('RMX3501', 'realme'), ('RMX3085', 'realme')]

categories = [
    "المحتوى الجنسي (Porn)",
    "العنف والإيذاء (Violence)",
    "الكراهية والتحرش (Hate / Harassment)",
    "الانتحار وإيذاء النفس (Self-harm / Suicide)",
    "اضطرابات الأكل وصورة الجسم",
    "الأنشطة والتحديات الخطرة (Dangerous acts)",
    "المحتوى الصادم والبشع (Shocking)",
    "معلومات خاطئة / مضللة (Misinformation)",
    "السلوك المخادع والغش (Fraud / Scam)",
    "السلع والأنشطة الخاضعة للإرشادات",
    "بحث غير مناسب وغير ذي صلة",
]

subcategories = {
    1: [{'reason': '90087', 'category': 'porn', 'name': 'العري الصريح والمحتوى الجنسي'}],
    2: [{'reason': '90044', 'category': 'violence', 'name': 'محتوى يظهر إيذاء جسدي أو عنف'}],
    3: [{'reason': '90045', 'category': 'hate', 'name': 'الكلام الذي يحض على الكراهية أو التحرش'}],
    4: [{'reason': '90046', 'category': 'suicide', 'name': 'تشجيع أو عرض محاولة إيذاء النفس'}],
    5: [{'reason': '90047', 'category': 'eating_disorder', 'name': 'تشجيع على فقدان وزن غير صحي'}],
    6: [{'reason': '90048', 'category': 'dangerous_acts', 'name': 'تحديات وأفعال خطيرة'}],
    7: [{'reason': '90049', 'category': 'shocking', 'name': 'مشاهد دماء أو صور مقزّزة'}],
    8: [{'reason': '90050', 'category': 'misinformation', 'name': 'أخبار كاذبة ومعلومات مضللة'}],
    9: [{'reason': '90051', 'category': 'fraud', 'name': 'احتيال تجاري وخدع لجذب المشاهدين'}],
    10: [{'reason': '90052', 'category': 'regulated_goods', 'name': 'بيع منتجات غير قانونية'}],
    11: [{'reason': '90053', 'category': 'scam', 'name': 'اقتراح بحث غير لائق أو كلمات غير مناسبة'}],
}

STATE = {}
STATE_LOCK = threading.Lock()

def st(chat_id):
    with STATE_LOCK:
        if chat_id not in STATE:
            STATE[chat_id] = {
                "step": None,
                "category": None,
                "subcategory": None,
                "link": None,
                "target": 0,
                "sessions": [],
                "proxies": [],
                "running": False,
                "stop": threading.Event(),
                "success": 0,
                "fail": 0,
                "sent": 0,
                "user_id": None,
                "video_id": None,
                "username": None,
                "status_msg_id": None,
                "last_edit": 0.0,
            }
        return STATE[chat_id]


def get_video_info(link):
    video_id = None
    username = None
    user_id = None
    m = re.search(r'/video/(\d{15,})', link)
    if m:
        video_id = m.group(1)
    m = re.search(r'tiktok\.com/@([^/\?]+)', link)
    if m:
        username = m.group(1)
    if not video_id:
        try:
            resp = requests.get('https://api16-normal-c-alisg.ttapis.com/tiktok/linker/target/get/v1/', params={'url': link, 'aid': '1233', 'channel': 'googleplay'}, headers={'User-Agent': 'com.zhiliaoapp.musically/2023105030'}, timeout=8, verify=False)
            landing = resp.json().get('landing_url', '')
            m2 = re.search(r'/video/(\d{15,})', landing)
            if m2:
                video_id = m2.group(1)
            m3 = re.search(r'tiktok\.com/@([^/\?]+)', landing)
            if m3 and not username:
                username = m3.group(1)
        except Exception:
            pass
    if username:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'text/html,application/xhtml+xml'}
            html = requests.get(f'https://www.tiktok.com/@{username}', headers=headers, timeout=8, verify=False).text
            m_uid = re.search(r'"user_id":"(\d{15,})"', html)
            if m_uid:
                user_id = m_uid.group(1)
            else:
                m_sec = re.search(r'"secUid":"([^"]+)"', html)
                if m_sec:
                    user_id = m_sec.group(1)
        except Exception:
            pass
    if not user_id:
        user_id = str(random.randint(7000000000000000000, 7999999999999999999))
    if not username:
        username = "unknown"
    if not video_id:
        video_id = str(random.randint(7000000000000000000, 7999999999999999999))
    return video_id, user_id, username


def send_real_report(session, proxy, video_id, user_id, report_type):
    try:
        country = random.choice(COUNTRIES)
        device_type, brand = random.choice(DEVICES)
        secret = secrets.token_hex(16)
        cookies = {'sessionid': session, 'passport_csrf_token': secret, 'passport_csrf_token_default': secret}
        params = {
            'report_type': 'video', 'object_id': str(video_id), 'owner_id': str(user_id),
            'enter_from': 'homepage_hot', 'extra_log_params': json.dumps({"last_from_group_id": str(video_id), "is_ecom": "0"}),
            'aweme_type': '0', 'group_id': str(video_id), 'isFirst': '1', 'no_hw': '1',
            'report_desc': '', 'uri': '', 'reason': report_type['reason'], 'category': report_type['category'],
            'request_tag_from': 'h5', 'device_platform': 'android', 'os': 'android', 'ssmix': 'a',
            '_rticket': str(int(time.time() * 1000)), 'cdid': str(uuid.uuid4() if 'uuid' in globals() else __import__('uuid').uuid4()),
            'channel': 'googleplay', 'aid': '1233', 'app_name': 'musical_ly',
            'version_code': '370805', 'version_name': '37.8.5', 'manifest_version_code': '2023708050',
            'update_version_code': '2023708050', 'ab_version': '37.8.5', 'resolution': '1080*2220', 'dpi': '440',
            'device_type': device_type, 'device_brand': brand, 'language': 'ar', 'os_api': '30', 'os_version': '11',
            'ac': 'mobile', 'is_pad': '0', 'current_region': country, 'app_type': 'normal', 'sys_region': country,
            'mcc_mnc': '42103', 'timezone_name': 'Asia/Aden', 'residence': country, 'app_language': 'ar',
            'carrier_region': country, 'timezone_offset': '10800', 'host_abi': 'arm64-v8a', 'locale': 'ar',
            'ac2': 'lte', 'uoo': '1', 'op_region': country, 'build_number': '37.8.5', 'region': country,
            'ts': str(int(time.time())), 'iid': str(random.randint(1000000000000000000, 9999999999999999999)),
            'device_id': str(random.randint(1000000000000000000, 9999999999999999999)),
            'openudid': binascii.hexlify(os.urandom(8)).decode() if 'binascii' in globals() else __import__('binascii').hexlify(os.urandom(8)).decode(),
        }
        encoded = urllib.parse.urlencode(params)
        
        signed = XGorgon.sign(encoded, "", urllib.parse.urlencode(cookies))
        
        report_headers = {
            'User-Agent': f'com.zhiliaoapp.musically/2023708050 (Linux; U; Android 11; ar; {device_type}; Build/RP1A.200720.011)',
            'x-tt-referer': 'https://www.tiktok.com/falcon/communitysafety/page/reasons/index.html',
            'Accept': 'application/json, text/plain, */*', 'x-tt-passport-csrf-token': secret,
            'content-type': 'application/x-www-form-urlencoded',
            'x-gorgon': signed.get('x-gorgon', ''), 'x-khronos': signed.get('x-khronos', ''),
            'x-ss-req-ticket': signed.get('x-ss-req-ticket', ''),
        }

        proxies_dict = None
        if proxy:
            p = proxy if proxy.startswith('http') or proxy.startswith('socks') else f'http://{proxy}'
            proxies_dict = {'http': p, 'https': p}

        response = requests.get(f'https://api16-normal-c-alisg.ttapis.com/aweme/v2/aweme/feedback/?{encoded}', headers=report_headers, cookies=cookies, proxies=proxies_dict, verify=False, timeout=5)
        if '"status_code":0' in response.text or '"status_message":""' in response.text:
            return True
        return False
    except Exception:
        return False


def render_status(s):
    return (
        "📊 الحالة المباشرة (هجوم آمن مع دمج التوقيعين 🛡️)\n"
        f"{LINE}\n"
        f"⚡ ناجح: {s['success']}\n"
        f"⚕️ فاشل: {s['fail']}\n"
        f"🔥 مرسلة: {s['sent']} / {s['target']}\n"
        f"{LINE}\n"
        f"🚀 الهجوم قيد التنفيذ..."
    )


def render_final(s, note=""):
    rate = (s["success"] / s["sent"] * 100) if s["sent"] else 0
    return (
        "🏁 انتهت العملية بنجاح\n"
        f"{LINE}\n"
        f"⚡ ناجح: {s['success']}\n"
        f"⚕️ فاشل: {s['fail']}\n"
        f"🔥 مرسلة: {s['sent']} / {s['target']}\n"
        f"📊 المعدل: {rate:.1f}%\n"
        f"{LINE}\n{note}"
    )


def run_engine(chat_id, s):
    try:
        try:
            bot.send_message(chat_id, "🔎 جاري فحص واستخراج معلومات الفيديو والهدف...")
        except Exception:
            pass

        video_id, user_id, username = get_video_info(s["link"])
        s["video_id"] = video_id
        s["user_id"] = user_id
        s["username"] = username

        try:
            target_card = (
                "✅ تم استخراج معلومات الهدف بنجاح\n"
                f"{LINE}\n"
                f"👤 المستخدم: @{username}\n"
                f"🆔 Video ID: {video_id}\n"
                f"🎯 الهدف المطلوب: {s['target']} بلاغ\n"
                f"🔑 السيشنات المتاحة: {len(s['sessions'])}\n"
                f"{LINE}"
            )
            bot.send_message(chat_id, target_card)
            status_msg = bot.send_message(chat_id, "🚀 بدء الإرسال الآمن مع التهدئة لتجنب الحظر...")
            s["status_msg_id"] = status_msg.message_id
        except Exception:
            pass

        def refresh(force=False):
            now = time.time()
            if not force and (now - s["last_edit"]) < 1.5:
                return
            s["last_edit"] = now
            try:
                bot.edit_message_text(render_status(s), chat_id=chat_id, message_id=s["status_msg_id"])
            except Exception:
                pass

        report_type = subcategories[s["category"]][0]
        session_idx = 0
        proxy_idx = 0

        while s["sent"] < s["target"] and not s["stop"].is_set():
            sess = s["sessions"][session_idx % len(s["sessions"])]
            prx = s["proxies"][proxy_idx % len(s["proxies"])] if s["proxies"] else None
            
            session_idx += 1
            if s["proxies"]:
                proxy_idx += 1

            success = send_real_report(sess, prx, video_id, user_id, report_type)
            s["sent"] += 1
            if success:
                s["success"] += 1
            else:
                s["fail"] += 1

            refresh()
            time.sleep(random.uniform(1.5, 3.0))

        note = "🛑 تم الإيقاف يدوياً." if s["stop"].is_set() else "✨ إكتمال البلاغات بنجاح تام."
        try:
            bot.edit_message_text(render_final(s, note), chat_id=chat_id, message_id=s["status_msg_id"])
        except Exception:
            pass

    except Exception as e:
        try:
            bot.send_message(chat_id, f"💥 خطأ أثناء التنفيذ: {e}")
        except Exception:
            pass
    finally:
        s["running"] = False
        s["stop"].clear()


# ============= أوامر وبوت التليجرام =============
@bot.message_handler(commands=["start"])
def cmd_start(message):
    chat_id = message.chat.id
    s = st(chat_id)
    if s["running"]:
        bot.send_message(chat_id, "⚠️ هناك عملية قيد التشغيل حالياً. أرسل /stop لإيقافها.")
        return
    s["step"] = None
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, cat in enumerate(categories, 1):
        kb.add(types.InlineKeyboardButton(f"{i}. {cat}", callback_data=f"cat:{i}"))
    bot.send_message(chat_id, "🎯 اختر فئة البلاغ الأساسية:", reply_markup=kb)


@bot.message_handler(commands=["stop"])
def cmd_stop(message):
    chat_id = message.chat.id
    s = st(chat_id)
    if s["running"]:
        s["stop"].set()
        bot.send_message(chat_id, "🛑 تم إرسال أمر الإيقاف المؤقت للعملية...")
    else:
        bot.send_message(chat_id, "لا توجد عملية تعمل حالياً.")


@bot.message_handler(commands=["cancel"])
def cmd_cancel(message):
    chat_id = message.chat.id
    s = st(chat_id)
    if s["running"]:
        bot.send_message(chat_id, "⚠️ العملية تعمل، استخدم /stop أولاً.")
        return
    s.update({"step": None, "category": None, "subcategory": None, "link": None, "target": 0, "sessions": [], "proxies": []})
    bot.send_message(chat_id, "🗑️ تم تصفير الذاكرة وإعادة الضبط. أرسل /start للبدء من جديد.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
def cb_category(call):
    chat_id = call.message.chat.id
    s = st(chat_id)
    cat = int(call.data.split(":")[1])
    s["category"] = cat
    s["subcategory"] = 1
    s["step"] = "await_link"
    bot.edit_message_text(f"📂 الفئة المختارة: {categories[cat - 1]}\n\n🔗 أرسل الآن رابط الفيديو المستهدف:", chat_id=chat_id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("session_method:"))
def cb_session_method(call):
    chat_id = call.message.chat.id
    s = st(chat_id)
    method = call.data.split(":")[1]
    
    if method == "text":
        s["step"] = "await_sessions_text"
        bot.edit_message_text("✍️ أرسل السيشنات الآن نصياً (كل سيشن في سطر جديد):", chat_id=chat_id, message_id=call.message.message_id)
    else:
        s["step"] = "await_sessions_file"
        bot.edit_message_text("📄 أرسل ملف السيشنات بصيغة نصية (.txt):", chat_id=chat_id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("proxy_method:"))
def cb_proxy_method(call):
    chat_id = call.message.chat.id
    s = st(chat_id)
    method = call.data.split(":")[1]

    if method == "none":
        s["proxies"] = []
        s["step"] = None
        start_process(chat_id, s)
    elif method == "text":
        s["step"] = "await_proxies_text"
        bot.edit_message_text("✍️ أرسل البروكسيات نصياً (كل بروكسي في سطر):", chat_id=chat_id, message_id=call.message.message_id)
    else:
        s["step"] = "await_proxies_file"
        bot.edit_message_text("🌐 أرسل ملف البروكسيات (.txt):", chat_id=chat_id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)


def ask_proxy_step(chat_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🌐 رفع ملف بروكسيات (.txt)", callback_data="proxy_method:file"),
        types.InlineKeyboardButton("✍️ إدخال البروكسيات نصياً", callback_data="proxy_method:text"),
        types.InlineKeyboardButton("🚫 التشغيل بدون بروكسيات", callback_data="proxy_method:none")
    )
    bot.send_message(chat_id, "🌐 اختر طريقة إدخال البروكسيات لحماية الأيبيهات:", reply_markup=kb)


def start_process(chat_id, s):
    bot.send_message(chat_id, "🚀 بدء تشغيل محرك الهجوم الآمن والتكرار الآن...")
    s["running"] = True
    s["stop"].clear()
    s["success"] = 0
    s["fail"] = 0
    s["sent"] = 0
    t = threading.Thread(target=run_engine, args=(chat_id, s), daemon=True)
    t.start()


@bot.message_handler(content_types=["text"])
def handle_text(message):
    chat_id = message.chat.id
    s = st(chat_id)
    text = message.text.strip()

    if s["running"]:
        return

    if s["step"] == "await_link":
        s["link"] = text
        s["step"] = "await_count"
        bot.send_message(chat_id, "🔢 كم عدد البلاغات المطلوبة؟ (مثال: 500)")
        return

    if s["step"] == "await_count":
        try:
            n = int(text)
            if n <= 0: raise ValueError
        except ValueError:
            bot.send_message(chat_id, "❌ أرسل رقماً صحيحاً وموجباً.")
            return
        s["target"] = n
        
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("✍️ إدخال السيشنات نصياً", callback_data="session_method:text"),
            types.InlineKeyboardButton("📄 رفع ملف سيشنات (.txt)", callback_data="session_method:file")
        )
        bot.send_message(chat_id, "🔑 اختر طريقة إضافة السيشنات:", reply_markup=kb)
        return

    if s["step"] == "await_sessions_text":
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            bot.send_message(chat_id, "❌ لم يتم العثور على سيشنات صحيحة.")
            return
        s["sessions"] = lines
        bot.send_message(chat_id, f"✅ تم حفظ {len(lines)} سيشن بنجاح.")
        ask_proxy_step(chat_id)
        return

    if s["step"] == "await_proxies_text":
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        s["proxies"] = lines
        bot.send_message(chat_id, f"✅ تم حفظ {len(lines)} بروكسي بنجاح.")
        s["step"] = None
        start_process(chat_id, s)
        return

    bot.send_message(chat_id, "ℹ️ أرسل /start للبدء من جديد.")


@bot.message_handler(content_types=["document"])
def handle_doc(message):
    chat_id = message.chat.id
    s = st(chat_id)

    if s["running"]:
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode("utf-8", errors="ignore")
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

        if not lines:
            bot.send_message(chat_id, "❌ الملف فارغ.")
            return

        if s["step"] == "await_sessions_file":
            s["sessions"] = lines
            bot.send_message(chat_id, f"✅ تم تحميل {len(lines)} سيشن من الملف.")
            ask_proxy_step(chat_id)
            return

        if s["step"] == "await_proxies_file":
            s["proxies"] = lines
            s["step"] = None
            bot.send_message(chat_id, f"✅ تم تحميل {len(lines)} بروكسي من الملف.")
            start_process(chat_id, s)
            return
    except Exception as e:
        bot.send_message(chat_id, f"💥 خطأ أثناء قراءة الملف: {e}")


# =========================================================
# التشغيل المتزامن (بوت التليجرام + سيرفر الويب الخلفي)
# =========================================================
def run_telegram_bot():
    print("Telegram Bot with Dual Signatures and Anti-Ban Engine is running...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    # تشغيل بوت التليجرام في خيط (Thread) مستقل في الخلفية
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # تشغيل سيرفر الويب في العملية الرئيسية لمنع Render من إيقاف التطبيق
    web_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
