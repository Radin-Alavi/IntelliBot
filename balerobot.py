from bale import Bot, CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import chess
import chess.engine
import os
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from reportlab.pdfgen import canvas
from pathlib import Path
import arabic_reshaper
from bidi.algorithm import get_display
import re

STOCKFISH_PATH = r"stockfish-windows-x86-64-avx2.exe"
PIECE_SYMBOLS = {
    'p': '♙', 'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔',
    'P': '♟', 'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚'
}

client = Bot(token="1073138097:49XMJIzGSAXXffU4p5hFbiDQB6NLp7RCxqdDpPeW")
user_input_state = {}

def pdf_to_docx(pdf_path, docx_path):
    """تبدیل PDF به DOCX"""
    reader = PdfReader(pdf_path)
    document = Document()

    for page in reader.pages:
        text = page.extract_text()
        text = reshape_text_if_persian(text)
        document.add_paragraph(text)

    document.save(docx_path)
    print(f"تبدیل شد {pdf_path} به {docx_path}")

def docx_to_pdf(docx_path, pdf_path):
    """تبدیل DOCX به PDF"""
    document = Document(docx_path)
    pdf = canvas.Canvas(pdf_path)

    y = 800 
    for i, paragraph in enumerate(document.paragraphs):
        text = reshape_text_if_persian(paragraph.text)
        pdf.drawString(100, y - 15 * i, text)

    pdf.save()
    print(f"تبدیل شد {docx_path} به {pdf_path}")

def is_persian(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

def reshape_text_if_persian(text):
    if is_persian(text):
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    return text

def display_board(board):
    board_str = str(board).split("\n")
    board_display = "♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜\n"
    for idx, line in enumerate(board_str):
        line_with_symbols = ''.join(PIECE_SYMBOLS.get(char, char) for char in line)
        board_display += f"{8 - idx} {line_with_symbols} {8 - idx}\n"
    board_display += "♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖\n"
    return board_display

async def play_chess(chat_id, color):
    if not os.path.exists(STOCKFISH_PATH):
        await client.send_message(chat_id=chat_id, text="❌ Stockfish پیدا نشد! لطفاً مسیر را بررسی کنید.")
        return

    board = chess.Board()
    user_input_state[chat_id] = {"board": board, "color": color}

    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            if color == "black":
                result = engine.play(board, chess.engine.Limit(time=1.0))
                board.push(result.move)
                await client.send_message(chat_id=chat_id, text=f"♟️ **Stockfish بازی را شروع کرد!**\n{display_board(board)}\n♔ **نوبت شماست! حرکت خود را بفرستید.**")
            else:
                await client.send_message(chat_id=chat_id, text=f"♔ **شما سفید هستید! بازی را شروع کنید.**\n{display_board(board)}")

            user_input_state[chat_id]["awaiting_move"] = True
    except PermissionError as e:
        await client.send_message(chat_id=chat_id, text="❌ خطای مجوز: لطفاً اجازه‌های اجرای Stockfish را بررسی کنید.")

@client.event
async def on_message(message: Message):
    chat_id = message.chat.id

    if message.document:
        file = message.document
        file_path = f'./{file.file_name}'

        await file.download(file_path)
        
        if file.file_name.endswith('.pdf'):
            docx_path = f"{file_path.replace('.pdf', '.docx')}"
            pdf_to_docx(file_path, docx_path)
            await client.send_document(chat_id=chat_id, document=docx_path)
            os.remove(file_path)
            os.remove(docx_path)
        
        elif file.file_name.endswith('.docx'):
            pdf_path = f"{file_path.replace('.docx', '.pdf')}"
            docx_to_pdf(file_path, pdf_path)
            await client.send_document(chat_id=chat_id, document=pdf_path)
            os.remove(file_path)
            os.remove(pdf_path)

        else:
            await client.send_message(chat_id=chat_id, text="❌ فقط فایل‌های PDF یا DOCX قابل تبدیل هستند.")

    elif chat_id in user_input_state and user_input_state[chat_id].get("awaiting_move"):
        board = user_input_state[chat_id]["board"]
        try:
            move = board.parse_san(message.content)
            if move in board.legal_moves:
                board.push(move)
            else:
                await client.send_message(chat_id=chat_id, text="❌ حرکت غیرمجاز است. دوباره امتحان کنید.")
                return
        except ValueError:
            await client.send_message(chat_id=chat_id, text="❌ فرمت حرکت اشتباه است. لطفاً دوباره تلاش کنید.")
            return

        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            if board.is_game_over():
                await client.send_message(chat_id=chat_id, text=f"🎉 بازی تمام شد! نتیجه: {board.result()}")
                del user_input_state[chat_id]
                return

            result = engine.play(board, chess.engine.Limit(time=1.0))
            board.push(result.move)

            if board.is_game_over():
                await client.send_message(chat_id=chat_id, text=f"🎉 بازی تمام شد! نتیجه: {board.result()}")
                del user_input_state[chat_id]
            else:
                await client.send_message(chat_id=chat_id, text=f"♟️ **Stockfish حرکت کرد!**\n{display_board(board)}\n♔ **نوبت شماست! حرکت خود را بفرستید.**")


@client.event
async def on_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if callback.data == "chess":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="⚪ سفید", callback_data="chess_white"))
        keyboard.add(InlineKeyboardButton(text="⚫ سیاه", callback_data="chess_black"))
        await client.send_message(chat_id=chat_id, text="🎲 **با چه رنگی می‌خواهید بازی کنید؟**", components=keyboard)
    elif callback.data == "chess_white":
        await play_chess(chat_id, "white")
    elif callback.data == "chess_black":
        await play_chess(chat_id, "black")

client.run()
