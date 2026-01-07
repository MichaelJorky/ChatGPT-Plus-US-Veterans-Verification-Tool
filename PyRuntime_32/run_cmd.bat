@echo off
title Script Runner - Pilih Mode

:top
cls
echo ==========================================
echo         PILIH MODE EKSEKUSI SCRIPT
echo ==========================================
echo [1] Mode Normal (Langsung Jalan)
echo [2] Mode Delay (Tunggu 5 Detik)
echo [3] Tampilkan Semua Opsi/Argumen
echo [4] Mode Proxy (Gunakan proxy tertentu)
echo [5] Mode Tanpa Proxy
echo [6] Test Koneksi Proxy
echo [7] Test API Email
echo [8] Keluar 
echo ==========================================
echo.

set /p pilihan="Masukkan pilihan Anda (1-8): "

if "%pilihan%"=="1" goto mode_normal
if "%pilihan%"=="2" goto mode_delay
if "%pilihan%"=="3" goto show_options
if "%pilihan%"=="4" goto mode_proxy
if "%pilihan%"=="5" goto mode_no_proxy
if "%pilihan%"=="6" goto test_proxy
if "%pilihan%"=="7" goto test_api
if "%pilihan%"=="8" exit

echo.
echo Pilihan tidak valid, silakan coba lagi.
pause
goto top

:mode_normal
cls
echo ==========================================
echo         MODE NORMAL
echo ==========================================
echo Menjalankan script dengan pengaturan default...
echo.
:: Cek apakah file ada sebelum dijalankan
if exist script.py (
    python script.py
) else (
    echo ERROR: File script.py tidak ditemukan di folder ini!
)
pause
goto top

:mode_delay
cls
echo ==========================================
echo         MODE DELAY
echo ==========================================
echo Menjalankan script dengan delay 5 detik antar percobaan...
echo.
if exist script.py (
    python script.py --delay 5
) else (
    echo ERROR: File script.py tidak ditemukan di folder ini!
)
pause
goto top

:show_options
cls
echo ==========================================
echo    SEMUA OPSI/ARGUMEN YANG TERSEDIA
echo ==========================================
echo.
echo Berikut adalah semua argumen yang bisa digunakan:
echo.
echo [1] --proxy           : Gunakan proxy spesifik
echo      Contoh: --proxy 127.0.0.1:8080
echo      Contoh: --proxy user:pass@192.168.1.1:8080
echo.
echo [2] --no-dedup        : Nonaktifkan pengecekan duplikasi
echo      (Lewati pengecekan data yang sudah digunakan)
echo.
echo [3] --continue-on-reject : Lanjutkan meskipun error 'Not approved'
echo      (Berguna untuk testing)
echo.
echo [4] --no-proxy        : Jangan gunakan proxy sama sekali
echo      (Abaikan file proxy.txt)
echo.
echo [5] --test-api        : Test API Guerrilla Mail saja
echo      (Tidak menjalankan verifikasi, hanya test email)
echo.
echo [6] --delay           : Delay antar percobaan (detik)
echo      Contoh: --delay 10  (untuk delay 10 detik)
echo      Default: 2 detik
echo.
echo [7] --single-domain   : Gunakan domain tunggal
echo      (Tidak menggunakan domain acak, hanya domain default)
echo.
echo [8] --list-domains    : Tampilkan semua domain yang tersedia
echo      (Hanya tampilkan list, tidak menjalankan verifikasi)
echo.
echo [9] --test-proxy      : Test koneksi proxy saja
echo      (Test apakah proxy berfungsi)
echo.
echo ==========================================
echo CARA PENGGUNAAN DI COMMAND LINE:
echo.
echo Contoh 1: python script.py --proxy 127.0.0.1:8080 --delay 5
echo Contoh 2: python script.py --no-dedup --single-domain
echo Contoh 3: python script.py --test-api --no-proxy
echo ==========================================
echo.
pause
goto top

:mode_proxy
cls
echo ==========================================
echo         MODE PROXY SPESIFIK
echo ==========================================
echo.
echo Format proxy yang didukung:
echo 1. ip:port           (Contoh: 127.0.0.1:8080)
echo 2. user:pass@ip:port (Contoh: user:pass@192.168.1.1:8080)
echo.
set /p proxy_input="Masukkan proxy (atau kosongkan untuk batal): "

if "%proxy_input%"=="" (
    echo Dibatalkan...
    pause
    goto top
)

echo.
echo Menjalankan dengan proxy: %proxy_input%
echo.
if exist script.py (
    python script.py --proxy "%proxy_input%"
) else (
    echo ERROR: File script.py tidak ditemukan di folder ini!
)
pause
goto top

:mode_no_proxy
cls
echo ==========================================
echo         MODE TANPA PROXY
echo ==========================================
echo Menjalankan script TANPA menggunakan proxy sama sekali...
echo (File proxy.txt akan diabaikan)
echo.
if exist script.py (
    python script.py --no-proxy
) else (
    echo ERROR: File script.py tidak ditemukan di folder ini!
)
pause
goto top

:test_proxy
cls
echo ==========================================
echo         TEST KONEKSI PROXY
echo ==========================================
echo.
echo Test apakah proxy berfungsi dengan benar...
echo.
set /p test_proxy="Masukkan proxy untuk test (kosongkan untuk test tanpa proxy): "

if "%test_proxy%"=="" (
    echo.
    echo Test tanpa proxy...
    echo.
    if exist script.py (
        python script.py --test-proxy
    ) else (
        echo ERROR: File script.py tidak ditemukan di folder ini!
    )
) else (
    echo.
    echo Test dengan proxy: %test_proxy%
    echo.
    if exist script.py (
        python script.py --test-proxy --proxy "%test_proxy%"
    ) else (
        echo ERROR: File script.py tidak ditemukan di folder ini!
    )
)
pause
goto top

:test_api
cls
echo ==========================================
echo         TEST API EMAIL
echo ==========================================
echo.
echo Test fungsi API Guerrilla Mail...
echo.
set /p test_proxy_api="Masukkan proxy (kosongkan untuk tanpa proxy): "

if "%test_proxy_api%"=="" (
    echo.
    echo Test API tanpa proxy...
    echo.
    if exist script.py (
        python script.py --test-api
    ) else (
        echo ERROR: File script.py tidak ditemukan di folder ini!
    )
) else (
    echo.
    echo Test API dengan proxy: %test_proxy_api%
    echo.
    if exist script.py (
        python script.py --test-api --proxy "%test_proxy_api%"
    ) else (
        echo ERROR: File script.py tidak ditemukan di folder ini!
    )
)
pause
goto top