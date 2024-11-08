import speech_recognition as sr

r = sr.Recognizer()

def record_text():
    try:
        with sr.Microphone() as source2:
            r.adjust_for_ambient_noise(source2, duration=0.05)  # کاهش مدت زمان تنظیم نویز
            audio2 = r.listen(source2)
            Mytext = r.recognize_google(audio2)
            return Mytext     
    except sr.RequestError:
        print("مشکلی در ارتباط با سرویس تشخیص گفتار پیش آمده.")
        
    except sr.UnknownValueError:
        print("نامشخص")
        
    return ""

def output_text(text):
    if text:  # فقط زمانی که متن دریافت شده، در فایل بنویسد
        with open("output.txt", "a") as f:
            f.write(text + "\n")
    return

while True:
    text = record_text()
    output_text(text)
    if text:
        print(text)
