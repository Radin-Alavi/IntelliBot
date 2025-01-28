import speech_recognition as sr
r = sr.Recognizer()

def record_text():
    try:
        with sr.Microphone() as source2:
            print("در حال گوش دادن...")
            r.adjust_for_ambient_noise(source2, duration=0.05)
            audio2 = r.listen(source2)
            # تنظیم زبان به فارسی
            Mytext = r.recognize_google(audio2, language="fa-IR")
            return Mytext     
    except sr.RequestError:
        print("مشکلی در ارتباط با سرویس تشخیص گفتار وجود دارد.")
        
    except sr.UnknownValueError:
        print("متن قابل تشخیص نیست.")
        
    return ""

def output_text(text):
    if text:  
        with open("output.txt", "a", encoding="utf-8") as f:
            f.write(text + "\n")
    return

while True:
    text = record_text()
    output_text(text)
    if text:
        print(f"متن تشخیص داده‌شده: {text}")
