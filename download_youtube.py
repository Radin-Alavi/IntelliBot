from pytube import YouTube
def download_video(video_url):
    try:
        yt = YouTube(video_url)
        stream = yt.streams.get_highest_resolution()
        print(f"دانلود ویدیو: {yt.title}")
        stream.download()
        print("دانلود با موفقیت انجام شد!")
    except Exception as e:
        print(f"خطا در دانلود: {e}")
if __name__ == "__main__":
    video_link = input("لطفا لینک ویدیو یوتیوب را وارد کنید: ")
    download_video(video_link)
