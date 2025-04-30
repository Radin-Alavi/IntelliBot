from bale import Bot, CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
import chess
import chess.engine
import os
from PyPDF2 import PdfReader
from pathlib import Path
import arabic_reshaper
from docx import Document
from bidi.algorithm import get_display
import re
import requests
import shutil
from deep_translator import GoogleTranslator
import json
import urllib.parse
from typing import Dict, Any
import yt_dlp
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import aiohttp
import asyncio

STOCKFISH_PATH = r"stockfish-windows-x86-64-avx2.exe"
ELO_LEVELS = {
    "2500+": {"skill_level": 20, "time_limit": 2.0},
    "2500-2000": {"skill_level": 18, "time_limit": 1.5},
    "2000-1500": {"skill_level": 15, "time_limit": 1.0},
    "1500-1000": {"skill_level": 10, "time_limit": 0.7},
    "1000-500": {"skill_level": 5, "time_limit": 0.4},
    "500-": {"skill_level": 1, "time_limit": 0.2}
}

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

client = Bot(token="1073138097:49XMJIzGSAXXffU4p5hFbiDQB6NLp7RCxqdDpPeW")
user_input_state = {}

async def get_tehran_air_quality(url="https://airnow.tehran.ir"):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.text()
                soup = BeautifulSoup(data, "html5lib")

                result = {
                    "success": True,
                    "24h_AQI": None,
                    "now_AQI": None,
                    "status": "ok"
                }

                aqi_24h = soup.find("span", {"id": "ContentPlaceHolder1_lblAqi24h"})
                aqi_now = soup.find("span", {"id": "ContentPlaceHolder1_lblAqi3h"})

                if aqi_24h:
                    result["24h_AQI"] = aqi_24h.get_text(strip=True)
                if aqi_now:
                    result["now_AQI"] = aqi_now.get_text(strip=True)

                return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "24h_AQI": None,
            "now_AQI": None
        }


def is_persian(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

def reshape_text_if_persian(text):
    if is_persian(text):
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    return text

def pdf_to_docx(pdf_path, docx_path):
    reader = PdfReader(pdf_path)
    document = Document()

    for page in reader.pages:
        text = page.extract_text()
        text = reshape_text_if_persian(text)
        document.add_paragraph(text)

    document.save(docx_path)
    print(f"تبدیل شد {pdf_path} به {docx_path}")


def display_board(board):
    """تولید تصویر صفحه شطرنج"""
    fen = board.fen()
    fen_encoded = urllib.parse.quote(fen, safe='')
    url = f"https://lichess1.org/export/fen.gif?fen={fen_encoded}&color=white"

    file_name = f"chess_board_{hash(fen)}.jpg"
    file_path = os.path.join("chess_boards", file_name)

    if not os.path.exists("chess_boards"):
        os.makedirs("chess_boards")

    if not os.path.exists(file_path):
        res = requests.get(url, stream=True)
        if res.status_code == 200:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
        else:
            return None

    return file_path

async def download_youtube_video(url: str, chat_id: int):
    """دانلود ویدیو از یوتیوب"""
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            duration = info.get('duration', 0)

            if duration > 720:
                await client.send_message(
                    chat_id,
                    "❌ ویدیوهای طولانی‌تر از 12 دقیقه پشتیبانی نمی‌شوند."
                )
                return

            await client.send_message(
                chat_id,
                f"⏳ در حال دانلود ویدیو: {title}\n"
                f"⏱️ مدت زمان: {duration//60}:{duration%60:02d}"
            )

            ydl.download([url])

            file_path = ydl.prepare_filename(info)
            file_size = os.path.getsize(file_path) / (1024 * 1024)

            if file_size > 500:
                await client.send_message(
                    chat_id,
                    "❌ حجم ویدیو بیش از حد مجاز است (حداکثر 500MB)."
                )
                os.remove(file_path)
                return

            with open(file_path, 'rb') as f:
                video_data = f.read()
                await client.send_video(
                    chat_id=chat_id,
                    video=InputFile(video_data),
                    caption="ویدیو دانلود شد"
                )

            os.remove(file_path)

    except Exception as e:
        await client.send_message(
            chat_id,
            f"❌ خطا در دانلود ویدیو: {str(e)}"
        )
async def play_chess(chat_id: int, color: str, elo_level: str):
    """شروع بازی شطرنج با سطح مشخص"""
    if not os.path.exists(STOCKFISH_PATH):
        await client.send_message(chat_id, "❌ موتور Stockfish یافت نشد!")
        return

    level_settings = ELO_LEVELS.get(elo_level, ELO_LEVELS["1500-1000"])
    board = chess.Board()

    level_names = {
        "2500+": "حرفه‌ای (2500+)",
        "2500-2000": "پیشرفته (2000-2500)",
        "2000-1500": "متوسط (1500-2000)",
        "1500-1000": "مبتدی+ (1000-1500)",
        "1000-500": "مبتدی (500-1000)",
        "500-": "تازه‌کار (زیر 500)"
    }

    user_input_state[chat_id] = {
        "board": board,
        "color": color,
        "elo_level": elo_level,
        "awaiting_move": True,
        "engine_settings": level_settings
    }

    file_path = display_board(board)
    if not file_path:
        await client.send_message(chat_id, "❌ خطا در ایجاد صفحه شطرنج")
        return

    if color == "black":
        await make_engine_move(chat_id, board, level_settings)
    else:
        with open(file_path, "rb") as f:
            await client.send_photo(chat_id, InputFile(f.read()))
        os.remove(file_path)
        await client.send_message(
            chat_id,
            f"♟️ شروع بازی - سطح {level_names[elo_level]}\n"
            f"♔ شما سفید هستید! لطفاً حرکت خود را وارد کنید\n"
            f"مثال: e4, Nf3, Qxf7"
        )

async def make_engine_move(chat_id: int, board: chess.Board, settings: Dict[str, Any]):
    """انجام حرکت توسط موتور شطرنج"""
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            engine.configure({"Skill Level": settings["skill_level"]})

            result = engine.play(
                board,
                chess.engine.Limit(time=settings["time_limit"])
            )

            if result.move:
                board.push(result.move)
                file_path = display_board(board)

                if file_path:
                    with open(file_path, "rb") as f:
                        await client.send_photo(chat_id, InputFile(f.read()))
                    os.remove(file_path)

                if board.is_game_over():
                    await handle_game_over(chat_id, board)
                else:
                    level_names = {
                        20: "حرفه‌ای", 18: "پیشرفته", 15: "متوسط",
                        10: "مبتدی+", 5: "مبتدی", 1: "تازه‌کار"
                    }
                    await client.send_message(
                        chat_id,
                        f"♟️ Stockfish (سطح {level_names[settings['skill_level']]}) حرکت کرد!\n"
                        f"♔ نوبت شما! حرکت خود را ارسال کنید"
                    )
            else:
                await client.send_message(chat_id, "❌ موتور شطرنج نتوانست حرکتی انجام دهد")

    except Exception as e:
        await client.send_message(chat_id, f"❌ خطا در موتور شطرنج: {str(e)}")
        del user_input_state[chat_id]

async def handle_game_over(chat_id: int, board: chess.Board):
    """پردازش پایان بازی"""
    result = board.result()
    if result == "1-0":
        message = "🏁 بازی تمام شد! شما برنده شدید! 🎉"
    elif result == "0-1":
        message = "🏁 بازی تمام شد! Stockfish برنده شد! 🤖"
    else:
        message = "🏁 بازی تمام شد! نتیجه مساوی بود! ⚖️"

    await client.send_message(chat_id, message)
    del user_input_state[chat_id]

async def process_document(chat_id, file_path, file_name):
    """دریافت فایل، پردازش و ارسال فایل تغییر یافته"""
    try:
        if not file_name.lower().endswith(".pdf"):
            raise ValueError("فقط فایل‌های PDF پشتیبانی می‌شوند")

        file_size = os.path.getsize(file_path) / (1024 * 1024)
        if file_size > 20:
            raise ValueError("حجم فایل نباید بیشتر از 20MB باشد")

        output_path = file_path.replace(".pdf", ".docx")

        await client.send_message(
            chat_id=chat_id,
            text="⏳ در حال تبدیل فایل PDF به DOCX... لطفاً صبر کنید"
        )

        try:
            pdf_to_docx(file_path, output_path)
        except Exception as e:
            print(e)

        with open(output_path, 'rb') as f:
            await client.send_document(
                chat_id=chat_id,
                document=InputFile(f.read(), file_name=os.path.basename(output_path))
            )

        os.remove(file_path)
        os.remove(output_path)

    except Exception as e:
        error_msg = f"❌ خطا در پردازش فایل: {str(e)}"
        if "PDF" in str(e):
            error_msg = "❌ فایل PDF معتبر نیست یا آسیب دیده است"

        await client.send_message(
            chat_id=chat_id,
            text=error_msg
        )

        for path in [file_path, file_path.replace(".pdf", ".docx")]:
            if os.path.exists(path):os.remove(path)

@client.event
async def on_message(message: Message):
    chat_id = message.chat.id

    with open("اسامی اشخاص ربات.txt", "a+", encoding="utf-8") as f:
        f.seek(0)
        ids = f.read().splitlines()
        if str(chat_id) not in ids:
            f.write(f"{chat_id}\n")

    if not message or (not message.text and not message.document):
        await message.reply("❌ پیام نامعتبر است.")
        return

    if message.content == "/stop":
        if chat_id in user_input_state:
            del user_input_state[chat_id]
            await client.send_message(
                chat_id,
                "✅ تمام عملیات‌های در حال انجام متوقف شدند.\n"
                "شما می‌توانید دوباره از منوی اصلی شروع کنید."
            )
        else:
            await client.send_message(
                chat_id,
                "⚠️ هیچ عملیاتی در حال انجام نیست که نیاز به توقف داشته باشد."
            )
        return

    if chat_id in user_input_state and user_input_state[chat_id].get("awaiting_move"):
        board = user_input_state[chat_id].get("board")
        settings = user_input_state[chat_id].get("engine_settings")

        try:
            move = board.parse_san(message.content.strip())
            if board.is_legal(move):
                board.push(move)

                if board.is_game_over():
                    await handle_game_over(chat_id, board)
                else:
                    await make_engine_move(chat_id, board, settings)
            else:
                await client.send_message(
                    chat_id,
                    "❌ حرکت نامعتبر! لطفاً حرکت صحیحی وارد کنید.\n"
                    "مثال‌های صحیح: e4, Nf3, Qxf7"
                )

        except ValueError:
            await client.send_message(
                chat_id,
                "❌ فرمت حرکت اشتباه است!\n"
                "لطفاً حرکت را به صورت استاندارد شطرنج وارد کنید.\n"
                "مثال‌های صحیح: e4, Nf3, Qxf7"
            )
        return

    if message.text and ("youtube.com" in message.text or "youtu.be" in message.text):
        await download_youtube_video(message.text, chat_id)
        return

    if message.document:
        doc = message.document
        if doc.file_name and doc.file_name.endswith('.pdf'):
            try:
                file_content = await client.get_file(doc.file_id)
                file_path = f"./{doc.file_name}"
                with open(file_path, "wb") as f:
                    f.write(file_content)
                await process_document(message.chat.id, file_path, doc.file_name)
            except Exception as e:
                await message.reply(
                    f"❌ خطا در پردازش فایل: {e}\n"
                    "لطفاً فایل PDF معتبری ارسال کنید."
                )
        else:
            await message.reply(
                "❌ لطفاً فقط فایل PDF ارسال کنید.\n"
                "فرمت‌های دیگر پشتیبانی نمی‌شوند."
            )
        return  

    if message.content == "/start":
        await handle_start_command(message)
    elif message.content.lower() == "chatgpt":
        user_input_state[chat_id] = {"awaiting": "chatgpt"}
        await client.send_message(
            chat_id=chat_id,
            text="🤖 حالت ChatGPT فعال شد!\n"
            "لطفاً سوال یا متن خود را ارسال کنید:"
        )
    elif chat_id in user_input_state and user_input_state[chat_id].get("awaiting") == "chatgpt":
        user_input = message.content
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer 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",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "meta-llama/llama-4-maverick:free",
                    "messages": [{"role": "user", "content": user_input}],
                })
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                await client.send_message(
                    chat_id,
                    text=f"🤖 پاسخ ChatGPT:\n\n{content}"
                )
            else:
                await client.send_message(
                    chat_id,
                    text=f"❌ خطا در دریافت پاسخ: {response.status_code}\n"
                )

        except Exception as e:
            await client.send_message(
                chat_id,
                text=f"❌ خطای غیرمنتظره: {e}\n"
                "لطفاً دوباره امتحان کنید."
            )
        finally:
            del user_input_state[chat_id]
        return

    if chat_id in user_input_state and user_input_state[chat_id].get("awaiting") == "humanizeai":
        text = message.content.strip()
        try:
            api_url = "https://api.humanizeai.pro/v1/humanize"
            api_key = "sk_o391poseytq84nt71t9g"

            payload = {"text": text, "language": "fa"}
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                humanized_text = result.get('humanizedText', "متن پردازش شده یافت نشد.")
                await client.send_message(
                    chat_id,
                    text=f"✍️ متن پردازش شده:\n\n{humanized_text}\n\n"
                    "✅ متن شما با موفقیت بازنویسی شد."
                )
            else:
                await client.send_message(
                    chat_id,
                    text=f"❌ خطا در بازنویسی متن: {response.status_code}\n"
                    "لطفاً دوباره امتحان کنید."
                )

        except Exception as e:
            await client.send_message(
                chat_id,
                text=f"❌ خطای غیرمنتظره: {e}\n"
                "سرویس در حال حاضر در دسترس نیست."
            )
        finally:
            del user_input_state[chat_id]
        return

    if chat_id in user_input_state:
        await_state = user_input_state[chat_id].get("awaiting")

        if await_state == "origin":
            lang_input = message.content.strip()
            if lang_input not in language_map:
                await client.send_message(
                    chat_id,
                    text="❌ زبان مبدأ ناشناخته است!\n"
                    "لطفاً یکی از زبان‌های زیر را انتخاب کنید:\n"
                    "فارسی, انگلیسی, فرانسوی, آلمانی, ترکی, عربی, چینی, ژاپنی, روسی, اسپانیایی, ایتالیایی"
                )
                return
            user_input_state[chat_id]["origin_lang"] = language_map[lang_input]
            user_input_state[chat_id]["awaiting"] = "destination"
            await client.send_message(
                chat_id,
                text=f"✅ زبان مبدأ: {lang_input}\n"
                "لطفاً زبان مقصد را انتخاب کنید:"
            )
            return

        elif await_state == "destination":
            lang_input = message.content.strip()
            if lang_input not in language_map:
                await client.send_message(
                    chat_id,
                    text="❌ زبان مقصد ناشناخته است!\n"
                    "لطفاً یکی از زبان‌های زیر را انتخاب کنید:\n"
                    "فارسی, انگلیسی, فرانسوی, آلمانی, ترکی, عربی, چینی, ژاپنی, روسی, اسپانیایی, ایتالیایی"
                )
                return
            user_input_state[chat_id]["destination_lang"] = language_map[lang_input]
            user_input_state[chat_id]["awaiting"] = "text_to_translate"
            await client.send_message(
                chat_id,
                text=f"✅ ترجمه از {user_input_state[chat_id]['origin_lang']} به {user_input_state[chat_id]['destination_lang']}\n"
                "لطفاً متنی که می‌خواهید ترجمه شود را وارد کنید:"
            )
            return

        elif await_state == "text_to_translate":
            origin = user_input_state[chat_id]["origin_lang"]
            dest = user_input_state[chat_id]["destination_lang"]
            text = message.content
            try:
                translated = GoogleTranslator(source=origin, target=dest).translate(text)
                await client.send_message(
                    chat_id,
                    text=f"🌐 ترجمه:\n\n{translated}\n\n"
                    f"✅ متن از {origin} به {dest} ترجمه شد."
                )
            except Exception as e:
                await client.send_message(
                    chat_id,
                    text=f"❌ خطا در ترجمه: {str(e)}\n"
                    "لطفاً دوباره امتحان کنید."
                )
            finally:
                del user_input_state[chat_id]
            return

@client.event
async def on_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id

    if callback.data == "chess":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(" رادین (2500+)", callback_data="chess_level_2500+"), row=1)
        keyboard.add(InlineKeyboardButton("سطح پیشرفته (2000-2500)", callback_data="chess_level_2500-2000"), row=2)
        keyboard.add(InlineKeyboardButton("سطح متوسط (1500-2000)", callback_data="chess_level_2000-1500"), row=3)
        keyboard.add(InlineKeyboardButton("سطح مبتدی+ (1000-1500)", callback_data="chess_level_1500-1000"), row=4)
        keyboard.add(InlineKeyboardButton("سطح مبتدی (500-1000)", callback_data="chess_level_1000-500"), row=5)
        keyboard.add(InlineKeyboardButton("سطح تازه‌کار (زیر 500)", callback_data="chess_level_500-"), row=6)

        await client.send_message(
            chat_id,
            "♟️ لطفاً سطح مهارت خود در شطرنج را انتخاب کنید:",
            components=keyboard
        )

    elif callback.data.startswith("chess_level_"):
        elo_level = callback.data.replace("chess_level_", "")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⚪ سفید (شما شروع می‌کنید)", callback_data=f"chess_color_white_{elo_level}"))
        keyboard.add(InlineKeyboardButton("⚫ سیاه (کامپیوتر شروع می‌کند)", callback_data=f"chess_color_black_{elo_level}"))

        level_names = {
            "2500+": "حرفه‌ای (2500+)",
            "2500-2000": "پیشرفته (2000-2500)",
            "2000-1500": "متوسط (1500-2000)",
            "1500-1000": "مبتدی+ (1000-1500)",
            "1000-500": "مبتدی (500-1000)",
            "500-": "تازه‌کار (زیر 500)"
        }

        await client.send_message(
            chat_id,
            f"♟️ سطح انتخاب شده: {level_names[elo_level]}\n"
            "با چه رنگی می‌خواهید بازی کنید?",
            components=keyboard
        )

    elif callback.data.startswith("chess_color_"):
        parts = callback.data.split("_")
        color = parts[2]
        elo_level = "_".join(parts[3:])

        level_names = {
            "2500+": "حرفه‌ای",
            "2500-2000": "پیشرفته",
            "2000-1500": "متوسط",
            "1500-1000": "مبتدی+",
            "1000-500": "مبتدی",
            "500-": "تازه‌کار"
        }

        await client.send_message(
            chat_id,
            f"♟️ شروع بازی شطرنج\n"
            f"• سطح: {level_names[elo_level]}\n"
            f"• رنگ شما: {'سفید ⚪' if color == 'white' else 'سیاه ⚫'}\n\n"
            f"در حال آماده‌سازی بازی..."
        )
        await play_chess(chat_id, color, elo_level)

    elif callback.data == "translate_text":
        user_input_state[chat_id] = {"awaiting": "origin"}
        await client.send_message(
            chat_id=chat_id,
            text="🌐 لطفاً زبان مبدأ را انتخاب کنید:\n"
            "فارسی, انگلیسی, فرانسوی, آلمانی, ترکی, عربی, چینی, ژاپنی, روسی, اسپانیایی, ایتالیایی"
        )

    elif callback.data == "chatgpt":
        user_input_state[chat_id] = {"awaiting": "chatgpt"}
        await client.send_message(
            chat_id=chat_id,
            text="🤖 حالت ChatGPT فعال شد!\n"
            "لطفاً سوال یا متن خود را ارسال کنید:"
        )

    elif callback.data == "pollution_tehran":
        try:
            air_quality = await get_tehran_air_quality()

            if air_quality["success"]:
                message = (
                    f"🏙️ **وضعیت کیفیت هوای تهران**\n\n"
                    f"🔢 شاخص آلودگی هوا در 24 ساعت گذشته: **{air_quality['24h_AQI'] or 'نامعلوم'}**\n"
                    f"🔢 شاخص آلودگی هوا در حال حاضر: **{air_quality['now_AQI'] or 'نامعلوم'}**\n\n"
                    f"⚠️ توجه: اطلاعات ممکن است با تاخیر به روز رسانی شوند"
                )

                await client.send_message(chat_id=chat_id, text=message)
            else:
                await client.send_message(
                    chat_id=chat_id,
                    text=f"❌ خطا در دریافت اطلاعات کیفیت هوا:\n{air_quality.get('error', 'خطای نامشخص')}\n\n"
                    "لطفاً بعداً تلاش کنید."
                )
        except Exception as e:
            await client.send_message(
                chat_id=chat_id,
                text=f"❌ خطای سیستمی: {str(e)}\n"
                "لطفاً بعداً تلاش کنید."
            )

    elif callback.data == "humanioutube eai":
        user_input_state[chat_id] = {"awaiting": "humanizeai"}
        await client.send_message(
            chat_id=chat_id,
            text="✍️ لطفاً متنی که می‌خواهید پردازش شود را وارد کنید:\n"
            "(این سرویس متن شما را به زبان طبیعی و انسانی تبدیل می‌کند)"
        )

    elif callback.data == "pdf_to_docx":
        user_input_state[chat_id] = {"awaiting": "waiting_pdf"}
        await client.send_message(
            chat_id,
            "📎 لطفاً فایل PDF خود را برای تبدیل به DOCX ارسال کنید:\n"
            "• حداکثر حجم فایل: 20MB\n"
            "• پس از تبدیل، فایل Word برای شما ارسال خواهد شد"
        )

    elif callback.data == "youtube_downloader":
        user_input_state[chat_id] = {"awaiting": "youtube_url"}
        await client.send_message(
            chat_id,
            "🎬 لطفاً لینک ویدیوی یوتیوب را ارسال کنید:\n"
            "• حداکثر مدت ویدیو: 10 دقیقه\n"
            "• حداکثر حجم: 50MB\n"
            "• پس از دانلود، فایل برای شما ارسال خواهد شد"
        )

async def handle_start_command(message: Message):
    """مدیریت دستور /start."""
    chat_id = message.chat.id
    reply_markup = InlineKeyboardMarkup()
    reply_markup.add(InlineKeyboardButton(text="🔀 تبدیل PDF به DOCX", callback_data="pdf_to_docx"), row=1)
    reply_markup.add(InlineKeyboardButton(text="🌐 ترجمه متن", callback_data="translate_text"), row=2)
    reply_markup.add(InlineKeyboardButton(text="♟️ بازی شطرنج", callback_data="chess"), row=3)
    reply_markup.add(InlineKeyboardButton(text="🤖 ChatGPT", callback_data="chatgpt"), row=4)
    reply_markup.add(InlineKeyboardButton(text="🏙️ کیفیت هوای تهران", callback_data="pollution_tehran"), row=5)
    reply_markup.add(InlineKeyboardButton(text="✍️ Humanize AI", callback_data="humanizeai"), row=6)
    reply_markup.add(InlineKeyboardButton(text="🎬 دانلود از یوتیوب", callback_data="youtube_downloader"), row=7)

    first_name = message.from_user.first_name if message.from_user and message.from_user.first_name else "کاربر"
    with open("اسامی اشخاص ربات.txt", "a+", encoding="utf-8") as f:
        f.seek(0)
        ids = f.read().splitlines()
        if str(first_name) not in ids:
            f.write(f"{first_name}\n")
    await client.send_message(
        chat_id,
        text=f"✨ سلام {first_name}، به ربات هوشمند خوش آمدید!\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        components=reply_markup
    )

@client.event
async def on_ready():
    print(f"{client.user} آماده است! 🚀")

client.run()