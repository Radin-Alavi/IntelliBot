from bale import Bot, CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, MenuKeyboardMarkup, MenuKeyboardButton, InputFile
import chess
import chess.engine
import os
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
import arabic_reshaper
import re
import requests
import shutil
import random
from googletrans import Translator as GoogleTranslator
from deep_translator import GoogleTranslator
import ssl
import aiohttp
import certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())

async def make_request():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://tapi.bale.ai', ssl=ssl_context) as response:
            print(await response.text())

import asyncio
asyncio.run(make_request())


language_map = {
    "انگلیسی": "en",
    "فارسی": "fa",
    "فرانسوی": "fr",
    "آلمانی": "de",
    "ترکی": "tr",
    "عربی": "ar",
    "چینی": "zh-CN",
    "ژاپنی": "ja",
    "روسی": "ru",
    "اسپانیایی": "es",
    "ایتالیایی": "it"
}


#  مسیر به موتور Stockfish
STOCKFISH_PATH = r"C:\Users\Lenovo\Documents\Pajoheshi\stockfish-windows-x86-64-avx2 copy.exe"

#  راه‌اندازی ربات با توکن شما
client = Bot(token="1073138097:49XMJIzGSAXXffU4p5hFbiDQB6NLp7RCxqdDpPeW")
user_input_state = {}

def docx_to_pdf(docx_path, pdf_path):
    """ تبدیل DOCX به PDF"""
    document = Document(docx_path)
    pdf = canvas.Canvas(pdf_path)

    y = 800
    for i, paragraph in enumerate(document.paragraphs):
        text = reshape_text_if_persian(paragraph.text)
        pdf.drawString(100, y - 15 * i, text)

    pdf.save()
    print(f" تبدیل {docx_path} به {pdf_path}")

def is_persian(text):
    """ بررسی اینکه آیا متن شامل کاراکترهای فارسی است"""
    return bool(re.search(r'[\u0600-\u06FF]', text))

def reshape_text_if_persian(text):
    """ بازشکل‌دهی متن اگر به فارسی است"""
    if is_persian(text):
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    return text

def display_board(board):
    """ دریافت و ذخیره تصویر صفحه شطرنج"""
    import urllib.parse

    fen = board.fen()
    fen_encoded = urllib.parse.quote(fen, safe='')
    url = f"https://lichess1.org/export/fen.gif?fen={fen_encoded}&color=white"

    print(" Generated URL:", url)

    file_name = f"chess_board_{hash(fen)}.jpg"
    file_path = os.path.join("chess_boards", file_name)

    if not os.path.exists("chess_boards"):
        os.makedirs("chess_boards")

    if not os.path.exists(file_path):
        res = requests.get(url, stream=True)
        if res.status_code == 200:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
            print("✅ تصویر با موفقیت ذخیره شد:", file_path)
        else:
            print(f"❌ خطا در دریافت تصویر: {res.status_code}, {res.text}")
            return None

    return file_path

async def play_chess(chat_id, color):
    """♟️ بازی شطرنج با کاربر"""
    if not os.path.exists(STOCKFISH_PATH):
        await client.send_message(chat_id=chat_id, text="❌ موتور Stockfish یافت نشد! لطفاً مسیر را بررسی کنید.")
        return

    board = chess.Board()
    user_input_state[chat_id] = {"board": board, "color": color}

    file_path = display_board(board)

    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            if color == "black":
                result = engine.play(board, chess.engine.Limit(time=1.0))
                board.push(result.move)

                file_path = display_board(board)

                await client.send_message(chat_id=chat_id, text="♟️ **Stockfish بازی را شروع کرد!**")
                with open(file_path, "rb") as test:
                    file = InputFile(test.read())
                    await client.send_photo(chat_id, file)
                    os.remove(file_path)
                await client.send_message(chat_id=chat_id, text="♔ **نوبت شما! حرکت خود را ارسال کنید.**")
            else:
                await client.send_message(chat_id=chat_id, text="♔ **شما سفید هستید! بازی را شروع کنید.**")
                with open(file_path, "rb") as test:
                    file = InputFile(test.read())
                    await client.send_photo(chat_id, file)
                os.remove(file_path)
            user_input_state[chat_id]["awaiting_move"] = True

    except PermissionError:
        await client.send_message(chat_id=chat_id, text="❌ خطای دسترسی: لطفاً مجوزهای اجرای Stockfish را بررسی کنید.")
    except Exception as e:
        await client.send_message(chat_id=chat_id, text=f"❌ خطای غیرمنتظره: {e}")

@client.event
async def on_message(message: Message):
    chat_id = message.chat.id

    if not hasattr(message, "content") or message.content is None:
        await client.send_message(chat_id, text="❌ پیام نامعتبر است.")
        return

    if chat_id in user_input_state:
        state = user_input_state[chat_id]
        if chat_id in user_input_state:
            state = user_input_state[chat_id]

        if state.get("awaiting_move"):
            board = state.get("board")
            if not board:
                await client.send_message(chat_id, text="❌ خطا در وضعیت بازی.")
                return
            try:
                move = board.parse_san(message.content.strip())
                if board.is_legal(move):
                    board.push(move)
                else:
                    await client.send_message(chat_id, text="❌ حرکت نامعتبر. دوباره امتحان کنید.")
                    return
            except ValueError:
                await client.send_message(chat_id, text="❌ فرمت حرکت اشتباهه. مثلاً: `e4` یا `Nf3`")
                return

            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                if board.is_game_over():
                    await client.send_message(chat_id, text=f"🏁 بازی تمام شد! نتیجه: {board.result()}")
                    del user_input_state[chat_id]
                    return

                result = engine.play(board, chess.engine.Limit(time=1.0))
                board.push(result.move)

            if board.is_game_over():
                await client.send_message(chat_id, text=f"🏁 بازی تمام شد! نتیجه: {board.result()}")
                del user_input_state[chat_id]
            else:
                image_path = display_board(board)
                await client.send_message(chat_id, text="♟️ **Stockfish حرکت کرد!**")
                with open(image_path, "rb") as f:
                    await client.send_photo(chat_id, InputFile(f.read()))
                os.remove(image_path)
                await client.send_message(chat_id, text="♔ **نوبت شماست!**")
            return

    if message.document:
        file = message.document

        if not file.file_name:
            await client.send_message(chat_id, text="❌ فایل نامعتبر است.")
            return

        file_path = f'./{file.file_name}'
        try:
            await file.download(file_path)
        except Exception as e:
            await client.send_message(chat_id, text=f"❌ خطا در دانلود فایل: {str(e)}")
            return

        await process_document(chat_id, file_path, file.file_name)

    if message.content == "/start":
        await handle_start_command(message)

    elif message.content == "ChatGPT":
        user_input_state[chat_id] = {"awaiting": "chatgpt"}
        await client.send_message(chat_id=chat_id, text="سلام. چه کمکی می‌تونم بهتون بکنم؟")
    elif chat_id in user_input_state and user_input_state[chat_id].get("awaiting") == "chatgpt":
        try:
            user_input = message.content
            url = "https://open.wiki-api.ir/apis-1/ChatGPT?q="
            response = requests.get(url + user_input)

            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    await client.send_message(chat_id, text=f"پاسخ از ChatGPT: {data['results']} ")
                else:
                    await client.send_message(chat_id, text="❌ نتیجه‌ای از API دریافت نشد.")
            else:
                await client.send_message(chat_id, text=f"❌ خطا در دریافت پاسخ از API: {response.status_code}")
        except Exception as e:
            await client.send_message(chat_id, text=f"❌ خطای غیرمنتظره در ChatGPT: {e}")
        del user_input_state[chat_id]

    # در on_message:

    if chat_id in user_input_state:
        await_state = user_input_state[chat_id].get("awaiting")

        if await_state == "origin":
            lang_input = message.content.strip()
            if lang_input not in language_map:
                await client.send_message(chat_id, text="❌ زبان مبدأ ناشناخته است. مثلاً: فارسی، انگلیسی، فرانسوی")
                return
            user_input_state[chat_id]["origin_lang"] = language_map[lang_input]
            user_input_state[chat_id]["awaiting"] = "destination"
            await client.send_message(chat_id, text="✅ حالا زبان مقصد را وارد کنید:")
            return

        elif await_state == "destination":
            lang_input = message.content.strip()
            if lang_input not in language_map:
                await client.send_message(chat_id, text="❌ زبان مقصد ناشناخته است. مثلاً: فارسی، انگلیسی، فرانسوی")
                return
            user_input_state[chat_id]["destination_lang"] = language_map[lang_input]
            user_input_state[chat_id]["awaiting"] = "text_to_translate"
            await client.send_message(chat_id, text="📝 متنی که می‌خواهید ترجمه شود را وارد کنید:")
            return

        elif await_state == "text_to_translate":
            origin = user_input_state[chat_id]["origin_lang"]
            dest = user_input_state[chat_id]["destination_lang"]
            text = message.content
            try:
                translated = GoogleTranslator(source=origin, target=dest).translate(text)
                await client.send_message(chat_id, text=f"✅ ترجمه:\n\n{translated}")
            except Exception as e:
                await client.send_message(chat_id, text=f"❌ خطا در ترجمه: {str(e)}")
            finally:
                del user_input_state[chat_id]
            return


    elif message.content == "/keyboard":
        first_name = message.from_user.first_name if message.from_user and message.from_user.first_name else "کاربر"
        await client.send_message(chat_id, text=f"*سلام {first_name}, به IntelliBot خوش آمدید*",
                                    components=MenuKeyboardMarkup()
                                    .add(MenuKeyboardButton(' ترجمه'))
                                    .add(MenuKeyboardButton(' pdf docx')))

    else:
        await client.send_message(chat_id, text=f"شما گفتید: {message.content}")

    print(" پیام دریافت شد")

async def process_document(chat_id, file_path, file_name):
    """ دریافت فایل، پردازش و ارسال فایل تغییر یافته"""

    output_path = file_path.replace(".pdf", ".docx") if file_name.endswith(".pdf") else file_path.replace(".docx", ".pdf")

    if file_name.endswith(".pdf"):
        pdf_to_docx(file_path, output_path)
    elif file_name.endswith(".docx"):
        docx_to_pdf(file_path, output_path)
    else:
        await client.send_message(chat_id=chat_id, text="❌ فرمت فایل پشتیبانی نمی‌شود! فقط PDF و DOCX مجاز است.")
        return

    await client.send_document(chat_id=chat_id, document=InputFile(output_path))

    os.remove(file_path)
    os.remove(output_path)

@client.event
async def on_ready():
    print(client.user, "آماده است! 🟢")

@client.event
async def on_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if callback.data == "chess":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="⚪ سفید", callback_data="chess_white"))
        keyboard.add(InlineKeyboardButton(text="⚫ سیاه", callback_data="chess_black"))
        await client.send_message(chat_id=chat_id, text=" **با چه رنگی می‌خواهید بازی کنید؟**", components=keyboard)
    elif callback.data == "chess_white":
        await play_chess(chat_id, "white")
    elif callback.data == "chess_black":
        await play_chess(chat_id, "black")
    elif callback.data == "translate_text":
        user_input_state[chat_id] = {"awaiting": "origin"}
        await client.send_message(chat_id=chat_id, text=" لطفاً زبان مبدأ را وارد کنید:")
    elif callback.data == "chatgpt":
        user_input_state[chat_id] = {"awaiting": "chatgpt"}
        await client.send_message(chat_id=chat_id, text="سلام. چه کمکی می‌تونم بهتون بکنم؟")

async def handle_start_command(message: Message):
    """مدیریت دستور /start."""
    chat_id = message.chat.id
    reply_markup = InlineKeyboardMarkup()
    reply_markup.add(InlineKeyboardButton(text=" تبدیل PDF به DOCX", callback_data="pdf_to_docx"), row=1)
    reply_markup.add(InlineKeyboardButton(text=" ترجمه متن", callback_data="translate_text"), row=2)
    reply_markup.add(InlineKeyboardButton(text="♟️ بازی شطرنج", callback_data="chess"), row=3)
    reply_markup.add(InlineKeyboardButton(text=" دانلود ویدئو یوتیوب", callback_data="download_youtube"), row=4)
    reply_markup.add(InlineKeyboardButton(text=" تبدیل صدا به متن", callback_data="audio_to_text"), row=5)
    reply_markup.add(InlineKeyboardButton(text=" ChatGPT", callback_data="chatgpt"), row=6)

    first_name = message.from_user.first_name if message.from_user and message.from_user.first_name else "کاربر"
    await client.send_message(chat_id, text=f"*سلام {first_name}, به IntelliBot خوش آمدید*", components=reply_markup)

client.run()