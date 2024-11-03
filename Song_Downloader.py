import yt_dlp

def download_song(song_name):
    ydl_opts = {
        'noplaylist': True,               # غیرفعال کردن دانلود پلی‌لیست
        'age_limit': 18,                  # تنظیم محدودیت سنی
        'ignoreerrors': True,             # ادامه‌ی دانلود در صورت بروز خطا
        'geo_bypass': True,               # بای‌پس محدودیت جغرافیایی
        'extract_flat': 'in_playlist'     # بهبود استخراج لینک
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([f'ytsearch:{song_name}'])
        except Exception as e:
            print(f"خطا در دانلود: {e}")

song = "just the two of us"
download_song(song)
