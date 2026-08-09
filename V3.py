#!/usr/bin/env python3
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

API_BASE = "https://api.gameskinbo.com"
API_CHECK = f"{API_BASE}/api/check"
API_CHECK_TRIAL = f"{API_BASE}/api/check_trial"
API_STATUS = f"{API_BASE}/api/status"
API_VERSION = f"{API_BASE}/version.json"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if not CURRENT_DIR or CURRENT_DIR == os.getcwd():
    CURRENT_DIR = os.getcwd()
CHATGPT_DIR = os.path.join(CURRENT_DIR, ".xenon_config")
os.makedirs(CHATGPT_DIR, exist_ok=True)

USER_KEY_FILE = os.path.join(CHATGPT_DIR, ".xenon_userkey")
DEVICE_FILE = os.path.join(CHATGPT_DIR, ".device_id")
TRIAL_KEY_FILE = os.path.join(CHATGPT_DIR, ".trial_key")
LICENSE_INFO_FILE = os.path.join(CHATGPT_DIR, ".license_info")
OUTPUT_MODE_FILE = os.path.join(CHATGPT_DIR, ".output_mode")
CUSTOM_NAME_FILE = os.path.join(CHATGPT_DIR, ".custom_name")
RARE_ONLY_FILE = os.path.join(CHATGPT_DIR, ".rare_only")
PASSWORD_FORMAT_FILE = os.path.join(CHATGPT_DIR, ".password_format")
THREAD_COUNT_FILE = os.path.join(CHATGPT_DIR, ".thread_count")
NAME_FORMAT_FILE = os.path.join(CHATGPT_DIR, ".name_format")
MAX_GENERATE_FILE = os.path.join(CHATGPT_DIR, ".max_generate")

OUTPUT_FOLDER = os.path.join(CURRENT_DIR, "XENON_FF")
SPECIAL_FOLDER = os.path.join(OUTPUT_FOLDER, "special")
ALL_FOLDER = os.path.join(OUTPUT_FOLDER, "allaccount")
os.makedirs(SPECIAL_FOLDER, exist_ok=True)
os.makedirs(ALL_FOLDER, exist_ok=True)

REGION = "ID"
REGION_NAME = "ID"
REGION_LANG = {"ID": "id"}

REGION_POOL = ["TH", "ME", "BR", "VN", "PH", "SG", "MY", "MX"]
region_index = 0
REGION_LOCK = threading.Lock()

def get_next_region():
    global region_index
    with REGION_LOCK:
        region_index = (region_index + 1) % len(REGION_POOL)
        return REGION_POOL[region_index]

THREAD_COUNT = 100
FAIL_SLEEP = 0
MAX_GENERATE = 0

WATERMARK = "XENON FF TEAM"
CHANNEL_LINK = "https://whatsapp.com/channel/0029Vb8wnA5LdQek3w0nUw1S"
OWNER_NAME = "Xenon Flash"
VERSION = "v3.5.0"

last_success_time = time.time()
stuck_warning_shown = False
file_lock = threading.RLock()
session_pool = deque()
session_lock = threading.Lock()
running = True
target_mode_active = False
target_id = None
target_progress = 0
rare_only = False
custom_prefix = ""

stats = {
    'total': 0, 'same_5': 0, 'same_6': 0,
    'same_7': 0, 'same_8': 0, 'same_9': 0,
    'same_10': 0, 'same_11plus': 0, 'start_time': time.time()
}
stats_lock = threading.Lock()
stuck_monitor_active = True

class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_WHITE = '\033[97m'

    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    BG_BRIGHT_BLACK = '\033[100m'
    BG_BRIGHT_RED = '\033[101m'
    BG_BRIGHT_GREEN = '\033[102m'
    BG_BRIGHT_YELLOW = '\033[103m'
    BG_BRIGHT_BLUE = '\033[104m'
    BG_BRIGHT_MAGENTA = '\033[105m'
    BG_BRIGHT_CYAN = '\033[106m'
    BG_BRIGHT_WHITE = '\033[107m'

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
            print(f"{C.GREEN}  Loaded {len(proxies)-1} proxies from proxy.txt{C.RESET}")
        except Exception as e:
            print(f"{C.YELLOW}  Error loading proxy.txt: {e}{C.RESET}")
    else:
        print(f"{C.YELLOW}  No proxy.txt found - create one with ip:port per line{C.RESET}")
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

def generate_cool_name():
    global custom_prefix
    name_format = load_name_format()

    suffix_chars = ['⁰','¹','²','³','⁴','⁵','⁶','⁷','⁸','⁹']
    suffix_length = random.randint(3, 5)
    suffix = ''.join(random.choice(suffix_chars) for _ in range(suffix_length))

    if custom_prefix:
        return custom_prefix + suffix

    if name_format == "numbers":
        length = random.randint(8, 12)
        base = ''.join(random.choices(string.digits, k=length))
        return base + suffix
    else:
        chars = string.ascii_letters + string.digits
        length = random.randint(8, 12)
        base = ''.join(random.choices(chars, k=length))
        return base + suffix

def generate_password():
    pwd_format = load_password_format()
    if pwd_format == "standard":
        digits = ''.join(random.choices(string.digits, k=random.randint(4, 6)))
        letters = ''.join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
        return f"XENON{digits}{letters}"
    else:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(8, 12)))

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
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    data = bytes.fromhex(hex_data)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, AES.block_size))

def encrypt_api(plain_hex):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    plain = bytes.fromhex(plain_hex)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(plain, AES.block_size)).hex()

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
            new_content = existing + content
            write_file_atomic(filepath, new_content)
        except:
            pass

def load_output_mode():
    content = read_file_safe(OUTPUT_MODE_FILE).strip()
    return content if content else "clean"

def save_output_mode(mode):
    write_file_atomic(OUTPUT_MODE_FILE, mode)

def load_thread_count():
    content = read_file_safe(THREAD_COUNT_FILE).strip()
    try:
        return int(content) if content else 100
    except:
        return 100

def save_thread_count(count):
    write_file_atomic(THREAD_COUNT_FILE, str(count))

def load_max_generate():
    content = read_file_safe(MAX_GENERATE_FILE).strip()
    try:
        return int(content) if content else 0
    except:
        return 0

def save_max_generate(count):
    write_file_atomic(MAX_GENERATE_FILE, str(count))

def load_password_format():
    content = read_file_safe(PASSWORD_FORMAT_FILE).strip()
    return content if content in ["standard", "custom"] else "standard"

def save_password_format(format_type):
    write_file_atomic(PASSWORD_FORMAT_FILE, format_type)

def load_name_format():
    content = read_file_safe(NAME_FORMAT_FILE).strip()
    return content if content in ["numbers", "letters"] else "numbers"

def save_name_format(format_type):
    write_file_atomic(NAME_FORMAT_FILE, format_type)

def load_custom_prefix():
    content = read_file_safe(CUSTOM_NAME_FILE).strip()
    return content if content else ""

def save_custom_prefix(prefix):
    write_file_atomic(CUSTOM_NAME_FILE, prefix)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_device_fingerprint():
    with file_lock:
        try:
            content = read_file_safe(DEVICE_FILE).strip()
            if content:
                return content
            raw = secrets.token_hex(16)
            device_id = hashlib.sha256(raw.encode()).hexdigest()[:32]
            write_file_atomic(DEVICE_FILE, device_id)
            return device_id
        except:
            return hashlib.sha256(secrets.token_hex(16).encode()).hexdigest()[:32]

def get_user_key():
    with file_lock:
        try:
            content = read_file_safe(USER_KEY_FILE).strip()
            if content:
                return content
            device_id = get_device_fingerprint()
            raw_key = hashlib.sha256(device_id.encode()).hexdigest()[:15].upper()
            formatted = f"{raw_key[:5]}-{raw_key[5:10]}-{raw_key[10:15]}"
            write_file_atomic(USER_KEY_FILE, formatted)
            return formatted
        except:
            return "N/A"

def check_version():
    return True

def config_menu():
    global THREAD_COUNT, custom_prefix, MAX_GENERATE
    clear_screen()
    print(f"\n  {C.CYAN}Configuration{C.RESET}")
    print()

    current_mode = load_output_mode()
    mode_display = "Clean" if current_mode == "clean" else "Full"
    print(f"  {C.GREEN}[1]{C.RESET} Output Format    : {C.WHITE}{mode_display}{C.RESET}")
    print()

    current_threads = load_thread_count()
    print(f"  {C.GREEN}[2]{C.RESET} Thread Count     : {C.WHITE}{current_threads}{C.RESET}")
    print()

    current_max = load_max_generate()
    max_display = str(current_max) if current_max > 0 else "Unlimited"
    print(f"  {C.GREEN}[3]{C.RESET} Max Generate     : {C.WHITE}{max_display}{C.RESET}")
    print()

    pwd_format = load_password_format()
    pwd_display = "XENONXXXX" if pwd_format == "standard" else "Custom"
    print(f"  {C.GREEN}[4]{C.RESET} Password Type    : {C.WHITE}{pwd_display}{C.RESET}")
    print()

    name_format = load_name_format()
    name_display = "Numbers" if name_format == "numbers" else "Mixed"
    print(f"  {C.GREEN}[5]{C.RESET} Name Type        : {C.WHITE}{name_display}{C.RESET}")
    print()

    prefix = load_custom_prefix()
    prefix_display = prefix if prefix else "None"
    print(f"  {C.GREEN}[6]{C.RESET} Name Prefix      : {C.WHITE}{prefix_display}{C.RESET}")
    print()

    print(f"  {C.RED}[7]{C.RESET} Back{C.RESET}")
    print()
    choice = input(f"  {C.GREEN}Select: {C.RESET}").strip()

    if choice == '1':
        clear_screen()
        print(f"\n  {C.CYAN}Output Format{C.RESET}")
        print()
        print(f"  {C.GREEN}[1]{C.RESET} Clean - Account ID | Name | Rarity | Percentage")
        print(f"  {C.GREEN}[2]{C.RESET} Full  - UID | Account ID | Password | Rarity")
        print()
        sub = input(f"  {C.GREEN}Select: {C.RESET}").strip()
        if sub == '2':
            save_output_mode('full')
            print(f"\n  {C.GREEN}Full mode activated{C.RESET}")
        else:
            save_output_mode('clean')
            print(f"\n  {C.GREEN}Clean mode activated{C.RESET}")
        time.sleep(0.8)
        return config_menu()

    elif choice == '2':
        clear_screen()
        print(f"\n  {C.CYAN}Thread Count{C.RESET}")
        print()
        print(f"  Current: {C.WHITE}{THREAD_COUNT}{C.RESET}")
        print(f"  Recommended: 50-200")
        print()
        try:
            new_threads = int(input(f"  {C.GREEN}Threads: {C.RESET}").strip())
            if 1 <= new_threads <= 500:
                THREAD_COUNT = new_threads
                save_thread_count(THREAD_COUNT)
                print(f"\n  {C.GREEN}Threads set to {THREAD_COUNT}{C.RESET}")
            else:
                print(f"\n  {C.RED}Invalid value (1-500){C.RESET}")
        except:
            print(f"\n  {C.RED}Invalid input{C.RESET}")
        time.sleep(0.8)
        return config_menu()

    elif choice == '3':
        clear_screen()
        print(f"\n  {C.CYAN}Max Generate{C.RESET}")
        print()
        print(f"  Current: {C.WHITE}{max_display}{C.RESET}")
        print(f"  0 = Unlimited")
        print(f"  Example: 300 will stop after 300 accounts")
        print()
        try:
            new_max = int(input(f"  {C.GREEN}Max: {C.RESET}").strip())
            if new_max >= 0:
                MAX_GENERATE = new_max
                save_max_generate(MAX_GENERATE)
                display = str(MAX_GENERATE) if MAX_GENERATE > 0 else "Unlimited"
                print(f"\n  {C.GREEN}Max generate set to {display}{C.RESET}")
            else:
                print(f"\n  {C.RED}Invalid value (0 or positive){C.RESET}")
        except:
            print(f"\n  {C.RED}Invalid input{C.RESET}")
        time.sleep(0.8)
        return config_menu()

    elif choice == '4':
        clear_screen()
        print(f"\n  {C.CYAN}Password Format{C.RESET}")
        print()
        print(f"  {C.GREEN}[1]{C.RESET} Standard - XENONXXXX")
        print(f"  {C.GREEN}[2]{C.RESET} Custom   - Random Alphanumeric")
        print()
        sub = input(f"  {C.GREEN}Select: {C.RESET}").strip()
        if sub == '2':
            save_password_format('custom')
            print(f"\n  {C.GREEN}Custom password format activated{C.RESET}")
        else:
            save_password_format('standard')
            print(f"\n  {C.GREEN}Standard password format activated{C.RESET}")
        time.sleep(0.8)
        return config_menu()

    elif choice == '5':
        clear_screen()
        print(f"\n  {C.CYAN}Name Format{C.RESET}")
        print()
        print(f"  {C.GREEN}[1]{C.RESET} Numbers Only")
        print(f"  {C.GREEN}[2]{C.RESET} Mixed (Letters + Numbers)")
        print()
        sub = input(f"  {C.GREEN}Select: {C.RESET}").strip()
        if sub == '2':
            save_name_format('letters')
            print(f"\n  {C.GREEN}Mixed name format activated{C.RESET}")
        else:
            save_name_format('numbers')
            print(f"\n  {C.GREEN}Numbers only name format activated{C.RESET}")
        time.sleep(0.8)
        return config_menu()

    elif choice == '6':
        clear_screen()
        print(f"\n  {C.CYAN}Name Prefix{C.RESET}")
        print()
        print(f"  Current: {C.WHITE}{prefix_display}{C.RESET}")
        print(f"  Example: XENONFLASH -> XENONFLASH²⁴⁶")
        print(f"  Leave empty to disable")
        print()
        new_prefix = input(f"  {C.GREEN}Prefix: {C.RESET}").strip().upper()
        if new_prefix:
            custom_prefix = new_prefix
            save_custom_prefix(custom_prefix)
            print(f"\n  {C.GREEN}Prefix set to {custom_prefix}{C.RESET}")
        else:
            custom_prefix = ""
            save_custom_prefix("")
            print(f"\n  {C.GREEN}Prefix disabled{C.RESET}")
        time.sleep(0.8)
        return config_menu()
    else:
        return

def show_loading_screen():
    clear_screen()
    print(f"\n  {C.CYAN}XENON FF CHECKER{C.RESET}")
    print()
    print(f"  Version  : {C.WHITE}{VERSION}{C.RESET}")
    print(f"  Owner    : {C.WHITE}{OWNER_NAME}{C.RESET}")
    print(f"  Channel  : {C.WHITE}{CHANNEL_LINK}{C.RESET}")
    print()
    print(f"  {C.YELLOW}Loading...{C.RESET}")
    time.sleep(0.8)
    print(f"  {C.GREEN}Ready{C.RESET}")
    time.sleep(0.5)

def show_banner():
    clear_screen()
    print(f"\n  {C.CYAN}XENON FF CHECKER{C.RESET}")
    print()
    print(f"  Version  : {C.WHITE}{VERSION}{C.RESET}")
    print(f"  Owner    : {C.WHITE}{OWNER_NAME}{C.RESET}")
    print(f"  Channel  : {C.WHITE}{CHANNEL_LINK}{C.RESET}")
    print()
    # Features lengkap sesuai konfigurasi
    print(f"  {C.DIM}Features:{C.RESET}")
    print(f"    - Auto Proxy Loader")
    print(f"    - Auto Region Rotation")
    print(f"    - Bypass Protection")
    print(f"    - Custom Name Prefix")
    print(f"    - Max Generate Limit")
    print(f"    - Output Format (Clean/Full)")
    print(f"    - Thread Count Adjustable")
    print(f"    - Password Type (Standard/Custom)")
    print(f"    - Name Type (Numbers/Mixed)")
    print(f"    - Per-Account JSON Saving")
    print()

def show_menu():
    show_banner()
    print(f"  {C.GREEN}[1]{C.RESET}  Normal Mode")
    print(f"  {C.YELLOW}[2]{C.RESET}  Target Mode")
    print(f"  {C.CYAN}[3]{C.RESET}  Configuration")
    print(f"  {C.RED}[4]{C.RESET}  Exit")
    print()
    print(f"  {C.DIM}Rarity: BIASA | JARANG | LANGKA | EPIK | LEGENDA | DEWA | MAHA DEWA{C.RESET}")
    print()
    return input(f"  {C.GREEN}Select: {C.RESET}").strip()

def get_color_for_digit(count):
    if count >= 9:
        return C.BG_BRIGHT_YELLOW + C.BLACK
    elif count == 8:
        return C.BG_BRIGHT_RED + C.WHITE
    elif count == 7:
        return C.BG_BRIGHT_MAGENTA + C.WHITE
    elif count == 6:
        return C.BG_BRIGHT_CYAN + C.BLACK
    elif count == 5:
        return C.BG_BRIGHT_BLUE + C.WHITE
    return C.WHITE

def get_rarity(same_count):
    if same_count >= 9:
        return f"{C.BG_BRIGHT_YELLOW}{C.BLACK} MAHA DEWA {C.RESET}", "MAHA DEWA", 99
    elif same_count == 8:
        return f"{C.BG_BRIGHT_RED}{C.WHITE} DEWA {C.RESET}", "DEWA", 85
    elif same_count == 7:
        return f"{C.BG_BRIGHT_MAGENTA}{C.WHITE} LEGENDA {C.RESET}", "LEGENDA", 70
    elif same_count == 6:
        return f"{C.BG_BRIGHT_CYAN}{C.BLACK} EPIK {C.RESET}", "EPIK", 50
    elif same_count == 5:
        return f"{C.BG_BRIGHT_BLUE}{C.WHITE} LANGKA {C.RESET}", "LANGKA", 30
    elif same_count == 4:
        return f"{C.BG_GREEN}{C.BLACK} JARANG {C.RESET}", "JARANG", 15
    else:
        return f"{C.DIM} BIASA {C.RESET}", "BIASA", 5

def count_same_digits(account_id):
    aid = str(account_id)
    if not aid.isdigit() or len(aid) < 5:
        return 0, None
    analyzed = aid[1:]
    digit_counts = Counter(analyzed)
    max_count = max(digit_counts.values()) if digit_counts else 0
    most_digit = max(digit_counts, key=digit_counts.get) if digit_counts else None
    return max_count, most_digit

def save_account_by_rarity(account_data, custom_name=""):
    try:
        same_count = account_data.get('same_digit_count', 0)
        most_digit = account_data.get('most_digit', '')
        uid = account_data.get('uid', 'N/A')
        aid = account_data.get('account_id', 'N/A')
        password = account_data.get('password', 'N/A')
        name = account_data.get('name', 'N/A')
        created_at = account_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        jwt_token = account_data.get('jwt_token', '')

        _, rarity_name, _ = get_rarity(same_count)

        rarity_folder_map = {
            'MAHA DEWA': 'mahadewa',
            'DEWA': 'dewa',
            'LEGENDA': 'legenda',
            'EPIK': 'epik',
            'LANGKA': 'langka',
            'JARANG': 'jarang',
            'BIASA': 'biasa'
        }

        folder_name = rarity_folder_map.get(rarity_name, 'other')
        rarity_folder = os.path.join(SPECIAL_FOLDER, folder_name)
        os.makedirs(rarity_folder, exist_ok=True)

        # --- PER ACCOUNT JSON (NAMA FILE = ACCOUNT ID) ---
        json_file = os.path.join(rarity_folder, f"{aid}.json")

        account_entry = {
            "uid": uid,
            "account_id": aid,
            "password": password,
            "name": name,
            "same_digit_count": same_count,
            "most_digit": most_digit,
            "rarity": rarity_name,
            "created_at": created_at,
            "jwt_token": jwt_token,
            "region": REGION_NAME,
            "custom_name": custom_name,
            "watermark": WATERMARK
        }

        with file_lock:
            # Tulis file JSON per account
            write_file_atomic(json_file, json.dumps(account_entry, indent=2, ensure_ascii=False))

            # Tetap buat file .txt untuk list semua akun di folder rarity
            txt_file = os.path.join(rarity_folder, f"{folder_name}.txt")
            digit_info = f"{most_digit}x{same_count}" if most_digit else f"{same_count}x"
            txt_entry = f"{uid} | {aid} | {password} | {digit_info} | [{rarity_name}]\n"
            append_file_atomic(txt_file, txt_entry)

            # Update cariid.txt (urut berdasarkan rarity)
            cariid_file = os.path.join(SPECIAL_FOLDER, "cariid.txt")
            all_entries = []
            if os.path.exists(cariid_file):
                content = read_file_safe(cariid_file)
                lines = content.split('\n')
                if lines:
                    header = lines[0] if lines[0].startswith('[') else "[9] [8] [7] [6] [5] (URUTAN SAME DIGIT TERBANYAK)\n\n"
                    all_entries = [line for line in lines[2:] if line.strip()]

            display_uid = f"{uid} | {password}" if custom_name else uid
            new_entry = f"[{same_count}] {display_uid} | {aid} | {digit_info} | [{rarity_name}]"
            all_entries.append(new_entry)

            def sort_key(line):
                for digit in range(9, 0, -1):
                    if f"[{digit}]" in line:
                        return -digit
                return 0

            all_entries.sort(key=sort_key)
            final_content = "[9] [8] [7] [6] [5] (URUTAN SAME DIGIT TERBANYAK)\n\n" + '\n'.join(all_entries) + '\n'
            write_file_atomic(cariid_file, final_content)

    except Exception as e:
        pass

def save_account_all(account_data, custom_name=""):
    try:
        same_count = account_data.get('same_digit_count', 0)
        most_digit = account_data.get('most_digit', '')
        uid = account_data.get('uid', 'N/A')
        aid = account_data.get('account_id', 'N/A')
        password = account_data.get('password', 'N/A')
        name = account_data.get('name', 'N/A')
        created_at = account_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        jwt_token = account_data.get('jwt_token', '')

        _, rarity_name, _ = get_rarity(same_count)

        account_json_file = os.path.join(ALL_FOLDER, "account.json")
        id_txt_file = os.path.join(ALL_FOLDER, "id.txt")

        with file_lock:
            all_accounts = []
            if os.path.exists(account_json_file):
                try:
                    with open(account_json_file, 'r', encoding='utf-8') as f:
                        all_accounts = json.load(f)
                except:
                    all_accounts = []

            account_entry = {
                "uid": uid,
                "account_id": aid,
                "password": password,
                "name": name,
                "same_digit_count": same_count,
                "most_digit": most_digit,
                "rarity": rarity_name,
                "created_at": created_at,
                "jwt_token": jwt_token,
                "region": REGION_NAME,
                "custom_name": custom_name
            }
            all_accounts.append(account_entry)
            write_file_atomic(account_json_file, json.dumps(all_accounts, indent=2, ensure_ascii=False))

            all_ids = []
            for acc in all_accounts:
                all_ids.append(acc.get('account_id', 'N/A'))
            write_file_atomic(id_txt_file, '\n'.join(all_ids))
    except:
        pass

def print_output(no, account_data, output_mode, custom_name="", rare_only=False, max_gen=0):
    same_count = account_data.get('same_digit_count', 0)
    most_digit = account_data.get('most_digit', '')
    uid = account_data.get('uid', 'N/A')
    aid = account_data.get('account_id', 'N/A')
    password = account_data.get('password', 'N/A')
    name_display = account_data.get('name', 'N/A')

    if rare_only and same_count < 5:
        return False

    color = get_color_for_digit(same_count)
    rarity_colored, rarity_name, percentage = get_rarity(same_count)
    prefix = f"[{custom_name}]" if custom_name else ""
    digit_info = f"{most_digit}x{same_count}" if most_digit and same_count >= 5 else ""

    no_str = f"{no:4d}"

    if max_gen > 0:
        progress = f"{no}/{max_gen}"
    else:
        progress = f"{no}"

    if output_mode == 'full':
        if same_count >= 5:
            print(f"{color}{progress}  {prefix} {uid}  |  {aid}  |  {password}  |  {rarity_colored}  |  {digit_info}  |  {C.GREEN}{percentage:2d}%{C.RESET}")
        else:
            print(f"{C.WHITE}{progress}  {prefix} {uid}  |  {aid}  |  {password}  |  {rarity_colored}  |  {C.GREEN}{percentage:2d}%{C.RESET}")
    else:
        if same_count >= 5:
            print(f"{color}{progress}  {prefix} {aid}  |  {name_display}  |  {rarity_colored}  |  {digit_info}  |  {C.GREEN}{percentage:2d}%{C.RESET}")
        else:
            print(f"{C.WHITE}{progress}  {prefix} {aid}  |  {name_display}  |  {rarity_colored}  |  {C.GREEN}{percentage:2d}%{C.RESET}")
    return True

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

def show_stuck_warning():
    global stuck_warning_shown
    if stuck_warning_shown:
        return
    stuck_warning_shown = True
    print(f"\n  {C.RED}Rate Limit Detected{C.RESET}")
    print()
    print(f"  No generation in last 10 seconds")
    print(f"  Possible IP ban detected")
    print()
    print(f"  Solution: Change IP or use proxy")
    print()
    stuck_warning_shown = False

def stuck_monitor():
    global last_success_time, stuck_monitor_active
    while stuck_monitor_active:
        time.sleep(10)
        if not running:
            break
        elapsed = time.time() - last_success_time
        if elapsed > 10 and stats['total'] > 0:
            show_stuck_warning()

monitor_thread = threading.Thread(target=stuck_monitor, daemon=True)
monitor_thread.start()

def worker(output_mode, custom_name="", rare_only=False, max_gen=0):
    global running, last_success_time, target_mode_active, target_id, target_progress
    while running:
        if max_gen > 0 and stats['total'] >= max_gen:
            running = False
            break
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
                if same_count == 5:
                    stats['same_5'] += 1
                elif same_count == 6:
                    stats['same_6'] += 1
                elif same_count == 7:
                    stats['same_7'] += 1
                elif same_count == 8:
                    stats['same_8'] += 1
                elif same_count == 9:
                    stats['same_9'] += 1
                elif same_count == 10:
                    stats['same_10'] += 1
                elif same_count >= 11:
                    stats['same_11plus'] += 1
                current_no = stats['total']
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
            if target_mode_active and target_id:
                if aid == target_id or uid == target_id:
                    print()
                    print(f"  {C.BG_BRIGHT_GREEN}{C.BLACK} TARGET FOUND {C.RESET}")
                    print()
                    print(f"  UID  : {C.WHITE}{uid}{C.RESET}")
                    print(f"  ID   : {C.WHITE}{aid}{C.RESET}")
                    print(f"  Pass : {C.WHITE}{password}{C.RESET}")
                    print()
                    target_progress = 0
                else:
                    target_progress += 1
                    if target_progress % 10 == 0:
                        print(f"  {C.YELLOW}Target search: {target_progress} checked{C.RESET}")
            printed = print_output(current_no, account_info, output_mode, custom_name, rare_only, max_gen)
            if same_count >= 5:
                save_account_by_rarity(account_info, custom_name)
            else:
                save_account_all(account_info, custom_name)
            last_success_time = time.time()
        else:
            time.sleep(FAIL_SLEEP)

def activation_flow():
    clear_screen()
    show_banner()
    print(f"  {C.GREEN}Ready{C.RESET}")
    time.sleep(1)
    return "license", "XENON-PROXY-1337", {"expiry": "2099-12-31", "duration": "Unlimited"}

def run_generator(output_mode, custom_name="", rare_only=False, is_target=False):
    global running, target_mode_active, target_id, target_progress, THREAD_COUNT, MAX_GENERATE
    clear_screen()
    show_banner()

    mode_text = "Target" if is_target else "Normal"
    max_display = str(MAX_GENERATE) if MAX_GENERATE > 0 else "Unlimited"

    print(f"  {C.CYAN}Generator Status{C.RESET}")
    print()
    print(f"  Mode    : {C.WHITE}{mode_text}{C.RESET}")
    print(f"  Output  : {C.WHITE}{output_mode.upper()}{C.RESET}")
    print(f"  Threads : {C.WHITE}{THREAD_COUNT}{C.RESET}")
    print(f"  Max Gen : {C.WHITE}{max_display}{C.RESET}")
    if is_target:
        print(f"  Target  : {C.WHITE}{target_id}{C.RESET}")
    if custom_name:
        print(f"  Prefix  : {C.WHITE}{custom_name}{C.RESET}")
    print()
    print(f"  {C.DIM}Rarity: BIASA | JARANG | LANGKA | EPIK | LEGENDA | DEWA | MAHA DEWA{C.RESET}")
    print()
    print(f"  {C.GREEN}Save: XENON_FF/special/ & XENON_FF/allaccount/{C.RESET}")
    print()
    print(f"  {C.YELLOW}Press CTRL+C to stop{C.RESET}")
    print()
    try:
        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            futures = [executor.submit(worker, output_mode, custom_name, rare_only, MAX_GENERATE) for _ in range(THREAD_COUNT)]
            for future in as_completed(futures):
                if not running:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                future.result()
    except KeyboardInterrupt:
        print()
        print(f"  {C.YELLOW}Stopped{C.RESET}")
        running = False
        time.sleep(1)
    except Exception as e:
        print()
        print(f"  {C.RED}Error: {e}{C.RESET}")
    time.sleep(1)
    elapsed = time.time() - stats['start_time']
    print()
    print(f"  {C.CYAN}Summary{C.RESET}")
    print()
    print(f"  Total      : {C.WHITE}{stats['total']}{C.RESET}")
    print(f"  LANGKA     : {C.WHITE}{stats['same_5']}{C.RESET}")
    print(f"  EPIK       : {C.WHITE}{stats['same_6']}{C.RESET}")
    print(f"  LEGENDA    : {C.WHITE}{stats['same_7']}{C.RESET}")
    print(f"  DEWA       : {C.WHITE}{stats['same_8']}{C.RESET}")
    print(f"  MAHA DEWA  : {C.WHITE}{stats['same_9'] + stats['same_10'] + stats['same_11plus']}{C.RESET}")
    print()
    print(f"  Time       : {C.WHITE}{elapsed:.1f}s{C.RESET}")
    if elapsed > 0:
        print(f"  Speed      : {C.WHITE}{stats['total']/elapsed:.2f}/s{C.RESET}")
    print()
    input(f"  {C.GREEN}Press ENTER to continue{C.RESET}")

def main():
    global running, THREAD_COUNT, REGION, REGION_NAME, PROXY_LIST, target_mode_active, target_id, custom_prefix, MAX_GENERATE

    show_loading_screen()

    PROXY_LIST = load_proxies_from_file()
    check_version()
    print()
    mode, key, info = activation_flow()

    clear_screen()
    show_banner()

    if len(PROXY_LIST) > 1:
        print(f"  {C.GREEN}Proxy loaded: {len(PROXY_LIST)-1}{C.RESET}")
    else:
        print(f"  {C.YELLOW}No proxy.txt found{C.RESET}")
    print()

    THREAD_COUNT = load_thread_count()
    custom_prefix = load_custom_prefix()
    MAX_GENERATE = load_max_generate()
    print(f"  {C.GREEN}Threads: {THREAD_COUNT}{C.RESET}")
    if custom_prefix:
        print(f"  {C.GREEN}Prefix : {custom_prefix}{C.RESET}")
    max_display = str(MAX_GENERATE) if MAX_GENERATE > 0 else "Unlimited"
    print(f"  {C.GREEN}Max Gen: {max_display}{C.RESET}")
    time.sleep(0.5)

    while True:
        choice = show_menu()

        if choice == '1':
            running = True
            stats['total'] = 0
            stats['same_5'] = 0
            stats['same_6'] = 0
            stats['same_7'] = 0
            stats['same_8'] = 0
            stats['same_9'] = 0
            stats['same_10'] = 0
            stats['same_11plus'] = 0
            stats['start_time'] = time.time()
            output_mode = load_output_mode()
            target_mode_active = False
            target_id = None
            run_generator(output_mode, custom_prefix, False, False)
        elif choice == '2':
            clear_screen()
            print(f"\n  {C.CYAN}Target Mode{C.RESET}")
            print()
            print(f"  Enter the target ID to search for")
            print()
            target_input = input(f"  {C.GREEN}Target ID: {C.RESET}").strip()
            if target_input:
                target_id = target_input
                target_mode_active = True
                running = True
                stats['total'] = 0
                stats['same_5'] = 0
                stats['same_6'] = 0
                stats['same_7'] = 0
                stats['same_8'] = 0
                stats['same_9'] = 0
                stats['same_10'] = 0
                stats['same_11plus'] = 0
                stats['start_time'] = time.time()
                output_mode = load_output_mode()
                run_generator(output_mode, custom_prefix, False, True)
            else:
                print(f"  {C.RED}No target entered{C.RESET}")
                time.sleep(1)
        elif choice == '3':
            config_menu()
        elif choice == '4':
            print(f"\n  {C.GREEN}Goodbye{C.RESET}\n")
            break

if __name__ == "__main__":
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        main()
    except ImportError:
        print(f"{C.RED}Error: pip install pycryptodome{C.RESET}")
        sys.exit(0)