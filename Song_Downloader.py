import yt_dlp

def download_song(song_name):
    ydl_opts = {
        'noplaylist': True,              
        'age_limit': 18,                 
        'ignoreerrors': True,             
        'geo_bypass': True,               
        'extract_flat': 'in_playlist'     
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([f'ytsearch:{song_name}'])
        except Exception as e:
            print(f"خطا در دانلود: {e}")

song = "just the two of us"
download_song(song)
