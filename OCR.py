import easyocr
import cv2
import pytesseract
import os

# تعیین مسیر نصب Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# تابع پیش‌پردازش برای بهبود تصویر
def preprocess_image(image_path):
    # خواندن تصویر
    image = cv2.imread(image_path)
    
    # تبدیل به مقیاس خاکستری
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # بهبود کنتراست تصویر
    enhanced_image = cv2.equalizeHist(gray)
    
    # ذخیره تصویر بهبود یافته
    enhanced_image_path = "enhanced_image.jpg"
    cv2.imwrite(enhanced_image_path, enhanced_image)
    return enhanced_image_path

# مسیر فایل تصویر (از مسیر مطلق استفاده کنید)
image_path = r"C:\Users\Lenovo\Downloads\-9223372036854775808_-210000.jpg"
enhanced_image_path = preprocess_image(image_path)

# استفاده از EasyOCR با تنظیمات بهینه
reader = easyocr.Reader(['en'], gpu=False)
result_easyocr = reader.readtext(enhanced_image_path, decoder='beamsearch')

# چاپ نتایج EasyOCR
print("نتایج تشخیص EasyOCR:")
for (bbox, text, prob) in result_easyocr:
    print(text)

# استفاده از Tesseract به عنوان جایگزین
print("\nنتایج تشخیص Tesseract:")
try:
    text_tesseract = pytesseract.image_to_string(cv2.imread(enhanced_image_path))
    print(text_tesseract)
except pytesseract.pytesseract.TesseractNotFoundError:
    print("Tesseract نصب نشده است یا در PATH سیستم یافت نمی‌شود.")
except PermissionError:
    print("خطای دسترسی: لطفاً مطمئن شوید که پایتون و Tesseract دسترسی لازم را دارند.")
except Exception as e:
    print(f"خطای غیرمنتظره: {e}")
