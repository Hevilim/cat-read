import os
import io
import telebot
from dotenv import load_dotenv
from database.core import init_db
from utils.extractor import parse
from indexer import index_doc, search
from utils.summarizer import summarize_text_llm
from database.crud import add_user, save_file, get_files, get_file, delete_file
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message):
    add_user(message.from_user)
    welcome = (
        f"Привет, {message.from_user.first_name}!\n\n"
        "Доступные команды:\n"
        "🔹 /help — помощь и описание функционала\n"
        "🔹 /list — список ваших загруженных файлов\n\n"
        "Просто отправьте сообщение или файл."
    )
    bot.send_message(message.chat.id, welcome)


@bot.message_handler(commands=['help'])
def handle_help(message):
    text = (
        "ℹ️ <b>Функционал бота:</b>\n\n"
        "— Отправьте <b>сообщение</b> — бот выполнит <b>поиск</b> по всем загруженным файлам.\n"
        "— Отправьте <b>файл</b> — он будет <b>сохранён и проиндексирован</b>.\n\n"
        "Команды:\n"
        "🔹 /list — список ваших файлов\n"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")


@bot.message_handler(commands=['list'])
def handle_list(message):
    files = get_files(message.from_user.id)
    if not files:
        bot.send_message(message.chat.id, "📂 У вас пока нет загруженных файлов.")
        return

    for f in files:
        text = (
            f"📄 <b>{f.filename}</b>\n  |\n"
            f"🕒 Добавлено: {f.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🧠 Выжимка", callback_data=f"summary_{f.id}"))
        markup.add(InlineKeyboardButton("⬇ Скачать", callback_data=f"download_{f.id}"))
        markup.add(InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{f.id}"))
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("summary_"))
def handle_summary(call):
    file_id = int(call.data.split("_")[1])
    f = get_file(file_id)
    if f:
        try:
            summary = summarize_text_llm(f.content)
            bot.send_message(
                call.message.chat.id,
                f"🧠 <b>Выжимка из файла {f.filename}:</b>\n\n{summary}",
                parse_mode="HTML"
            )
        except Exception as e:
            bot.send_message(call.message.chat.id, "⚠️ Не удалось сгенерировать выжимку.")
            print("[ERROR] Ошибка при генерации выжимки:", e)
    else:
        bot.answer_callback_query(call.id, "Файл не найден.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
def handle_download(call):
    file_id = int(call.data.split("_")[1])
    f = get_file(file_id)
    if f:
        bot.send_document(call.message.chat.id, InputFile(io.BytesIO(f.content.encode()), file_name=f.filename))


@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def handle_delete(call):
    file_id = int(call.data.split("_")[1])
    success = delete_file(file_id)
    if success:
        bot.edit_message_text("✅ Файл удалён.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Ошибка при удалении файла.")


@bot.message_handler(content_types=['document'])
def handle_file(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    content = parse(downloaded_file, message.document.mime_type)

    if not content.strip():
        bot.reply_to(message, "⚠️ Не удалось извлечь текст из файла. Возможно, это скан или защищённый PDF.")
        return

    file_id = save_file(message.from_user.id, message.document.file_name, content)
    index_doc(file_id, content)
    bot.reply_to(message, "✅ Файл загружен и проиндексирован.")


@bot.message_handler(func=lambda m: True)
def handle_search(message):
    results = search(message.text)
    if not results:
        bot.send_message(message.chat.id, "❌ Ничего не найдено.")
        return

    found = False
    for file_id in results:
        f = get_file(int(file_id))
        if not f:
            continue

        snippet = get_snippet(f.content, message.text)
        if not snippet.strip():
            continue

        found = True
        text = f"📄 <b>{f.filename}</b>\n  |\n🔍 ...{snippet}..."
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    if not found:
        bot.send_message(message.chat.id, "❌ Ничего не найдено.")


def get_snippet(text, query, window=20):
    idx = text.lower().find(query.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(query) + window)
    return text[start:end]


if __name__ == '__main__':
    init_db()
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)