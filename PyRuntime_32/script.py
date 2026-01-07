import json
import hashlib
import time
import re
import os
import sys
import argparse
import uuid
import base64
import random
import string
from pathlib import Path
from typing import Optional, List, Dict, Any
import urllib.parse

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Error: Library 'requests' diperlukan. Install dengan: pip install requests")
    exit(1)

# Coba import cloudscraper untuk bypass Cloudflare (opsional tapi direkomendasikan)
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    print("[PERINGATAN] cloudscraper tidak terinstall. Install untuk bypass Cloudflare yang lebih baik:")
    print("       pip install cloudscraper")

# Konstanta
SHEERID_API = "https://services.sheerid.com/rest/v2"
CHATGPT_API = "https://chatgpt.com/backend-api"
DEFAULT_PROGRAM_ID = "690415d58971e73ca187d8c9"
GUERRILLA_MAIL_API = "https://api.guerrillamail.com/ajax.php"

# File paths
PROXY_FILE = "proxy.txt"
USED_FILE = "used.txt"

# Military Branch Organization IDs
BRANCH_ORG_MAP = {
    "Army": {"id": 4070, "name": "Army"},
    "Air Force": {"id": 4073, "name": "Air Force"},
    "Navy": {"id": 4072, "name": "Navy"},
    "Marine Corps": {"id": 4071, "name": "Marine Corps"},
    "Coast Guard": {"id": 4074, "name": "Coast Guard"},
    "Space Force": {"id": 4544268, "name": "Space Force"},
    "Army National Guard": {"id": 4075, "name": "Army National Guard"},
    "Army Reserve": {"id": 4076, "name": "Army Reserve"},
    "Air National Guard": {"id": 4079, "name": "Air National Guard"},
    "Air Force Reserve": {"id": 4080, "name": "Air Force Reserve"},
    "Navy Reserve": {"id": 4078, "name": "Navy Reserve"},
    "Marine Corps Reserve": {"id": 4077, "name": "Marine Corps Forces Reserve"},
    "Coast Guard Reserve": {"id": 4081, "name": "Coast Guard Reserve"},
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"

# Semua domain Guerrilla Mail yang tersedia
GUERRILLA_DOMAINS = [
    "sharklasers.com",          # Utama
    "guerrillamail.com",        # Utama
    "guerrillamail.info",       # Alternatif 1
    "grr.la",                   # Alternatif 2 (pendek)
    "guerrillamail.biz",        # Alternatif 3
    "guerrillamail.de",         # Alternatif 4 (Jerman)
    "guerrillamail.net",        # Alternatif 5
    "guerrillamail.org",        # Alternatif 6
    "guerrillamailblock.com",   # Alternatif 7
    "pokemail.net",             # Alternatif 8
    "spam4.me",                 # Alternatif 9
    "guerrillamail.fr",         # Alternatif 10 (Prancis)
    "guerrillamail.nl",         # Alternatif 11 (Belanda)
]

def create_session_with_retry(proxies=None, use_cloudscraper=True):
    """Buat sesi HTTP dengan logika retry"""
    if use_cloudscraper and HAS_CLOUDSCRAPER:
        try:
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
                delay=10,
            )
            if proxies:
                scraper.proxies = proxies
            return scraper, True
        except Exception as e:
            print(f"[PERINGATAN] Gagal membuat cloudscraper: {e}")
    
    # Fallback ke requests
    session = requests.Session()
    
    # Konfigurasi strategi retry
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    if proxies:
        session.proxies = proxies
    
    return session, False

# ============ FUNGSI FORMATTING PROXY ============
def format_proxy(proxy_str: str) -> Optional[Dict[str, str]]:
    """Format string proxy ke dict untuk library requests"""
    if not proxy_str:
        return None
    
    # Jika sudah format http:// atau https://
    if proxy_str.startswith(('http://', 'https://')):
        return {"http": proxy_str, "https": proxy_str}
    
    # Format: ip:port
    if ':' in proxy_str and '@' not in proxy_str:
        parts = proxy_str.split(':')
        if len(parts) == 2:
            ip, port = parts
            # Validasi IP dan port
            if port.isdigit() and 1 <= int(port) <= 65535:
                proxy_url = f"http://{ip}:{port}"
                return {"http": proxy_url, "https": proxy_url}
    
    # Format: ip:port:user:pass
    elif proxy_str.count(':') == 3:
        parts = proxy_str.split(':')
        if len(parts) == 4:
            ip, port, user, password = parts
            if port.isdigit() and 1 <= int(port) <= 65535:
                proxy_url = f"http://{user}:{password}@{ip}:{port}"
                return {"http": proxy_url, "https": proxy_url}
    
    # Format lain, return as-is
    proxy_url = f"http://{proxy_str}"
    return {"http": proxy_url, "https": proxy_url}

def mask_proxy_url(proxy_url: str) -> str:
    """Mask URL proxy untuk keamanan"""
    if not proxy_url:
        return ""
    
    # Jika format http://user:pass@ip:port
    if '@' in proxy_url:
        parts = proxy_url.split('@')
        if len(parts) == 2:
            auth_part = parts[0]
            # Hapus http:// atau https://
            if auth_part.startswith('http://'):
                auth_part = auth_part[7:]
            elif auth_part.startswith('https://'):
                auth_part = auth_part[8:]
            
            if ':' in auth_part:
                user_pass = auth_part.split(':')
                if len(user_pass) >= 2:
                    user_pass[1] = "*****"
                    masked_auth = ":".join(user_pass)
                    return f"http://{masked_auth}@{parts[1]}"
    
    # Return sebagian saja
    return proxy_url[:30] + "..." if len(proxy_url) > 30 else proxy_url

def load_proxies(file_path: str = None) -> List[str]:
    """Load daftar proxy dari file"""
    path = Path(file_path or PROXY_FILE)
    if not path.exists():
        return []
    
    proxies = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            proxies.append(line)
    
    print(f"[DEBUG] Memuat {len(proxies)} proxy mentah dari file")
    return proxies


def get_used_data() -> set:
    """Load data yang sudah digunakan"""
    path = Path(__file__).parent / USED_FILE
    if not path.exists():
        return set()
    return set(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def is_data_used(first_name: str, last_name: str, dob: str) -> bool:
    """Cek apakah data sudah digunakan"""
    key = f"{first_name.upper()}|{last_name.upper()}|{dob}"
    return key in get_used_data()


def mark_data_used(first_name: str, last_name: str, dob: str):
    """Tandai data sebagai sudah digunakan"""
    path = Path(__file__).parent / USED_FILE
    key = f"{first_name.upper()}|{last_name.upper()}|{dob}"
    with open(path, "a", encoding="utf-8") as f:
        f.write(key + "\n")


def generate_fingerprint():
    """Generate device fingerprint"""
    screens = ["1920x1080", "2560x1440", "1366x768"]
    screen = screens[hash(str(time.time())) % len(screens)]
    raw = f"{screen}|{time.time()}|{uuid.uuid4()}"
    return hashlib.md5(raw.encode()).hexdigest()


def generate_newrelic_headers():
    """Generate NewRelic tracking headers"""
    trace_id = uuid.uuid4().hex + uuid.uuid4().hex[:8]
    trace_id = trace_id[:32]
    span_id = uuid.uuid4().hex[:16]
    timestamp = int(time.time() * 1000)
    
    payload = {
        "v": [0, 1],
        "d": {
            "ty": "Browser",
            "ac": "364029",
            "ap": "134291347",
            "id": span_id,
            "tr": trace_id,
            "ti": timestamp
        }
    }
    
    return {
        "newrelic": base64.b64encode(json.dumps(payload).encode()).decode(),
        "traceparent": f"00-{trace_id}-{span_id}-01",
        "tracestate": f"364029@nr=0-1-364029-134291347-{span_id}----{timestamp}"
    }


def match_branch(input_str):
    """Map input string ke nama cabang"""
    normalized = input_str.upper().replace("US ", "").strip()
    
    for branch in BRANCH_ORG_MAP:
        if branch.upper() == normalized:
            return branch
    
    # Fuzzy matching
    if "MARINE" in normalized and "RESERVE" not in normalized:
        return "Marine Corps"
    if "ARMY" in normalized and "NATIONAL" in normalized:
        return "Army National Guard"
    if "ARMY" in normalized and "RESERVE" in normalized:
        return "Army Reserve"
    if "ARMY" in normalized:
        return "Army"
    if "NAVY" in normalized and "RESERVE" in normalized:
        return "Navy Reserve"
    if "NAVY" in normalized:
        return "Navy"
    if "AIR" in normalized and "NATIONAL" in normalized:
        return "Air National Guard"
    if "AIR" in normalized and "RESERVE" in normalized:
        return "Air Force Reserve"
    if "AIR" in normalized:
        return "Air Force"
    if "COAST" in normalized and "RESERVE" in normalized:
        return "Coast Guard Reserve"
    if "COAST" in normalized:
        return "Coast Guard"
    if "SPACE" in normalized:
        return "Space Force"
    
    return "Army"


def parse_data_line(line):
    """Parse baris data: firstName|lastName|branch|birthDate|dischargeDate"""
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 4:
        return None
    
    branch_name = match_branch(parts[2])
    org = BRANCH_ORG_MAP.get(branch_name, BRANCH_ORG_MAP["Army"])
    
    return {
        "firstName": parts[0],
        "lastName": parts[1],
        "branch": branch_name,
        "birthDate": parts[3],
        "dischargeDate": parts[4] if len(parts) > 4 else "2025-01-02",
        "organization": org
    }


class TempEmailService:
    """Class untuk mengelola email temporary menggunakan API Guerrilla Mail"""
    
    def __init__(self, proxies=None, use_random_domain=True):
        self.email_address = None
        self.email_token = None  # Token sesi dari API
        self.session = requests.Session()
        self.use_random_domain = use_random_domain
        
        if proxies:
            self.session.proxies = proxies
        
        print("[EMAIL TEMPORARY] Menggunakan API Guerrilla Mail dengan domain acak")
        print(f"[EMAIL TEMPORARY] Domain yang tersedia: {len(GUERRILLA_DOMAINS)} pilihan")
    
    def generate_email(self):
        """Mendapatkan alamat email baru dari API Guerrilla Mail dengan domain acak"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Jika ingin menggunakan domain acak, set parameter domain
                params = {'f': 'get_email_address'}
                
                if self.use_random_domain:
                    # Pilih domain acak dari list
                    random_domain = random.choice(GUERRILLA_DOMAINS)
                    print(f"   [EMAIL TEMPORARY] Percobaan {attempt+1}: Mencoba domain {random_domain}")
                    
                    # Coba set domain melalui parameter
                    params['domain'] = random_domain
                
                resp = self.session.get(GUERRILLA_MAIL_API, params=params, timeout=30)
                
                if resp.status_code == 200:
                    data = resp.json()
                    self.email_address = data.get('email_addr')
                    self.email_token = data.get('sid_token')
                    
                    if self.email_address and self.email_token:
                        # Verifikasi domain yang digunakan
                        used_domain = self.email_address.split('@')[-1]
                        print(f"   [EMAIL TEMPORARY] BERHASIL Digenerate via API: {self.email_address}")
                        print(f"   [EMAIL TEMPORARY] Domain: {used_domain}")
                        print(f"   [EMAIL TEMPORARY] Token sesi: {self.email_token[:20]}...")
                        
                        # Tampilkan statistik domain
                        self._show_domain_stats(used_domain)
                        
                        return self.email_address
                    else:
                        print(f"   [EMAIL TEMPORARY] Percobaan {attempt+1} gagal: Tidak ada email/token yang dikembalikan")
                        continue
                else:
                    print(f"   [EMAIL TEMPORARY] Percobaan {attempt+1} gagal: HTTP {resp.status_code}")
                    continue
                    
            except Exception as e:
                print(f"   [EMAIL TEMPORARY] Percobaan {attempt+1} gagal: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
        
        # Jika semua percobaan gagal, generate manual dengan domain acak
        print("   [EMAIL TEMPORARY] Semua percobaan API gagal, membuat email manual")
        return self._generate_manual_email()
    
    def _generate_manual_email(self):
        """Generate email manual dengan domain acak"""
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        domain = random.choice(GUERRILLA_DOMAINS)
        self.email_address = f"{username}@{domain}"
        
        print(f"   [EMAIL TEMPORARY] Dibuat manual: {self.email_address}")
        print(f"   [EMAIL TEMPORARY] Catatan: Email manual memiliki akses inbox terbatas")
        
        return self.email_address
    
    def _show_domain_stats(self, used_domain):
        """Tampilkan statistik penggunaan domain"""
        domain_index = GUERRILLA_DOMAINS.index(used_domain) if used_domain in GUERRILLA_DOMAINS else -1
        
        if domain_index >= 0:
            print(f"   [EMAIL TEMPORARY] Index domain: {domain_index + 1}/{len(GUERRILLA_DOMAINS)}")
        
        # Tampilkan beberapa domain lain untuk variasi
        if len(GUERRILLA_DOMAINS) > 1:
            other_domains = random.sample([d for d in GUERRILLA_DOMAINS if d != used_domain], min(3, len(GUERRILLA_DOMAINS)-1))
            print(f"   [EMAIL TEMPORARY] Domain lain yang tersedia: {', '.join(other_domains)}")
    
    def check_email(self, max_attempts=25, delay=4):
        """Memeriksa inbox melalui API untuk mendapatkan link verifikasi"""
        if not self.email_address or not self.email_token:
            print("   [EMAIL TEMPORARY] Tidak ada sesi email aktif. Tidak dapat memeriksa inbox.")
            return None
        
        print(f"   [EMAIL TEMPORARY] Memeriksa inbox untuk: {self.email_address}")
        print(f"   [EMAIL TEMPORARY] Domain: {self.email_address.split('@')[-1]}")
        print(f"   [EMAIL TEMPORARY] Akan memeriksa {max_attempts} kali dengan interval {delay} detik")
        
        last_email_id = 0  # Track ID email terakhir yang dicek
        start_time = time.time()
        
        for attempt in range(max_attempts):
            time.sleep(delay)
            
            try:
                # Fetch daftar email dari inbox
                params = {
                    'f': 'get_email_list',
                    'sid_token': self.email_token,
                    'offset': 0,
                    'seq': 0  # Dapatkan email terbaru
                }
                
                resp = self.session.get(GUERRILLA_MAIL_API, params=params, timeout=15)
                
                if resp.status_code == 200:
                    data = resp.json()
                    emails = data.get('list', [])
                    
                    if emails:
                        # Sort emails by mail_id descending (terbaru pertama)
                        emails.sort(key=lambda x: int(x.get('mail_id', 0)), reverse=True)
                        
                        for email in emails:
                            mail_id = email.get('mail_id')
                            mail_from = email.get('mail_from', '').lower()
                            mail_subject = email.get('mail_subject', '').lower()
                            
                            # Skip jika sudah dicek
                            if int(mail_id) <= last_email_id:
                                continue
                            
                            # Cek jika email dari SheerID
                            if any(keyword in mail_from or keyword in mail_subject 
                                   for keyword in ['sheerid', 'verif', 'verify', 'confirmation']):
                                print(f"   [EMAIL TEMPORARY] BERHASIL Ditemukan email verifikasi (ID: {mail_id})")
                                print(f"   [EMAIL TEMPORARY] Dari: {mail_from[:50]}...")
                                print(f"   [EMAIL TEMPORARY] Subjek: {mail_subject[:50]}...")
                                
                                # Fetch konten email lengkap
                                email_content = self._fetch_email_content(mail_id)
                                if email_content:
                                    # Cari link verifikasi SheerID
                                    link = self._extract_verification_link(email_content)
                                    if link:
                                        elapsed = int(time.time() - start_time)
                                        print(f"   [EMAIL TEMPORARY] BERHASIL Link diekstrak setelah {elapsed} detik!")
                                        last_email_id = int(mail_id)
                                        return link
                                    else:
                                        print(f"   [EMAIL TEMPORARY] Tidak ada link verifikasi di email {mail_id}")
                            else:
                                # Update last_email_id meskipun bukan email verifikasi
                                last_email_id = max(last_email_id, int(mail_id))
                    else:
                        # Tidak ada email di inbox
                        pass
                
                # Tampilkan progress
                if (attempt + 1) % 5 == 0:
                    elapsed = int(time.time() - start_time)
                    print(f"      Memeriksa... ({attempt+1}/{max_attempts}) - {elapsed} detik berlalu")
                    
            except Exception as e:
                print(f"   [DEBUG] Error memeriksa inbox pada percobaan {attempt+1}: {e}")
                continue
        
        elapsed = int(time.time() - start_time)
        print(f"   [EMAIL TEMPORARY] GAGAL Tidak ada email verifikasi ditemukan setelah {max_attempts} percobaan ({elapsed} detik)")
        return None
    
    def _fetch_email_content(self, mail_id):
        """Mengambil konten email spesifik dari API"""
        try:
            params = {
                'f': 'fetch_email',
                'sid_token': self.email_token,
                'email_id': mail_id
            }
            
            resp = self.session.get(GUERRILLA_MAIL_API, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                # Gabungkan subjek dan body
                subject = data.get('mail_subject', '')
                body = data.get('mail_body', '')
                body_excerpt = data.get('mail_excerpt', '')
                
                # Gunakan excerpt jika body kosong
                if not body and body_excerpt:
                    body = body_excerpt
                
                # Decode HTML entities jika ada
                import html
                body = html.unescape(body)
                
                return f"{subject} {body}"
            else:
                print(f"   [DEBUG] Gagal mengambil email {mail_id}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"   [DEBUG] Error mengambil email {mail_id}: {e}")
        
        return None
    
    def _extract_verification_link(self, email_content):
        """Mengekstrak link verifikasi dari konten email"""
        if not email_content:
            return None
        
        # Decode HTML entities
        import html
        email_content = html.unescape(email_content)
        
        patterns = [
            r'https://services\.sheerid\.com/verify/[^\s"\'<>]+emailToken=\d+',
            r'https://services\.sheerid\.com/[^\s"\'<>]+verificationId=[^\s"\'<>]+',
            r'https?://[^\s"\'<>]*sheerid[^\s"\'<>]*verification[^\s"\'<>]*',
            r'https?://services\.sheerid\.com[^\s"\'<>]+',
            r'emailToken=(\d+)',  # Cari token langsung
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, email_content, re.IGNORECASE)
            for match in matches:
                if pattern == r'emailToken=(\d+)':
                    # Hanya dapat token, konstruksi link
                    token = match
                    return f"https://services.sheerid.com/verify/690415d58971e73ca187d8c9/?emailToken={token}"
                
                # Bersihkan link dari karakter HTML
                link = match.replace("&amp;", "&")
                link = link.replace("\\/", "/")
                link = link.replace("\r", "").replace("\n", "")
                
                # Pastikan link lengkap
                if link.startswith("http"):
                    # Perbaiki link jika perlu
                    if "emailToken=" in link and not link.startswith("https://services.sheerid.com"):
                        # Cari bagian setelah emailToken
                        token_part = link.split("emailToken=")[-1]
                        link = f"https://services.sheerid.com/verify/690415d58971e73ca187d8c9/?emailToken={token_part}"
                    
                    print(f"   [EMAIL TEMPORARY] Link diekstrak: {link[:80]}...")
                    return link
        
        # Coba cari link dengan regex yang lebih longgar
        loose_pattern = r'(https?://[^\s<>"]+sheerid[^\s<>"]+)'
        matches = re.findall(loose_pattern, email_content, re.IGNORECASE)
        for match in matches:
            link = match.replace("&amp;", "&")
            if "sheerid" in link.lower():
                print(f"   [EMAIL TEMPORARY] Ditemukan link SheerID: {link[:80]}...")
                return link
        
        # Cari token saja
        token_pattern = r'token[=:]?\s*(\d{6,})'
        token_matches = re.findall(token_pattern, email_content, re.IGNORECASE)
        if token_matches:
            token = token_matches[0]
            print(f"   [EMAIL TEMPORARY] Ditemukan token: {token}")
            return f"https://services.sheerid.com/verify/690415d58971e73ca187d8c9/?emailToken={token}"
        
        return None


class VeteransVerifier:
    """Veterans verification handler dengan email temporary otomatis"""
    
    def __init__(self, config, proxy: str = None, proxy_index: int = 0, use_random_domain=True):
        self.access_token = config.get("accessToken", "")
        self.program_id = config.get("programId", DEFAULT_PROGRAM_ID)
        
        # Format proxy
        self.proxies = format_proxy(proxy)
        self.proxy_str = proxy
        
        # Setup email client dengan API Guerrilla Mail
        self.email_client = TempEmailService(
            proxies=self.proxies,
            use_random_domain=use_random_domain
        )
        self.email_address = None
        
        self.proxy_index = proxy_index
        
        # Buat session
        self.session, self.using_cloudscraper = create_session_with_retry(
            proxies=self.proxies,
            use_cloudscraper=True
        )
        
        if self.using_cloudscraper:
            print(f"[INFO] Menggunakan cloudscraper dengan proxy #{proxy_index}")
        else:
            print(f"[INFO] Menggunakan requests dengan proxy #{proxy_index}")
        
        if proxy:
            masked_proxy = mask_proxy_url(proxy)
            print(f"[INFO] Proxy: {masked_proxy}")
            print(f"[INFO] Proxy diformat: {self._debug_proxy_format()}")
        
        print("[INFO] Berjalan dalam mode FULL AUTOMATION dengan API Guerrilla Mail")
        if use_random_domain:
            print(f"[INFO] Menggunakan domain acak dari {len(GUERRILLA_DOMAINS)} pilihan")
    
    def _debug_proxy_format(self):
        """Debug format proxy untuk verifikasi"""
        if not self.proxies:
            return "Tidak ada proxy"
        
        proxy_info = []
        for scheme, url in self.proxies.items():
            proxy_info.append(f"{scheme}: {mask_proxy_url(url)}")
        
        return " | ".join(proxy_info)
    
    def _get_headers(self, sheerid=False):
        base = {
            "sec-ch-ua": '"Chromium";v="131", "Google Chrome";v="131"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": USER_AGENT,
            "accept": "application/json",
            "content-type": "application/json",
            "accept-language": "en-US,en;q=0.9"
        }
        
        if sheerid:
            nr = generate_newrelic_headers()
            return {
                **base,
                "clientversion": "2.157.0",
                "clientname": "jslib",
                "newrelic": nr["newrelic"],
                "traceparent": nr["traceparent"],
                "tracestate": nr["tracestate"],
                "origin": "https://services.sheerid.com"
            }
        
        return {
            **base,
            "authorization": f"Bearer {self.access_token}",
            "origin": "https://chatgpt.com",
            "referer": "https://chatgpt.com/veterans-claim",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "oai-device-id": str(uuid.uuid4()),
            "oai-language": "en-US",
        }
    
    def create_verification(self):
        """Langkah 1: Buat verifikasi ID dari ChatGPT"""
        print("   -> Membuat permintaan verifikasi...")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Generate email temporary via API
                if not self.email_address:
                    self.email_address = self.email_client.generate_email()
                    print(f"   [INFO] Menggunakan email: {self.email_address}")
                
                resp = self.session.post(
                    f"{CHATGPT_API}/veterans/create_verification",
                    headers=self._get_headers(),
                    json={"program_id": self.program_id},
                    timeout=30
                )
                
                if resp.status_code == 200:
                    verification_id = resp.json().get("verification_id")
                    return verification_id
                elif resp.status_code == 403 and attempt < max_attempts - 1:
                    print(f"   [DEBUG] 403, menunggu sebelum mencoba lagi...")
                    time.sleep(5)
                    continue
                else:
                    resp.raise_for_status()
                    
            except requests.exceptions.HTTPError as e:
                if attempt < max_attempts - 1:
                    print(f"   [DEBUG] Percobaan {attempt+1} gagal: {e}")
                    time.sleep(5)
                    continue
                else:
                    if hasattr(e, 'response') and e.response.status_code == 403:
                        print("   [ERROR] 403 Forbidden!")
                    raise
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"   [DEBUG] Percobaan {attempt+1} gagal: {e}")
                    time.sleep(5)
                    continue
                else:
                    raise
    
    def submit_military_status(self, verification_id):
        """Langkah 2: Submit status sebagai VETERAN"""
        print("   -> Mengirimkan status militer (VETERAN)...")
        
        resp = self.session.post(
            f"{SHEERID_API}/verification/{verification_id}/step/collectMilitaryStatus",
            headers=self._get_headers(sheerid=True),
            json={"status": "VETERAN"},
            timeout=30,
            proxies=self.proxies if not self.using_cloudscraper else None
        )
        resp.raise_for_status()
    
    def submit_personal_info(self, verification_id, user_data):
        """Langkah 3: Submit informasi pribadi"""
        print("   -> Mengirimkan info pribadi...")
        
        fingerprint = generate_fingerprint()
        referer = f"https://services.sheerid.com/verify/{self.program_id}/?verificationId={verification_id}"
        
        payload = {
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"],
            "birthDate": user_data["birthDate"],
            "email": self.email_address,
            "phoneNumber": "",
            "organization": user_data["organization"],
            "dischargeDate": user_data["dischargeDate"],
            "deviceFingerprintHash": fingerprint,
            "locale": "en-US",
            "country": "US",
            "metadata": {
                "marketConsentValue": False,
                "refererUrl": referer,
                "verificationId": verification_id,
                "submissionOptIn": "By submitting the personal information above, I acknowledge..."
            }
        }
        
        headers = self._get_headers(sheerid=True)
        headers["referer"] = referer
        
        resp = self.session.post(
            f"{SHEERID_API}/verification/{verification_id}/step/collectInactiveMilitaryPersonalInfo",
            headers=headers,
            json=payload,
            timeout=30,
            proxies=self.proxies if not self.using_cloudscraper else None
        )
        
        response_text = resp.text
        response_lower = response_text.lower()
        
        # Pola error kritis
        critical_error_patterns = [
            ("verification limit exceeded", "Verification Limit Exceeded"),
            ("we're glad you're enthusiastic", "Rate limit exceeded"),
            ("already redeemed or attempted", "Already redeemed"),
            ("we are unable to verify you at this time", "Unable to verify"),
            ("unable to verify you", "Unable to verify"),
            ("not approved", "Not approved"),
            ("<span>not approved</span>", "Not approved"),
            ("please contact sheerid support", "Contact support required"),
            ("try again</span></a>", "System error"),
            ("error</h1>", "Generic error page"),
            ("sid-step-error", "Error page detected"),
            ("rejected", "Verification rejected"),
            ("denied", "Verification denied"),
            ("failed", "Verification failed"),
            ("invalid", "Invalid verification"),
            ("too many attempts", "Too many attempts"),
            ("rate limit", "Rate limit exceeded"),
            ("429", "HTTP 429 - Too Many Requests"),
        ]
        
        for pattern, error_name in critical_error_patterns:
            if pattern.lower() in response_lower:
                print(f"   [ERROR] {error_name} terdeteksi!")
                return {
                    "_critical_error": True,
                    "_error_type": error_name,
                    "_already_verified": True,
                    "currentStep": "error"
                }
        
        try:
            data = resp.json()
            error_ids = str(data.get("errorIds", [])).lower()
            
            critical_json_errors = [
                "verificationlimitexceeded", "limit", "exceeded", "redeem",
                "attempt", "429", "blocked", "suspended", "banned",
                "rejected", "denied", "not.approved", "not_approved",
                "notapproved", "invalid", "failure", "fail"
            ]
            
            for error_keyword in critical_json_errors:
                if error_keyword in error_ids:
                    print(f"   [ERROR] JSON menunjukkan error kritis: {error_ids}")
                    return {
                        "_critical_error": True,
                        "_error_type": f"JSON error: {error_ids}",
                        "_already_verified": True,
                        "currentStep": "error"
                    }
            
            return data
            
        except json.JSONDecodeError:
            return {
                "error": "Invalid response format",
                "_already_verified": True,
                "currentStep": "error"
            }
    
    def submit_email_token(self, verification_id, email_token):
        """Langkah 5: Submit email token"""
        print(f"   -> Mengirimkan email token: {email_token}...")
        
        resp = self.session.post(
            f"{SHEERID_API}/verification/{verification_id}/step/emailLoop",
            headers=self._get_headers(sheerid=True),
            json={
                "emailToken": email_token,
                "deviceFingerprintHash": generate_fingerprint()
            },
            timeout=30,
            proxies=self.proxies if not self.using_cloudscraper else None
        )
        return resp.json()
    
    def verify(self, user_data):
        """Main verification flow dengan pengecekan email otomatis"""
        try:
            # Langkah 1: Buat verifikasi
            verification_id = self.create_verification()
            print(f"   [OK] Verification ID: {verification_id}")
            
            # Langkah 2: Submit status militer
            self.submit_military_status(verification_id)
            print("   [OK] Status dikirim")
            
            # Langkah 3: Submit info pribadi
            result = self.submit_personal_info(verification_id, user_data)
            
            # Cek error kritis
            if result.get("_critical_error"):
                error_type = result.get("_error_type", "Critical error")
                return {
                    "success": False, 
                    "message": f"{error_type} - Program dihentikan", 
                    "stop_program": True
                }
            
            step = result.get("currentStep")
            print(f"   [OK] Info pribadi dikirim - Step: {step}")
            
            # Jika sudah verified DAN step adalah error, periksa apakah ini error kritis
            if result.get("_already_verified") and step == "error":
                error_msg = str(result.get("errorIds", [])).lower()
                critical_keywords = [
                    "limit", "exceed", "redeem", "attempt", "429", 
                    "unable", "block", "suspend", "ban",
                    "reject", "deny", "not.approved", "not_approved",
                    "notapproved", "invalid", "fail", "failure"
                ]
                if any(keyword in error_msg for keyword in critical_keywords):
                    return {
                        "success": False, 
                        "message": "Critical verification error - Program dihentikan", 
                        "stop_program": True
                    }
                else:
                    return {"success": False, "message": "Data sudah diverifikasi", "skip": True}
            
            if step == "success":
                return {"success": True, "message": "Verifikasi berhasil!"}
            
            if step == "docUpload":
                return {"success": False, "message": "Diperlukan upload dokumen"}
            
            if step == "error":
                # Cek lagi untuk error kritis di error message
                error_msg = str(result.get("errorIds", [])).lower()
                critical_keywords = [
                    "limit", "exceed", "redeem", "attempt", "429", 
                    "unable", "block", "suspend", "ban",
                    "reject", "deny", "not.approved", "not_approved",
                    "notapproved", "invalid", "fail", "failure"
                ]
                if any(keyword in error_msg for keyword in critical_keywords):
                    return {
                        "success": False, 
                        "message": "Critical verification error - Program dihentikan", 
                        "stop_program": True
                    }
                return {"success": False, "message": f"Error: {result.get('errorIds')}"}
            
            # Langkah 4: Jika perlu verifikasi email, lakukan otomatis via API
            if step == "emailLoop":
                print("   -> Menunggu email verifikasi (pengecekan otomatis via API)...")
                
                # Tunggu dan cek email via API
                link = self.email_client.check_email(max_attempts=25, delay=4)
                
                if not link:
                    return {"success": False, "message": "Email verifikasi tidak diterima"}
                
                # Ekstrak token dari link
                token_match = re.search(r"emailToken=(\d+)", link)
                if not token_match:
                    # Coba pattern lain
                    token_match = re.search(r"token[=:]?\s*(\d+)", link)
                    if not token_match:
                        # Cari angka 6 digit di link
                        token_match = re.search(r"(\d{6,})", link)
                        if not token_match:
                            return {"success": False, "message": "Tidak dapat mengekstrak emailToken dari link"}
                
                # Langkah 5: Submit token
                email_token = token_match.group(1)
                print(f"   -> Mengirimkan email token: {email_token}...")
                
                email_result = self.submit_email_token(verification_id, email_token)
                
                if email_result.get("currentStep") == "success":
                    return {"success": True, "message": "Verifikasi berhasil!"}
                else:
                    return {
                        "success": False, 
                        "message": f"Verifikasi email gagal: {email_result.get('errorIds')}"
                    }
            
            if step == "collectInactiveMilitaryPersonalInfo":
                if result.get("errorIds"):
                    return {"success": False, "message": f"Error: {result.get('errorIds')}"}
                return {"success": False, "message": "Terdapat di step info pribadi"}
            
            return {"success": False, "message": f"Step tidak diketahui: {step}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Veterans Verification Tool dengan Full Automation")
    parser.add_argument("--proxy", type=str, help="Gunakan proxy spesifik (ip:port atau user:pass@ip:port)")
    parser.add_argument("--no-dedup", action="store_true", help="Nonaktifkan pengecekan duplikasi")
    parser.add_argument("--continue-on-reject", action="store_true", help="Lanjutkan meskipun terjadi error 'Not approved'")
    parser.add_argument("--no-proxy", action="store_true", help="Jangan gunakan proxy meskipun proxy.txt ada")
    parser.add_argument("--test-api", action="store_true", help="Test API Guerrilla Mail saja")
    parser.add_argument("--delay", type=int, default=2, help="Delay antar percobaan dalam detik (default: 2)")
    parser.add_argument("--single-domain", action="store_true", help="Gunakan domain tunggal daripada domain acak")
    parser.add_argument("--list-domains", action="store_true", help="Tampilkan semua domain yang tersedia")
    parser.add_argument("--test-proxy", action="store_true", help="Test koneksi proxy saja")
    args = parser.parse_args()
    
    print()
    print("=" * 75)
    print("  Veterans Verification Tool - FULL AUTOMATION DENGAN DOMAIN ACAK")
    print("  ChatGPT Plus - US Veterans Verification")
    print("=" * 75)
    print()
    
    if args.list_domains:
        print("Domain Guerrilla Mail yang tersedia:")
        for i, domain in enumerate(GUERRILLA_DOMAINS, 1):
            print(f"  {i:2d}. @{domain}")
        print(f"\nTotal: {len(GUERRILLA_DOMAINS)} domain tersedia")
        return
    
    print("  FITUR:")
    print("  * Pembuatan email otomatis via API Guerrilla Mail")
    print("  * Pemilihan domain acak dari 13+ pilihan")
    print("  * Pengecekan inbox otomatis untuk link verifikasi")
    print("  * Ekstraksi dan pengiriman token otomatis")
    print("  * Proses verifikasi 100% otomatis tanpa intervensi manual")
    print("  * Dukungan untuk berbagai format proxy")
    print()
    
    # Test proxy jika diminta
    if args.test_proxy:
        print("[INFO] Menguji koneksi proxy...")
        if args.proxy:
            test_proxy = format_proxy(args.proxy)
            print(f"  Input: {args.proxy}")
            print(f"  Diformat: {test_proxy}")
            
            # Test koneksi
            try:
                session = requests.Session()
                session.proxies = test_proxy
                resp = session.get("https://httpbin.org/ip", timeout=10)
                if resp.status_code == 200:
                    print(f"  BERHASIL Proxy berfungsi! IP Anda: {resp.json().get('origin')}")
                else:
                    print(f"  GAGAL Uji proxy gagal: HTTP {resp.status_code}")
            except Exception as e:
                print(f"  GAGAL Error uji proxy: {e}")
        else:
            print("  Silakan tentukan proxy dengan opsi --proxy")
        return
    
    # Load config
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        print("[ERROR] config.json tidak ditemukan!")
        print()
        print("Buat config.json dengan konten minimal berikut:")
        print('{"accessToken": "YOUR_TOKEN_HERE", "programId": "690415d58971e73ca187d8c9"}')
        print()
        print("Untuk mendapatkan accessToken dari ChatGPT:")
        print("1. Login ke https://chatgpt.com")
        print("2. Buka DevTools (F12) -> Network tab")
        print("3. Kunjungi: https://chatgpt.com/api/auth/session")
        print("4. Copy nilai 'accessToken' dari response")
        return
    
    config = json.loads(config_path.read_text(encoding="utf-8"))
    
    if not config.get("accessToken"):
        print("[ERROR] accessToken tidak ada di config.json!")
        return
    
    # Test API jika diminta
    if args.test_api:
        print("[INFO] Menguji API Guerrilla Mail dengan domain acak...")
        # Format proxy jika ada
        proxies = format_proxy(args.proxy) if args.proxy else None
        temp_email = TempEmailService(proxies=proxies, use_random_domain=not args.single_domain)
        email = temp_email.generate_email()
        print(f"  Email yang dihasilkan: {email}")
        print("  Menguji pengecekan inbox...")
        # Coba check inbox sekali
        temp_email.check_email(max_attempts=3, delay=2)
        return
    
    # Load proxies dari file atau argumen
    proxies_list = []
    
    if args.proxy:
        # Gunakan proxy dari argumen
        proxies_list = [args.proxy]
        print(f"[INFO] Menggunakan proxy dari command line: {mask_proxy_url(args.proxy)}")
    elif not args.no_proxy:
        # Load dari file
        proxies_list = load_proxies(str(Path(__file__).parent / PROXY_FILE))
        if proxies_list:
            print(f"[INFO] Memuat {len(proxies_list)} proxy dari proxy.txt")
            # Tampilkan beberapa contoh
            sample_count = min(3, len(proxies_list))
            print(f"[INFO] Contoh proxy: {', '.join([mask_proxy_url(p) for p in proxies_list[:sample_count]])}")
    
    # Load data
    data_path = Path(__file__).parent / "data.txt"
    if not data_path.exists():
        print("[ERROR] data.txt tidak ditemukan!")
        print()
        print("Buat data.txt dengan format:")
        print("firstName|lastName|branch|birthDate|dischargeDate")
        print()
        print("Contoh baris:")
        print("John|Doe|Army|1980-01-01|2023-12-31")
        print("Jane|Smith|Navy|1985-05-15|2024-06-30")
        return
    
    lines = [l.strip() for l in data_path.read_text(encoding="utf-8").split("\n")
             if l.strip() and not l.startswith("#")]
    
    if not lines:
        print("[ERROR] data.txt kosong!")
        return
    
    print(f"[INFO] Memuat {len(lines)} record")
    print(f"[INFO] Delay antar percobaan: {args.delay} detik")
    if args.single_domain:
        print("[INFO] Menggunakan mode domain tunggal")
    else:
        print(f"[INFO] Menggunakan mode domain acak ({len(GUERRILLA_DOMAINS)} domain)")
    print()

    success = 0
    fail = 0
    skip = 0
    critical_error = False
    error_type = ""
    
    # Rotasi proxy
    current_proxy_index = 0
    
    for i, line in enumerate(lines):
        user_data = parse_data_line(line)
        if not user_data:
            print(f"[{i+1}/{len(lines)}] Format tidak valid, dilewati")
            continue
        
        name = f"{user_data['firstName']} {user_data['lastName']}"
        
        # Check deduplication
        if not args.no_dedup and is_data_used(user_data['firstName'], user_data['lastName'], user_data['birthDate']):
            print(f"[{i+1}/{len(lines)}] {name} - Sudah digunakan, dilewati")
            skip += 1
            continue
        
        print(f"[{i+1}/{len(lines)}] {name} ({user_data['branch']})")
        print("-" * 50)
        
        # Pilih proxy
        current_proxy = None
        if proxies_list:
            current_proxy = proxies_list[current_proxy_index % len(proxies_list)]
            current_proxy_index += 1
            
            if current_proxy_index >= len(proxies_list):
                current_proxy_index = 0
        
        # Buat verifier dengan email temporary API
        verifier = VeteransVerifier(
            config, 
            proxy=current_proxy, 
            proxy_index=current_proxy_index,
            use_random_domain=not args.single_domain
        )
        
        result = verifier.verify(user_data)
        
        # Handle critical errors
        if result.get("stop_program"):
            error_message = result.get("message", "")
            
            if "Not approved" in error_message and args.continue_on_reject:
                print(f"   [PERINGATAN] {error_message}")
                print("   Melanjutkan ke record berikutnya karena flag --continue-on-reject")
                fail += 1
                print()
                time.sleep(args.delay)
                continue
            
            print(f"   [KRITIS] {error_message}")
            
            if "403" in error_message and proxies_list and len(proxies_list) > 1:
                print("   [INFO] Error 403, mencoba proxy berikutnya...")
                fail += 1
                print()
                time.sleep(args.delay)
                continue
            
            print("=" * 55)
            if "Not approved" in error_message:
                print("  Program dihentikan - Verifikasi TIDAK DISETUJUI")
            else:
                print("  Program dihentikan - ERROR KRITIS")
            print("=" * 55)
            
            critical_error = True
            error_type = result.get('message', 'Error tidak diketahui')
            break
        
        # Mark as used jika tidak skip
        if not args.no_dedup and not result.get("skip"):
            mark_data_used(user_data['firstName'], user_data['lastName'], user_data['birthDate'])
        
        if result.get("success"):
            success += 1
            print(f"   [BERHASIL] Verifikasi selesai secara otomatis!")
            print()
            print("-" * 55)
            print("  BERHASIL Verifikasi berhasil! Menghentikan...")
            print("-" * 55)
            break
        elif result.get("skip"):
            skip += 1
            print(f"   [LEWATI] {result['message']}\n")
        else:
            fail += 1
            print(f"   [GAGAL] {result.get('message') or result.get('error')}\n")
        
        # Delay sebelum record berikutnya
        if i < len(lines) - 1:
            print(f"   [INFO] Menunggu {args.delay} detik sebelum record berikutnya...")
            time.sleep(args.delay)
    
    print()
    print("=" * 75)
    print("  RINGKASAN VERIFIKASI")
    print("=" * 75)
    print(f"  BERHASIL (terverifikasi otomatis): {success}")
    print(f"  LEWATI (duplikat): {skip}")
    print(f"  GAGAL: {fail}")
    print(f"  TOTAL diproses: {success + skip + fail}/{len(lines)}")
    print()
    
    if success > 0:
        print("  SUKSES! Verifikasi selesai sepenuhnya otomatis!")
        print("    Tidak diperlukan langkah manual apapun.")
    
    if critical_error:
        print(f"  KRITIS Program dihentikan karena: {error_type}")
        print("    Pertimbangkan untuk mengganti proxy atau menunggu sebelum mencoba lagi.")
    
    print("=" * 75)


if __name__ == "__main__":
    main()