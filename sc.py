#!/usr/bin/env python3
"""
XENON FF HUNTING - RARE TO GODLIKE (ALVIN LOGIC)
URUTAN 5-9+ dengan logic Alvin:
- 5x5 = RARE
- 6x5 = RARE
- 6x6 = EPIC
- 7x5 = RARE
- 7x6 = EPIC
- 7x7 = LEGENDARY
- 8x5 = RARE
- 8x6 = EPIC
- 8x7 = LEGENDARY
- 8x8 = MYTHIC
- 9x = GODLIKE
"""

import warnings
warnings.filterwarnings('ignore')
import requests
import random
import string
import time
import os
import json
import codecs
import base64
import sys
import hashlib
import secrets
import re
import threading
import tempfile
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque, Counter
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
except ImportError:
    print("[!] Install pycryptodome: pip install pycryptodome")
    sys.exit(1)

# ==================== CONFIG ====================
API_BASE = "https://api.gameskinbo.com"
API_CHECK = f"{API_BASE}/api/check"
API_CHECK_TRIAL = f"{API_BASE}/api/check_trial"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CHATGPT_DIR = "/storage/emulated/0/Pictures/ChatGPT"
os.makedirs(CHATGPT_DIR, exist_ok=True)

USER_KEY_FILE = os.path.join(CHATGPT_DIR, ".anonfk_userkey")
DEVICE_FILE = os.path.join(CHATGPT_DIR, ".device_id")
OUTPUT_MODE_FILE = os.path.join(CHATGPT_DIR, ".output_mode")
CUSTOM_NAME_FILE = os.path.join(CHATGPT_DIR, ".custom_name")
CUSTOM_LETTERS_FILE = os.path.join(CHATGPT_DIR, ".custom_letters")

# ==================== OUTPUT FOLDER STRUCTURE ====================
OUTPUT_FOLDER = os.path.join(CURRENT_DIR, "XENON_FF")
HUNT_FOLDER = os.path.join(OUTPUT_FOLDER, "hunt_results")
RARE_FOLDER = os.path.join(HUNT_FOLDER, "rare")
EPIC_FOLDER = os.path.join(HUNT_FOLDER, "epic")
LEGENDARY_FOLDER = os.path.join(HUNT_FOLDER, "legendary")
MYTHIC_FOLDER = os.path.join(HUNT_FOLDER, "mythic")
GODLIKE_FOLDER = os.path.join(HUNT_FOLDER, "godlike")
ALL_FOLDER = os.path.join(OUTPUT_FOLDER, "allaccount")
LOGS_FOLDER = os.path.join(OUTPUT_FOLDER, "logs")

# Buat semua folder
for folder in [OUTPUT_FOLDER, HUNT_FOLDER, RARE_FOLDER, EPIC_FOLDER, 
               LEGENDARY_FOLDER, MYTHIC_FOLDER, GODLIKE_FOLDER, 
               ALL_FOLDER, LOGS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

REGION = "ID"
REGION_NAME = "GHOST"
REGION_LANG = {"ID": "id"}
REGION_POOL = ["TH", "ME", "BR", "VN", "PH", "SG", "MY", "MX"]
region_index = 0
REGION_LOCK = threading.Lock()

def get_next_region():
    global region_index
    with REGION_LOCK:
        region_index = (region_index + 1) % len(REGION_POOL)
        return REGION_POOL[region_index]

THREAD_COUNT = 900
REQUEST_DELAY = 0
FAIL_SLEEP = 0

WATERMARK = "XENON FF HUNTING"
VERSION = "v3.0.0-ALVIN-LOGIC"
DEV_NAME = "Xenon"

last_success_time = time.time()
stuck_warning_shown = False
file_lock = threading.RLock()
session_pool = deque()
session_lock = threading.Lock()
running = True

stats = {
    'total': 0, 'common': 0, 'uncommon': 0,
    'rare': 0, 'epic': 0, 'legendary': 0,
    'mythic': 0, 'godlike': 0,
    'start_time': time.time(),
    'best_same': 0,
    'best_account_id': '',
    'best_uid': '',
    'hunted_accounts': []
}
stats_lock = threading.Lock()
stuck_monitor_active = True

# ==================== UI STYLES ====================
class UI:
    HEADER = '\033[38;2;100;200;255m'
    SUCCESS = '\033[38;2;0;255;150m'
    WARNING = '\033[38;2;255;200;50m'
    ERROR = '\033[38;2;255;80;80m'
    INFO = '\033[38;2;180;180;255m'
    DIM = '\033[38;2;120;120;120m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    # Rarity Colors
    RARE = '\033[38;2;0;150;255m'
    EPIC = '\033[38;2;180;50;255m'
    LEGENDARY = '\033[38;2;255;180;0m'
    MYTHIC = '\033[38;2;255;50;50m'
    GODLIKE = '\033[38;2;0;255;255m'
    COMMON = '\033[38;2;150;150;150m'
    UNCOMMON = '\033[38;2;0;200;50m'
    
    # Backgrounds
    BG_RARE = '\033[48;2;0;150;255m'
    BG_EPIC = '\033[48;2;180;50;255m'
    BG_LEGENDARY = '\033[48;2;255;180;0m'
    BG_MYTHIC = '\033[48;2;255;50;50m'
    BG_GODLIKE = '\033[48;2;0;255;255m'
    BG_COMMON = '\033[48;2;80;80;80m'
    BG_UNCOMMON = '\033[48;2;0;200;50m'

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_status(text, status="info"):
    icons = {"info": "●", "success": "✓", "warning": "⚠", "error": "✗"}
    colors = {"info": UI.INFO, "success": UI.SUCCESS, "warning": UI.WARNING, "error": UI.ERROR}
    print(f"{colors.get(status, UI.INFO)}[{icons.get(status, '•')}] {text}{UI.RESET}")

def print_header():
    clear()
    print(f"{UI.HEADER}{UI.BOLD}")
    print(" ╔══════════════════════════════════════════════════════════╗")
    print(" ║  🎯 XENON FF HUNTING  v3.0                            ║")
    print(" ║  Auto Hunt Rare → Godlike (Alvin Logic)               ║")
    print(" ╚══════════════════════════════════════════════════════════╝")
    print(f"{UI.RESET}")

def draw_box(title="", width=60):
    print(f"{UI.HEADER}┌{'─' * (width-2)}┐{UI.RESET}")
    if title:
        padding = (width - len(title) - 2) // 2
        print(f"{UI.HEADER}│{' ' * padding}{UI.BOLD}{title}{UI.RESET}{UI.HEADER}{' ' * (width - len(title) - padding - 2)}│{UI.RESET}")
        print(f"{UI.HEADER}├{'─' * (width-2)}┤{UI.RESET}")

# ==================== PROXY ====================
def load_proxies_from_file():
    proxy_file = os.path.join(CURRENT_DIR, "proxy.txt")
    proxies = [None]
    if os.path.exists(proxy_file):
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if not line.startswith('http'):
                            line = f"http://{line}"
                        proxies.append(line)
            print_status(f"Loaded {len(proxies)-1} proxies", "success")
        except Exception as e:
            print_status(f"Error loading proxy.txt: {e}", "warning")
    else:
        print_status("No proxy.txt found - running direct", "warning")
    return proxies

PROXY_LIST = [None]
proxy_index = 0
PROXY_LOCK = threading.Lock()

def get_next_proxy():
    global proxy_index
    with PROXY_LOCK:
        if len(PROXY_LIST) <= 1:
            return None
        proxy = PROXY_LIST[proxy_index % len(PROXY_LIST)]
        proxy_index += 1
        return proxy

# ==================== RARITY SYSTEM - ALVIN LOGIC ====================
def get_rarity_info(most_digit, same_count):
    if same_count >= 9:
        return "GODLIKE", UI.GODLIKE, UI.BG_GODLIKE, "⭐"
    elif same_count >= 8:
        return "MYTHIC", UI.MYTHIC, UI.BG_MYTHIC, "🔥"
    elif same_count >= 7:
        return "LEGENDARY", UI.LEGENDARY, UI.BG_LEGENDARY, "💎"
    elif same_count >= 6:
        return "EPIC", UI.EPIC, UI.BG_EPIC, "⚡"
    elif same_count >= 5:
        return "RARE", UI.RARE, UI.BG_RARE, "✨"
    elif same_count >= 4:
        return "UNCOMMON", UI.UNCOMMON, UI.BG_UNCOMMON, "📗"
    else:
        return "COMMON", UI.COMMON, UI.BG_COMMON, "📄"

# ==================== CHARS & DEVICE ====================
VIETNAMESE_LETTERS = [
    'a','à','á','ả','ã','ạ','ă','ằ','ắ','ẳ','ẵ','ặ','â','ầ','ấ','ẩ','ẫ','ậ',
    'b','c','d','đ','e','è','é','ẻ','ẽ','ẹ','ê','ề','ế','ể','ễ','ệ',
    'g','h','i','ì','í','ỉ','ĩ','ị','k','l','m','n',
    'o','ò','ó','ỏ','õ','ọ','ô','ồ','ố','ổ','ỗ','ộ','ơ','ờ','ớ','ở','ỡ','ợ',
    'p','q','r','s','t','u','ù','ú','ủ','ũ','ụ','ư','ừ','ứ','ử','ữ','ự',
    'v','x','y','ỳ','ý','ỷ','ỹ','ỵ',
    'A','À','Á','Ả','Ã','Ạ','Ă','Ằ','Ắ','Ẳ','Ẵ','Ặ','Â','Ầ','Ấ','Ẩ','Ẫ','Ậ',
    'B','C','D','Đ','E','È','É','Ẻ','Ẽ','Ẹ','Ê','Ề','Ế','Ể','Ễ','Ệ',
    'G','H','I','Ì','Í','Ỉ','Ĩ','Ị','K','L','M','N',
    'O','Ò','Ó','Ỏ','Õ','Ọ','Ô','Ồ','Ố','Ổ','Ỗ','Ộ','Ơ','Ờ','Ớ','Ở','Ỡ','Ợ',
    'P','Q','R','S','T','U','Ù','Ú','Ủ','Ũ','Ụ','Ư','Ừ','Ứ','Ử','Ữ','Ự',
    'V','X','Y','Ỳ','Ý','Ỷ','Ỹ','Ỵ'
]

KHMER_LETTERS = [
    'ក','ខ','គ','ឃ','ង','ច','ឆ','ជ','ឈ','ញ','ដ','ឋ','ឌ','ឍ','ណ','ត',
    'ថ','ទ','ធ','ន','ប','ផ','ព','ភ','ម','យ','រ','ល','វ','ឝ','ឞ','ស',
    'ហ','ឡ','អ','ឣ','ឤ','ឥ','ឦ','ឧ','ឨ','ឩ','ឪ','ឫ','ឬ','ឭ','ឮ','ឯ',
    'ឰ','ឱ','ឲ','ឳ','កា','ខា','គា','ឃា','ងា','ចា','ឆា','ជា','ឈា','ញា',
    'ដា','ឋា','ឌា','ឍា','ណា','តា','ថា','ទា','ធា','នា','បា','ផា','ពា',
    'ភា','មា','យា','រា','លា','វា','សា','ហា','ឡា','អា'
]

THAI_LETTERS = [
    'ก','ข','ฃ','ค','ฅ','ฆ','ง','จ','ฉ','ช','ซ','ฌ','ญ','ฎ','ฏ','ฐ','ฑ','ฒ',
    'ณ','ด','ต','ถ','ท','ธ','น','บ','ป','ผ','ฝ','พ','ฟ','ภ','ม','ย','ร','ฤ',
    'ล','ว','ศ','ษ','ส','ห','ฬ','อ','ฮ',
    'ะ','ั','า','ำ','ิ','ี','ึ','ื','ุ','ู','เ','แ','โ','ใ','ไ','ๅ','ๆ','็',
    '่','้','๊','๋','์','ํ','ฺ','฿','ฯ','๏','๚','๛'
]

JAPANESE_LETTERS = [
    'あ','い','う','え','お','か','き','く','け','こ','さ','し','す','せ','そ',
    'た','ち','つ','て','と','な','に','ぬ','ね','の','は','ひ','ふ','へ','ほ',
    'ま','み','む','め','も','や','ゆ','よ','ら','り','る','れ','ろ','わ','を','ん',
    'ぁ','ぃ','ぅ','ぇ','ぉ','っ','ゃ','ゅ','ょ',
    'ア','イ','ウ','エ','オ','カ','キ','ク','ケ','コ','サ','シ','ス','セ','ソ',
    'タ','チ','ツ','テ','ト','ナ','ニ','ヌ','ネ','ノ','ハ','ヒ','フ','ヘ','ホ',
    'マ','ミ','ム','メ','モ','ヤ','ユ','ヨ','ラ','リ','ル','レ','ロ','ワ','ヲ','ン',
    'ァ','ィ','ゥ','ェ','ォ','ッ','ャ','ュ','ョ'
]

MANDARIN_LETTERS = [
    '的','一','是','了','我','不','人','在','他','有','这','个','上','们','来',
    '到','时','大','地','为','子','中','你','说','生','国','年','着','就','那',
    '和','要','她','出','也','得','里','后','自','以','会','家','可','下','而',
    '过','天','去','能','对','小','多','然','于','心','学','么','之','都','好',
    '看','起','发','当','没','成','只','如','事','把','还','用','第','样','道',
    '想','作','种','开','手','爱','情','王','龙','虎','凤','皇','帝','君','子',
    '文','武','神','仙','魔','鬼','妖','灵','圣','贤','义','勇','忠','诚','信'
]

CHARS = VIETNAMESE_LETTERS + KHMER_LETTERS + THAI_LETTERS + JAPANESE_LETTERS + MANDARIN_LETTERS

DEVICE_POOL = []
samsung = [f"SM-{c}{random.randint(100,999)}" for _ in range(2000) for c in "AGNFMSJE"]
xiaomi = [f"{p} {random.randint(7,14)}" for _ in range(1500) for p in ["Redmi Note", "Redmi", "Poco F", "Poco X", "Mi", "Xiaomi", "Redmi K", "Poco M"]]
oppo = [f"OPPO {m}{random.randint(2,9999)}" for _ in range(1200) for m in ["CPH", "Find X", "Reno", "A", "F", "R", "K"]]
vivo = [f"vivo {m}{random.randint(1,9999)}" for _ in range(1200) for m in ["V", "X", "Y", "T", "S", "U", "Z"]]
realme = [f"Realme {m}{random.randint(7,70)}" for _ in range(1000) for m in ["", " Pro", " GT ", " C", " Narzo ", " X", " U"]]
oneplus = [f"OnePlus {random.randint(8,14)}" for _ in range(800)]
moto = [f"Moto {m}{random.randint(10,100)}" for _ in range(800) for m in ["G", "E", "Edge ", "Z", "X"]]
google = [f"Pixel {random.randint(3,8)}" for _ in range(500)]
sony = [f"Xperia {random.randint(1,5)} {chr(65+random.randint(0,2))}" for _ in range(400)]
nokia = [f"Nokia {random.randint(1,9)}.{random.randint(1,3)}" for _ in range(300)]
lg = [f"LG {chr(65+random.randint(0,15))}{random.randint(10,99)}" for _ in range(300)]
honor = [f"Honor {random.randint(10,70)}" for _ in range(300)]
asus = [f"ASUS Zenfone {random.randint(5,10)}" for _ in range(300)]
other = ["ASUS_I005DA","ASUS ROG Phone 5","Nothing Phone 1","Nothing Phone 2","SHARP AQUOS R8","Motorola Edge","Nubia RedMagic","Black Shark","Realme GT","Poco F4","iQOO 9","Oppo Find N","Vivo X Fold"] * 200

all_models = samsung + xiaomi + oppo + vivo + realme + oneplus + moto + google + sony + nokia + lg + honor + asus + other
brands = ["samsung","xiaomi","oppo","vivo","realme","oneplus","motorola","asus","google","sony","nokia","lg","honor","poco","iqoo","nubia","blackshark","nothing"]
android_versions = ["9","10","11","12","13","14","15","16"]

for _ in range(50000):
    DEVICE_POOL.append({
        "model": random.choice(all_models),
        "brand": random.choice(brands),
        "android": random.choice(android_versions)
    })

HEX_KEY = bytes.fromhex("32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533")

# ==================== ENCRYPTION ====================
def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def get_headers():
    device = random.choice(DEVICE_POOL)
    return {
        "User-Agent": f"GarenaMSDK/4.0.39({device['model']};Android {device['android']};en;ID;)",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": f"v1 {random.randint(100000, 999999)}",
        "X-Forwarded-For": get_random_ip(),
        "X-Real-IP": get_random_ip(),
    }

def get_headers_form():
    h = get_headers()
    h["Content-Type"] = "application/x-www-form-urlencoded"
    return h

def encode_varint(n):
    if n < 0:
        return b''
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            byte |= 0x80
        result.append(byte)
        if not n:
            break
    return bytes(result)

def create_proto_field(field_num, value):
    if isinstance(value, dict):
        nested = b''
        for k, v in value.items():
            nested += create_proto_field(k, v)
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(nested)) + nested
    elif isinstance(value, int):
        header = (field_num << 3) | 0
        return encode_varint(header) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        encoded_val = value.encode() if isinstance(value, str) else value
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(encoded_val)) + encoded_val
    return b''

def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())

def aes_encrypt(hex_data):
    data = bytes.fromhex(hex_data)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, AES.block_size))

def encrypt_api(plain_hex):
    plain = bytes.fromhex(plain_hex)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(plain, AES.block_size)).hex()

# ==================== LOGIN ====================
def major_login(uid, password, access_token, open_id, region):
    try:
        lang = REGION_LANG.get(region, "en")
        payload_parts = [
            b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
            lang.encode("ascii"),
            b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118692\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
        ]
        payload = b''.join(payload_parts)
        if region in ["ME", "TH"]:
            url = "https://loginbp.common.ggbluefox.com/MajorLogin"
        else:
            url = "https://loginbp.ggblueshark.com/MajorLogin"
        headers = {
            "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
            "Host": "loginbp.ggblueshark.com" if region not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
            "ReleaseVersion": "OB54", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
            "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1"
        }
        data = payload.replace(b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', access_token.encode())
        data = data.replace(b'1d8ec0240ede109973f3321b9354b44d', open_id.encode())
        d = encrypt_api(data.hex())
        session = requests.Session()
        session.verify = False
        response = session.post(url, headers=headers, data=bytes.fromhex(d), timeout=5)
        if response.status_code == 200 and len(response.text) > 10:
            jwt_start = response.text.find("eyJ")
            if jwt_start != -1:
                jwt_token = response.text[jwt_start:]
                second_dot = jwt_token.find(".", jwt_token.find(".") + 1)
                if second_dot != -1:
                    jwt_token = jwt_token[:second_dot + 44]
                try:
                    parts = jwt_token.split('.')
                    if len(parts) >= 2:
                        payload_part = parts[1]
                        padding = 4 - len(payload_part) % 4
                        if padding != 4:
                            payload_part += '=' * padding
                        decoded = base64.urlsafe_b64decode(payload_part)
                        data = json.loads(decoded)
                        account_id = data.get('account_id') or data.get('external_id')
                        if account_id:
                            return {"account_id": str(account_id), "jwt_token": jwt_token}
                except:
                    pass
        return {"account_id": "N/A", "jwt_token": ""}
    except:
        return {"account_id": "N/A", "jwt_token": ""}

# ==================== SESSION ====================
def get_session():
    with session_lock:
        if session_pool:
            return session_pool.popleft()
    s = requests.Session()
    s.verify = False
    proxy = get_next_proxy()
    if proxy:
        s.proxies = {'http': proxy, 'https': proxy}
    return s

def return_session(s):
    with session_lock:
        if len(session_pool) < THREAD_COUNT * 2:
            session_pool.append(s)
        else:
            s.close()

for _ in range(min(10, THREAD_COUNT)):
    s = requests.Session()
    s.verify = False
    session_pool.append(s)

# ==================== FILE OPERATIONS ====================
def read_file_safe(filepath):
    with file_lock:
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
        except:
            pass
    return ""

def write_file_atomic(filepath, content):
    with file_lock:
        try:
            temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath) or '.', text=True)
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                shutil.move(temp_path, filepath)
            except:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise
        except:
            pass

def append_file_atomic(filepath, content):
    with file_lock:
        try:
            existing = read_file_safe(filepath)
            write_file_atomic(filepath, existing + content)
        except:
            pass

def load_custom_letters():
    content = read_file_safe(CUSTOM_LETTERS_FILE).strip()
    if content and len(content) == 2 and content.isalpha():
        return content.upper()
    return "AB"

def save_custom_letters(letters):
    write_file_atomic(CUSTOM_LETTERS_FILE, letters.upper())

# ==================== COUNT SAME DIGITS ====================
def count_same_digits(account_id):
    aid = str(account_id)
    if not aid.isdigit() or len(aid) < 5:
        return 0, None
    analyzed = aid[1:]
    digit_counts = Counter(analyzed)
    max_count = max(digit_counts.values()) if digit_counts else 0
    most_digit = max(digit_counts, key=digit_counts.get) if digit_counts else None
    return max_count, most_digit

# ==================== SAVE HUNTED ACCOUNT ====================
def save_hunted_account(account_data):
    try:
        same_count = account_data.get('same_digit_count', 0)
        most_digit = account_data.get('most_digit', '')
        uid = account_data.get('uid', 'N/A')
        aid = account_data.get('account_id', 'N/A')
        password = account_data.get('password', 'N/A')
        name = account_data.get('name', 'N/A')
        jwt_token = account_data.get('jwt_token', '')
        rarity_label, _, _, emoji = get_rarity_info(most_digit, same_count)

        # Tentukan folder berdasarkan rarity
        rarity_folders = {
            'GODLIKE': GODLIKE_FOLDER,
            'MYTHIC': MYTHIC_FOLDER,
            'LEGENDARY': LEGENDARY_FOLDER,
            'EPIC': EPIC_FOLDER,
            'RARE': RARE_FOLDER
        }
        target_folder = rarity_folders.get(rarity_label, HUNT_FOLDER)
        os.makedirs(target_folder, exist_ok=True)

        # File paths
        json_file = os.path.join(target_folder, f"{rarity_label.lower()}.json")
        txt_file = os.path.join(target_folder, f"{rarity_label.lower()}.txt")
        
        # Master files
        master_json = os.path.join(HUNT_FOLDER, "all_hunts.json")
        master_txt = os.path.join(HUNT_FOLDER, "all_hunts.txt")

        account_entry = {
            "uid": uid,
            "account_id": aid,
            "password": password,
            "name": name,
            "same_digit_count": same_count,
            "most_digit": most_digit,
            "rarity": rarity_label,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "jwt_token": jwt_token,
            "region": REGION_NAME,
            "watermark": WATERMARK
        }

        with file_lock:
            # Save to rarity folder
            all_accounts = []
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        all_accounts = json.load(f)
                except:
                    all_accounts = []
            all_accounts.append(account_entry)
            write_file_atomic(json_file, json.dumps(all_accounts, indent=2, ensure_ascii=False))

            # Save to txt
            digit_info = f"{most_digit}x{same_count}" if most_digit else f"{same_count}x"
            txt_entry = f"{uid} | {aid} | {password} | {digit_info} | [{rarity_label}] {emoji}\n"
            append_file_atomic(txt_file, txt_entry)

            # Save to master
            master_accounts = []
            if os.path.exists(master_json):
                try:
                    with open(master_json, 'r', encoding='utf-8') as f:
                        master_accounts = json.load(f)
                except:
                    master_accounts = []
            master_accounts.append(account_entry)
            write_file_atomic(master_json, json.dumps(master_accounts, indent=2, ensure_ascii=False))
            append_file_atomic(master_txt, txt_entry)

            # Save to allaccount
            all_json = os.path.join(ALL_FOLDER, "account.json")
            all_txt = os.path.join(ALL_FOLDER, "id.txt")
            all_accounts_all = []
            if os.path.exists(all_json):
                try:
                    with open(all_json, 'r', encoding='utf-8') as f:
                        all_accounts_all = json.load(f)
                except:
                    all_accounts_all = []
            all_accounts_all.append(account_entry)
            write_file_atomic(all_json, json.dumps(all_accounts_all, indent=2, ensure_ascii=False))
            
            all_ids = [acc.get('account_id', 'N/A') for acc in all_accounts_all]
            write_file_atomic(all_txt, '\n'.join(all_ids))

            # Update cariid.txt
            cariid_file = os.path.join(HUNT_FOLDER, "cariid.txt")
            existing = read_file_safe(cariid_file)
            if not existing:
                existing = "[9] [8] [7] [6] [5] (URUTAN SAME DIGIT TERBANYAK)\n\n"
            
            lines = existing.strip().split('\n')
            header = lines[0] if lines and lines[0].startswith('[') else "[9] [8] [7] [6] [5] (URUTAN SAME DIGIT TERBANYAK)\n\n"
            entries = [l for l in lines[2:] if l.strip()] if len(lines) > 2 else []
            
            new_entry = f"[{same_count}] {uid} | {aid} | {password} | {digit_info} | [{rarity_label}] {emoji}"
            entries.append(new_entry)
            
            def sort_key(line):
                for digit in range(9, 0, -1):
                    if f"[{digit}]" in line:
                        return -digit
                return 0
            entries.sort(key=sort_key)
            final_content = header + '\n'.join(entries) + '\n'
            write_file_atomic(cariid_file, final_content)

        return True
    except Exception as e:
        return False

# ==================== GENERATE ====================
def generate_cool_name():
    letters = load_custom_letters()
    first_char = letters[0]
    second_char = letters[1]
    length = random.randint(8, 12)
    f_pos = random.randint(0, length - 1)
    k_pos = random.randint(0, length - 1)
    while k_pos == f_pos:
        k_pos = random.randint(0, length - 1)
    name = []
    for i in range(length):
        if i == f_pos:
            name.append(first_char)
        elif i == k_pos:
            name.append(second_char)
        else:
            name.append(random.choice(CHARS))
    return ''.join(name)

def generate_password():
    digits = ''.join(random.choices(string.digits, k=random.randint(4, 6)))
    letters = ''.join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
    return f"XENONFK{digits}{letters}"

def generate_account():
    global last_success_time
    if not running:
        return None
    session = get_session()
    try:
        for retry in range(2):
            try:
                password = generate_password()
                name = generate_cool_name()
                resp = session.post(
                    "https://100067.connect.garena.com/api/v2/oauth/guest:register",
                    headers=get_headers(),
                    json={"app_id": 100067, "client_type": 2, "password": password, "source": 2},
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "data" in data and "uid" in data["data"]:
                        uid = data["data"]["uid"]
                        resp2 = session.post(
                            "https://100067.connect.garena.com/oauth/guest/token/grant",
                            headers=get_headers_form(),
                            data={"uid": uid, "password": password, "response_type": "token", "client_type": "2", "client_secret": HEX_KEY, "client_id": "100067"},
                            timeout=5
                        )
                        if resp2.status_code == 200:
                            token_data = resp2.json()
                            open_id = token_data.get('open_id', '')
                            access_token = token_data.get('access_token', '')
                            if open_id and access_token:
                                keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
                                encoded = ""
                                for i in range(len(open_id)):
                                    encoded += chr(ord(open_id[i]) ^ keystream[i % len(keystream)])
                                hex_str = ''.join(c if 32 <= ord(c) <= 126 else '\\u{:04x}'.format(ord(c)) for c in encoded)
                                field = codecs.decode(hex_str, 'unicode_escape').encode('latin1')
                                if REGION in ["ME", "TH"]:
                                    url_major = "https://loginbp.common.ggbluefox.com/MajorRegister"
                                else:
                                    url_major = "https://loginbp.ggblueshark.com/MajorRegister"
                                lang_code = REGION_LANG.get(REGION, "en")
                                payload = {1: name, 2: access_token, 3: open_id, 5: 102000007, 6: 4, 7: 1, 13: 1, 14: field, 15: lang_code, 16: 1, 17: 1}
                                payload_bytes = build_proto(payload)
                                encrypted_payload = aes_encrypt(payload_bytes.hex())
                                headers_major = {
                                    "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
                                    "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
                                    "Host": "loginbp.ggblueshark.com" if REGION not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
                                    "ReleaseVersion": "OB54", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
                                    "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1"
                                }
                                session.post(url_major, headers=headers_major, data=encrypted_payload, timeout=5)
                                login_result = major_login(uid, password, access_token, open_id, REGION)
                                account_id = login_result.get("account_id", "N/A")
                                jwt_token = login_result.get("jwt_token", "")
                                if account_id != "N/A":
                                    return_session(session)
                                    last_success_time = time.time()
                                    return {
                                        "uid": uid,
                                        "password": password,
                                        "name": name,
                                        "account_id": account_id,
                                        "jwt_token": jwt_token,
                                        "success": True
                                    }
            except:
                pass
    except:
        pass
    return_session(session)
    return None

# ==================== WORKER ====================
def show_rare_find(account_data, same_count, most_digit, total_generated, hunt_time):
    uid = account_data.get('uid', 'N/A')
    aid = account_data.get('account_id', 'N/A')
    password = account_data.get('password', 'N/A')
    rarity_label, color, bg, emoji = get_rarity_info(most_digit, same_count)

    print()
    print(f"{bg}{UI.BOLD}┌{'─' * 66}┐{UI.RESET}")
    print(f"{bg}{UI.BOLD}│  {emoji} {rarity_label} FOUND!{' ' * (56 - len(rarity_label))}│{UI.RESET}")
    print(f"{bg}{UI.BOLD}├{'─' * 66}┤{UI.RESET}")
    print(f"{bg}{UI.BOLD}│  Rarity : {rarity_label:<10} ({same_count}x {most_digit}){' ' * (33 - len(str(same_count))) }│{UI.RESET}")
    print(f"{bg}{UI.BOLD}│  UID    : {uid:<36} │{UI.RESET}")
    print(f"{bg}{UI.BOLD}│  ACC ID : {aid:<36} │{UI.RESET}")
    print(f"{bg}{UI.BOLD}│  PASS   : {password:<36} │{UI.RESET}")
    print(f"{bg}{UI.BOLD}│  Stats  : {total_generated} gen | {hunt_time:.1f}s{' ' * (25 - len(str(total_generated)) - len(f'{hunt_time:.1f}'))}│{UI.RESET}")
    print(f"{bg}{UI.BOLD}└{'─' * 66}┘{UI.RESET}")
    print()

def worker_hunt():
    global running, last_success_time
    while running:
        account = generate_account()
        if account and account.get("success"):
            uid = account["uid"]
            aid = account["account_id"]
            if aid == "N/A":
                aid = str(uid)
            password = account["password"]
            name = account["name"]
            jwt_token = account.get("jwt_token", "")

            same_count, most_digit = count_same_digits(aid)

            with stats_lock:
                stats['total'] += 1
                current_total = stats['total']
                rarity_label, _, _, _ = get_rarity_info(most_digit, same_count)
                
                if rarity_label == "GODLIKE":
                    stats['godlike'] += 1
                elif rarity_label == "MYTHIC":
                    stats['mythic'] += 1
                elif rarity_label == "LEGENDARY":
                    stats['legendary'] += 1
                elif rarity_label == "EPIC":
                    stats['epic'] += 1
                elif rarity_label == "RARE":
                    stats['rare'] += 1
                elif rarity_label == "UNCOMMON":
                    stats['uncommon'] += 1
                else:
                    stats['common'] += 1

                if same_count > stats['best_same']:
                    stats['best_same'] = same_count
                    stats['best_account_id'] = aid
                    stats['best_uid'] = uid

                hunt_time = time.time() - stats['start_time']

            # ONLY SAVE 5x+ (RARE TO GODLIKE)
            if same_count >= 5:
                account_info = {
                    'uid': uid,
                    'password': password,
                    'account_id': aid,
                    'name': name,
                    'region': REGION_NAME,
                    'same_digit_count': same_count,
                    'most_digit': most_digit,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'watermark': WATERMARK,
                    'jwt_token': jwt_token
                }

                save_hunted_account(account_info)

                with stats_lock:
                    stats['hunted_accounts'].append(account_info)

                show_rare_find(account_info, same_count, most_digit, current_total, hunt_time)

            last_success_time = time.time()
        else:
            time.sleep(FAIL_SLEEP)
        time.sleep(REQUEST_DELAY)

def show_live_stats():
    while running:
        time.sleep(5)
        if not running:
            break
        with stats_lock:
            total = stats['total']
            best = stats['best_same']
            best_aid = stats['best_account_id']
            hunt_time = time.time() - stats['start_time']
            speed = total / hunt_time if hunt_time > 0 else 0
            hunted_count = len(stats['hunted_accounts'])

        print(f"{UI.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{UI.RESET}")
        print(f"{UI.INFO}⚡ Total: {total} | Speed: {speed:.1f}/s | Found: {hunted_count} | Best: {best}x | ID: {best_aid}{UI.RESET}")
        print(f"{UI.RARE}RARE: {stats['rare']}{UI.RESET} | {UI.EPIC}EPIC: {stats['epic']}{UI.RESET} | {UI.LEGENDARY}LEGENDARY: {stats['legendary']}{UI.RESET} | {UI.MYTHIC}MYTHIC: {stats['mythic']}{UI.RESET} | {UI.GODLIKE}GODLIKE: {stats['godlike']}{UI.RESET}")
        print(f"{UI.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{UI.RESET}")
        print()

def stuck_monitor():
    global last_success_time, stuck_monitor_active
    while stuck_monitor_active:
        time.sleep(10)
        if not running:
            break
        elapsed = time.time() - last_success_time
        if elapsed > 10 and stats['total'] > 0:
            print()
            print_status("Rate limit detected - slow generation", "warning")
            print_status("Try enabling Airplane Mode or change IP", "info")
            print()

# ==================== MAIN ====================
def run_hunt():
    global running, THREAD_COUNT

    print_header()
    print()
    print(f"{UI.INFO}┌{'─' * 60}┐{UI.RESET}")
    print(f"{UI.INFO}│  {UI.BOLD}HUNT CONFIGURATION{UI.RESET}{UI.INFO}                              │{UI.RESET}")
    print(f"{UI.INFO}│  Mode   : INFINITE (never stops){UI.RESET}{UI.INFO}                     │{UI.RESET}")
    print(f"{UI.INFO}│  Region : GHOST (ID){UI.RESET}{UI.INFO}                                    │{UI.RESET}")
    print(f"{UI.INFO}│  Threads: {THREAD_COUNT}{UI.RESET}{UI.INFO}{' ' * (49 - len(str(THREAD_COUNT)))}│{UI.RESET}")
    print(f"{UI.INFO}│  Logic  : ALVIN (5x=RARE, 6x=EPIC, 7x=LEGENDARY){UI.RESET}{UI.INFO}   │{UI.RESET}")
    print(f"{UI.INFO}│  Save   : XENON_FF/hunt_results/ [rarity folders]{UI.RESET}{UI.INFO}  │{UI.RESET}")
    print(f"{UI.INFO}└{'─' * 60}┘{UI.RESET}")
    print()
    print(f"{UI.DIM}Press CTRL+C to stop and save results{UI.RESET}")
    print()

    stats['total'] = 0
    stats['common'] = 0
    stats['uncommon'] = 0
    stats['rare'] = 0
    stats['epic'] = 0
    stats['legendary'] = 0
    stats['mythic'] = 0
    stats['godlike'] = 0
    stats['start_time'] = time.time()
    stats['best_same'] = 0
    stats['best_account_id'] = ''
    stats['best_uid'] = ''
    stats['hunted_accounts'] = []

    running = True

    monitor_thread = threading.Thread(target=stuck_monitor, daemon=True)
    monitor_thread.start()

    stats_thread = threading.Thread(target=show_live_stats, daemon=True)
    stats_thread.start()

    try:
        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            futures = [executor.submit(worker_hunt) for _ in range(THREAD_COUNT)]
            for future in as_completed(futures):
                if not running:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                future.result()
    except KeyboardInterrupt:
        print()
        print_status("Stopping hunt...", "warning")
        running = False
        time.sleep(1)
    except Exception as e:
        print()
        print_status(f"Error: {e}", "error")

    time.sleep(1)
    elapsed = time.time() - stats['start_time']
    hunted_count = len(stats['hunted_accounts'])

    print()
    print(f"{UI.HEADER}{'─' * 60}{UI.RESET}")
    print(f"{UI.SUCCESS}{UI.BOLD}🎯 HUNT COMPLETE!{UI.RESET}")
    print()
    print(f"{UI.INFO}Total Generated : {UI.BOLD}{stats['total']}{UI.RESET}")
    print(f"{UI.SUCCESS}Rare+ Found     : {UI.BOLD}{hunted_count}{UI.RESET}")
    print()
    print(f"{UI.INFO}Rarity Breakdown:{UI.RESET}")
    print(f"  {UI.COMMON}COMMON     : {stats['common']}{UI.RESET}")
    print(f"  {UI.UNCOMMON}UNCOMMON   : {stats['uncommon']}{UI.RESET}")
    print(f"  {UI.RARE}RARE       : {stats['rare']}{UI.RESET}")
    print(f"  {UI.EPIC}EPIC       : {stats['epic']}{UI.RESET}")
    print(f"  {UI.LEGENDARY}LEGENDARY  : {stats['legendary']}{UI.RESET}")
    print(f"  {UI.MYTHIC}MYTHIC     : {stats['mythic']}{UI.RESET}")
    print(f"  {UI.GODLIKE}GODLIKE    : {stats['godlike']}{UI.RESET}")
    print()
    if stats['best_same'] > 0:
        print(f"{UI.SUCCESS}🏆 Best Find : {stats['best_same']}x same digit{UI.RESET}")
        print(f"   UID : {stats['best_uid']}")
        print(f"   ID  : {stats['best_account_id']}")
    print()
    print(f"{UI.INFO}Time  : {elapsed:.1f}s{UI.RESET}")
    if elapsed > 0:
        print(f"{UI.INFO}Speed : {stats['total']/elapsed:.2f} acc/s{UI.RESET}")
    print()
    print(f"{UI.SUCCESS}📁 Saved to:{UI.RESET}")
    print(f"   {UI.DIM}XENON_FF/hunt_results/{UI.RESET}")
    print(f"   {UI.DIM}├── rare/     → {UI.RARE}RARE{UI.RESET}")
    print(f"   {UI.DIM}├── epic/     → {UI.EPIC}EPIC{UI.RESET}")
    print(f"   {UI.DIM}├── legendary/ → {UI.LEGENDARY}LEGENDARY{UI.RESET}")
    print(f"   {UI.DIM}├── mythic/    → {UI.MYTHIC}MYTHIC{UI.RESET}")
    print(f"   {UI.DIM}└── godlike/   → {UI.GODLIKE}GODLIKE{UI.RESET}")
    print()

def main():
    global running, THREAD_COUNT, PROXY_LIST

    PROXY_LIST = load_proxies_from_file()
    
    clear()
    print(f"{UI.HEADER}{UI.BOLD}")
    print(" ╔══════════════════════════════════════════════════════════╗")
    print(" ║  🎯 XENON FF HUNTING  v3.0                            ║")
    print(" ║  Auto Hunt Rare → Godlike (Alvin Logic)               ║")
    print(" ║  5x=RARE | 6x=EPIC | 7x=LEGENDARY                    ║")
    print(" ║  8x=MYTHIC | 9x=GODLIKE                              ║")
    print(" ╚══════════════════════════════════════════════════════════╝")
    print(f"{UI.RESET}")
    print()
    
    if len(PROXY_LIST) > 1:
        print_status(f"Proxies loaded: {len(PROXY_LIST)-1}", "success")
    else:
        print_status("No proxy.txt - running direct", "warning")
    print()
    
    print_status(f"Starting with {THREAD_COUNT} threads...", "info")
    print_status("Mode: INFINITE - only saves 5x-9x (ALVIN LOGIC)", "info")
    print()

    time.sleep(1)
    run_hunt()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_status("Exiting...", "warning")
        sys.exit(0)
