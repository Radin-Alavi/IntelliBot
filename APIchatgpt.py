import requests

# گرفتن ورودی از کاربر
user_input = input("لطفاً سوال خود را وارد کنید: ")

# آدرس API
url = "https://open.wiki-api.ir/apis-1/ChatGPT?q="

# ارسال ورودی به API و دریافت پاسخ
response = requests.get(url + user_input)

# بررسی وضعیت پاسخ و چاپ نتیجه
if response.status_code == 200:
    # استخراج داده‌های JSON از پاسخ
    data = response.json()

    # نمایش فقط بخش "results" از پاسخ
    if "results" in data:
        print({data['results']})
    else:
        print("نتیجه‌ای از API دریافت نشد.")
else:
    print(f"خطا در دریافت پاسخ از API: {response.status_code}")
