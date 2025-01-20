from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from reportlab.pdfgen import canvas
from pathlib import Path

def pdf_to_docx(pdf_path, docx_path):
    """تبدیل PDF به DOCX"""
    reader = PdfReader(pdf_path)
    document = Document()

    for page in reader.pages:
        text = page.extract_text()
        document.add_paragraph(text)

    document.save(docx_path)
    print(f"تبدیل شد{pdf_path} به {docx_path}")

def docx_to_pdf(docx_path, pdf_path):
    """تبدیل DOCX به PDF"""
    document = Document(docx_path)
    pdf = canvas.Canvas(pdf_path)

    for i, paragraph in enumerate(document.paragraphs):
        pdf.drawString(100, 800 - 15 * i, paragraph.text)

    pdf.save()
    print(f"تبدیلل شد {docx_path} بخ {pdf_path}")

def main():
    print("یک گزینه را انتخاب کنید")
    print("1. تبدیل PDF به DOCX")
    print("2. تبدیل DOCX به PDF")
    choice = input(" انتخاب کنید (1/2) ").strip()

    if choice == "1":
        pdf_path = input("مسیر فایل PDF را وارد کنید ").strip()
        docx_path = input("مسیر فایل DOCX را وارد کنید  ").strip()
        if Path(pdf_path).exists():
            pdf_to_docx(pdf_path, docx_path)
        else:
            print("این فایل PDF وجود ندارد")

    elif choice == "2":
        docx_path = input("مسیر فایل DOCX را وارد کنید  ").strip()
        pdf_path = input("مسیر فایل PDF را وارد کنید  ").strip()
        if Path(docx_path).exists():
            docx_to_pdf(docx_path, pdf_path)
        else:
            print("این فایل DOCX وجود ندارد")

    else:
        print("از بین 1 و 2 انتخاب کنید")

if __name__ == "__main__":
    main()