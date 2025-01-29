from bale import Bot, CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, MenuKeyboardMarkup, MenuKeyboardButton
import pdox
import translate1111

client = Bot(token="1073138097:49XMJIzGSAXXffU4p5hFbiDQB6NLp7RCxqdDpPeW")

user_input_state = {}

@client.event
async def on_ready():
    print(client.user, "is ready!")

@client.event
async def on_message(message: Message):
    chat_id = message.chat.id
    if chat_id in user_input_state and user_input_state[chat_id].get("awaiting"):
        if user_input_state[chat_id]["awaiting"] == "origin":
            user_input_state[chat_id]["origin"] = message.content
            user_input_state[chat_id]["awaiting"] = "dest"
            await client.send_message(chat_id=chat_id, text="لطفاً مقصد (زبان) را وارد کنید:")
        elif user_input_state[chat_id]["awaiting"] == "dest":
            user_input_state[chat_id]["dest"] = message.content
            await client.send_message(chat_id=chat_id, text="لطفا متن اصلی را وارد کنید:")
            user_input_state[chat_id]["awaiting"] = "text"
        elif user_input_state[chat_id]["awaiting"] == "text":
            user_input_state[chat_id]["text"] = message.content
            origin = user_input_state[chat_id]["origin"]
            dest = user_input_state[chat_id]["dest"]
            text = user_input_state[chat_id]["text"]
            translation = translate1111.translate(text, origin, dest)  # Assuming this function takes text, source and destination as parameters
            await client.send_message(chat_id=chat_id, text=f"ترجمه: {translation}")
            user_input_state[chat_id]["awaiting"] = None
        return

    if message.content == "/start":
        reply_markup = InlineKeyboardMarkup()
        reply_markup.add(InlineKeyboardButton(text="تبدیل PDF به docx", callback_data="pdf_to_docx"), row=1)
        reply_markup.add(InlineKeyboardButton(text="ترجمه متن", callback_data="translate_text"), row=2)
        reply_markup.add(InlineKeyboardButton(text="شطرنج", callback_data="chess"), row=3)
        reply_markup.add(InlineKeyboardButton(text="دانلود ویدیو یوتیوب", callback_data="download_youtube"), row=4)
        reply_markup.add(InlineKeyboardButton(text="تبدیل صوت به متن", callback_data="audio_to_text"), row=5)
        await client.send_message(chat_id=chat_id, text=f"*Hi {message.author.first_name}, Welcome to IntelliBot*", components=reply_markup)

    elif message.content == "/keyboard":
        await client.send_message(chat_id=chat_id, text=f"*Hi {message.author.first_name}, Welcome to IntelliBot*",
                            components=MenuKeyboardMarkup().add(MenuKeyboardButton('translate')).add(MenuKeyboardButton('pdf docx')))

    elif message.content in ['package site', 'package github']:
        await client.send_message(chat_id=chat_id, text="This package is available at: {}".format(
            {"package site": 'https://python-bale-bot.ir', "package github": 'https://python-bale-bot.ir/github'}[message.content]
        ))

    elif message.content == "ترجمه":
        user_input_state[chat_id] = {"awaiting": "origin"}
        await client.send_message(chat_id=chat_id, text="لطفا متن مبدا (زبان) را وارد کنید:")

    else:
        await client.send_message(chat_id=chat_id, text=f"You said: {message.content}")

@client.event
async def on_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if callback.data == "pdf_to_docx":
        await client.send_message(chat_id=chat_id, text=pdox.main())
    elif callback.data == "translate_text":
        user_input_state[chat_id] = {"awaiting": "origin"}
        await client.send_message(chat_id=chat_id, text="لطفا متن مبدا (زبان) را وارد کنید:")
    elif callback.data == "chess":
        await client.send_message(chat_id=chat_id, text="Starting a game of chess...")
    elif callback.data == "download_youtube":
        await client.send_message(chat_id=chat_id, text="Please enter the link of the YouTube video:")
    elif callback.data == "audio_to_text":
        await client.send_message(chat_id=chat_id, text="Please upload the audio file for transcription:")

client.run()
