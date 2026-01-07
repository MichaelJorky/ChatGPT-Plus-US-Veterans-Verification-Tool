# ChatGPT Plus - US Veterans Verification Tool

## 📋 Deskripsi
Alat otomatis untuk verifikasi veteran militer AS yang berguna untuk mendapatkan akses ChatGPT Plus secara gratis melalui program OpenAI untuk veteran. Tool ini menangani seluruh proses verifikasi secara otomatis, termasuk pembuatan email sementara, pengecekan inbox, dan verifikasi token.

## ⚡ Fitur Utama
- ✅ **Proses otomatis lengkap** - dari awal hingga selesai
- ✅ **Email temporary otomatis** - menggunakan API Guerrilla Mail
- ✅ **Random domain selection** - 13+ domain untuk menghindari blokir
- ✅ **Proxy support** - mendukung berbagai format proxy
- ✅ **Anti-duplikasi** - otomatis menandai data yang sudah digunakan
- ✅ **Multi-branch support** - semua cabang militer AS didukung
- ✅ **No manual intervention** - 100% hands-free

## 🚀 Instalasi Cepat

### Struktur Folder:
```
chatgpt-veterans-verifier/
├── PyRuntime_32/                 # Python runtime untuk Windows 32-bit
│   ├── script.py                # Script utama Python
│   ├── run_cmd.bat              # Menu GUI untuk Windows
│   ├── config.json              # Konfigurasi token akses
│   ├── data.txt                 # Data veteran untuk verifikasi
│   ├── proxy.txt                # Daftar proxy (opsional)
│   ├── used.txt                 # Data yang sudah digunakan (auto-generated)
│   └── requirements.txt         # Dependencies (sudah include dalam runtime)
│
├── PyRuntime_64/                 # Python runtime untuk Windows 64-bit
│   ├── script.py                # Script utama Python
│   ├── run_cmd.bat              # Menu GUI untuk Windows
│   ├── config.json              # Konfigurasi token akses
│   ├── data.txt                 # Data veteran untuk verifikasi
│   ├── proxy.txt                # Daftar proxy (opsional)
│   ├── used.txt                 # Data yang sudah digunakan (auto-generated)
│   └── requirements.txt         # Dependencies (sudah include dalam runtime)
│
├── LICENSE                       # Lisensi MIT
└── README.md                     # Dokumentasi ini
```

### Untuk Windows (Direkomendasikan):
1. **Tentukan tipe sistem Anda:**
   - Windows 32-bit → Gunakan folder `PyRuntime_32`
   - Windows 64-bit → Gunakan folder `PyRuntime_64`

2. **Masuk ke folder runtime yang sesuai:**
   ```cmd
   cd PyRuntime_64  # Untuk Windows 64-bit
   ```

3. **Siapkan file konfigurasi:**
   - Edit `config.json` dan ganti token akses Anda
   - Edit `data.txt` dengan data yang akan diverifikasi

4. **Jalankan `run_cmd.bat`** dan pilih mode yang diinginkan

### Untuk Sistem Lain (Linux/Termux):
```bash
# Pilih salah satu folder runtime
cd PyRuntime_64  # atau PyRuntime_32

# Jalankan langsung
python script.py --delay 5

# Atau jalankan dengan proxy
python script.py --proxy 127.0.0.1:8080 --delay 10
```

## ⚙️ Konfigurasi

### 1. config.json (Lokasi: di dalam folder runtime)
```json
{
    "accessToken": "TOKEN AKSES_CHATGPT_ANDA",
    "programId": "690415d58971e73ca187d8c9"
}
```

### 2. Cara Mendapatkan Access Token:
1. Login ke https://chatgpt.com
2. Setelah login, buka: https://chatgpt.com/api/auth/session
3. Copy nilai `accessToken`
4. Tempel ke file `config.json` di dalam folder runtime yang Anda pilih

### 3. data.txt Format (Lokasi: di dalam folder runtime):
```
NamaDepan|NamaBelakang|Cabang|TanggalLahir|TanggalKeluar
```

**Contoh:**
```
JOHN|SMITH|Army|1990-05-15|2023-06-01
DAVID|JOHNSON|Marine Corps|1988-12-20|2022-03-15
MICHAEL|WILLIAMS|Navy|1992-08-10|2024-01-10
```

**Cabang yang Didukung:**
- Army, Navy, Air Force, Marine Corps, Coast Guard, Space Force
- Army National Guard, Army Reserve, Air National Guard
- Air Force Reserve, Navy Reserve, Marine Corps Reserve, Coast Guard Reserve

**Catatan Penting:**
- Tanggal keluar harus dalam **12 bulan terakhir** untuk memenuhi syarat
- Tahun lahir **disarankan tidak di bawah 1969**
- **Tanggal keluar rumah sakit** harus valid dan realistis

## 🎮 Cara Penggunaan

### Windows (Menggunakan GUI):
1. **Buka folder runtime yang sesuai:**
   - Untuk 64-bit: `PyRuntime_64`
   - Untuk 32-bit: `PyRuntime_32`

2. **Double-click `run_cmd.bat`**
3. **Pilih mode yang diinginkan:**
   ```
   [1] Mode Normal (Langsung Jalan)
   [2] Mode Delay (Tunggu 5 Detik)
   [3] Tampilkan Semua Opsi/Argumen
   [4] Mode Proxy (Gunakan proxy tertentu)
   [5] Mode Tanpa Proxy
   [6] Test Koneksi Proxy
   [7] Test API Email
   [8] Keluar
   ```

### Linux/Termux (Command Line):
```bash
# Masuk ke folder runtime
cd PyRuntime_64  # atau PyRuntime_32

# Mode normal
python script.py

# Dengan delay 10 detik
python script.py --delay 10

# Dengan proxy spesifik
python script.py --proxy 127.0.0.1:8080 --delay 5

# Tanpa pengecekan duplikasi
python script.py --no-dedup

# Test API saja
python script.py --test-api

# Tampilkan semua domain yang tersedia
python script.py --list-domains
```

## 🖥️ Contoh Output
```
==========================================
         MODE NORMAL
==========================================
[INFO] Loaded 5 records
[INFO] Using random domain mode (13 domains)

[1/5] JOHN SMITH (Army)
--------------------------------------------------
   -> Creating verification request...
   [EMAIL TEMPORARY] Generated via API: john123@sharklasers.com
   [OK] Verification ID: abc123def456
   -> Submitting military status (VETERAN)...
   [OK] Status submitted
   -> Submitting personal info...
   [OK] Personal info submitted - Step: emailLoop
   -> Waiting for verification email (auto-checking via API)...
   [EMAIL TEMPORARY] Polling inbox for: john123@sharklasers.com
   [EMAIL TEMPORARY] Found verification email (ID: 12345)
   [EMAIL TEMPORARY] Link extracted after 12s!
   -> Submitting email token: 654321...
   [SUCCESS] Verification completed automatically!

   -------------------------------------------------
     BERHASIL Verifikasi berhasil! Menghentikan...
   -------------------------------------------------

==========================================
  RINGKASAN VERIFIKASI
==========================================
  BERHASIL (terverifikasi otomatis): 1
  LEWATI (duplikat): 0
  GAGAL: 0
  TOTAL diproses: 1/5
```

## ⚠️ Troubleshooting & Error Handling

| Error Message | Penyebab | Solusi |
|---------------|----------|---------|
| **403 Forbidden** | Token akses telah kedaluwarsa | Dapatkan token baru dari ChatGPT |
| **401 Unauthorized** | Token tidak valid | Periksa format token, dapatkan token baru |
| **Not approved** | Data tidak ada dalam basis data ATAU IP diblokir | Gunakan proxy, coba data yang berbeda |
| **Document upload required** | Verifikasi otomatis gagal | Data tidak ada dalam basis data DoD/DEERS |
| **Data already verified** | Veteran sudah menggunakannya | Coba data yang berbeda |
| **Already used, skipping** | Data di used.txt | Gunakan flag `--no-dedup` |
| **Error Discharge Date** | Tanggal keluar lebih lama | Gunakan tanggal keluar rumah sakit terbaru |
| **Python not found** | Runtime tidak sesuai | Gunakan folder runtime yang benar untuk sistem Anda |

## 🔒 Penggunaan Proxy (Opsional)

### proxy.txt Format (Lokasi: di dalam folder runtime):
```
# Format 1: ip:port
123.45.67.89:8080
98.76.54.32:3128

# Format 2: user:pass@ip:port
user:password@192.168.1.1:8080
admin:pass123@10.0.0.1:8888
```

**Penting:**
- ❌ **TIDAK direkomendasikan** menggunakan proxy untuk API backend ChatGPT
- ✅ **Rekomendasi**: Gunakan VPN atau tanpa proxy sama sekali
- ⚠️ **Satu IP address** disarankan maksimal 3 akun (lebih dari itu risiko banned tinggi)

## 📋 Persyaratan & Rekomendasi

### Persyaratan Sistem:
- **Windows 32-bit**: Gunakan folder `PyRuntime_32`
- **Windows 64-bit**: Gunakan folder `PyRuntime_64`
- **Linux/Termux**: Python 3.7+ dengan dependencies terinstall
- **Internet**: Koneksi stabil untuk API calls
- **Storage**: Minimal 50MB free space

### Rekomendasi Keamanan:
1. **Gunakan VPN** daripada proxy untuk kestabilan
2. **Limit 3 akun per IP** untuk menghindari banned
3. **Test dengan 1 data dulu** sebelum batch processing
4. **Backup config.json** jika sudah berhasil
5. **Pastikan folder runtime sesuai** dengan sistem Anda

## ⚖️ Disclaimer & Etika

### PERINGATAN:
1. **Tool ini untuk tujuan pendidikan** dan mempermudah proses verifikasi
2. **TIDAK menyertakan data veterans asli** - user harus mencari data sendiri
3. **Tanggung jawab pengguna** untuk penggunaan yang etis dan legal
4. **Jangan gunakan data veterans hidup** tanpa izin
5. **Resiko akun banned** jika melanggar terms of service ChatGPT

### Legalitas:
- Tool ini hanya mengotomatisasi proses yang tersedia publik
- Tidak melakukan hacking, cracking, atau aktivitas ilegal
- Menggunakan API resmi yang tersedia
- Compliance dengan rate limiting yang diterapkan

## 🤝 Kontribusi & Support

### Kontribusi:
1. Fork repository
2. Buat feature branch
3. Commit changes
4. Push ke branch
5. Buat Pull Request

### Support Developer:
Jika Anda merasa alat ini bermanfaat, pertimbangkan untuk memberikan dukungan:
- **Buy me a coffee**: https://saweria.co/teknoxpert
- **Report issues**: GitHub Issues
- **Feature requests**: GitHub Discussions

## 📄 Lisensi
Proyek ini dilisensikan di bawah **MIT License** - lihat file [LICENSE](LICENSE) untuk detail lengkap.

## 🔗 Links & Referensi
- [ChatGPT Veterans Program](https://chatgpt.com/veterans-claim)
- [OpenAI Documentation](https://platform.openai.com/docs)
- [SheerID Verification Service](https://www.sheerid.com/)
- [Guerrilla Mail API](https://www.guerrillamail.com/GuerrillaMailAPI.html)
- [US Veterans - Wikipedia](https://en.wikipedia.org/wiki/Special:Search?go=Go&search=US+Veterans&ns0=1)

---

**Catatan Akhir**: 
1. **Pastikan menggunakan folder runtime yang benar** sesuai dengan sistem operasi Anda
2. Semua file konfigurasi harus **di dalam folder runtime** yang digunakan
3. Tool ini dibuat untuk mempermudah proses verifikasi yang sudah tersedia
4. Pengguna bertanggung jawab penuh atas penggunaan yang sesuai dengan hukum dan etika yang berlaku
5. Selalu hormati privasi dan hak veterans

**Happy Coding!** 🚀
