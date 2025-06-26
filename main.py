import json
import logging
from datetime import time, datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    ConversationHandler, filters
)
import gspread
from google.oauth2.service_account import Credentials

# --- НАСТРОЙКИ ---
BOT_TOKEN = "7589448484:AAGPmfUoP5rdkMoDWauxTn8LMP2yDTiEmaA"
ADMIN_CHAT_ID = 7723022511
GOOGLE_SHEET_NAME = "NEXEL_Bot_Data"
TIMEZONE_HOUR = 9

# --- ВАЖНО ---
# Вставь сюда JSON ключ сервисного аккаунта Google
GOOGLE_CREDENTIALS_JSON = {
  "type": "service_account",
  "project_id": "mineral-battery-444808-b6",
  "private_key_id": "f6528f31392b5e97e48b4bbe5bf9950a06853582",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCbpA4Y1DLjk54Q\n/2NTPhHkATWANtZPxkW4Qu5Mid7wYJrX0XC7iSsNQ6g1lSfcASyxu1k+2EAY1Tmg\nWJbEhrSyn8m+9jGtN9hRVxz2DZWRYeL0FXqGLH4TIVj13BN4ddJGaL26+C/OdWKz\n4GiHJmNml7R+qfsS11cRcXEfp6mYCb2CnLqFO4ou95lGyS2mmFoNkLyem0qRJIht\n+9jUu/kJzr8HesbiXpFUYcw4J0iHUcwVx40HjTGRpQL0QIMeHsFP41GXDd/qk/x0\nRL0chYmS1hmkX6GX2jKXYyoi58FDp6FSGIBooguSeZds3rv0U8WosPEhQ60IVTlJ\nNsf1JGMbAgMBAAECggEACYFe9Qg8pWZ2EF6wj7xqNk0WmeJ/ezbGOkcoK5d9/JtB\nya16X5G0heZcZw1ZdlfCBYbGIA7v9zRKhS7z4kPB1Gjq1tVNWmFfPjR+Sc6xlEPw\nquyG45vjBUMTnkxXChPUCEXMVJdkwAyuPwMVDy/6gSEBvnyeH1v0btXJTWAdfPH+\n7zbAMDtRMa72eqWpMMAGujfHbfQ2rQBTAOPtaZYNGt7BrmqeAd55xdDRBKo6Pkb3\noW8tHW+JMmi4WAeejbrXisQqhJkEy3Rx1Y2IF83YcTEXL0gxzbneW+CUJHXa2Sn6\nw9tkfQFd4EjV6Bs8ug4sAtKoM+R9iWxD6mazFFyCaQKBgQDQ9G/jIdd9zHb66UPj\nUCJgYJKEzILmXloYQTDaVm3w7PFsRF0wWcfcWl8/04+2n7HO5cGpNZHQoDV+2PqC\nd1q8MYj0OBMTExK+2lh0Q1sszYqu+7gDpTzdA5BTLBPQegGIJET3HMI/BMFK1XDG\n0mxzrU5zPW5MPbVFeYIn4iXSQwKBgQC+rsA+VUFa1Oq3yEsAT0iQq3UkbQd/Zk+B\nt+DhjPQ4NzmVE+DEVG4t39g3rdeyG70pImlwx+459oaW5RHWerxkMC88zGm2tp00\nZCQk8fxkMAqybhtpP+5l73t4E7S9hcQqAs2ZEa4LtFaWiHQj7rXHabR8o7uz4ZEw\nHXENgYL6SQKBgFgJZMqxi3U5HDgC59NyA8nPZmwFLnGY9ySY8thK6e9EJUOUWh7w\n9L/mY5Mks7wh9GxTaRC9vT3FAkT7bjBh0RzRUf5zUbYLpy46GGKDrnpl7zRiYdlH\nWSlVQw2H2KFRhiux/EyRFVYvzrCU1Psv1Pm33wG2tC3zIdivpSLgqUa5AoGBAJas\na4hVweDOYfJ7OJi0DXkTour3pHcNF0I/VFmmEcziBoRAQtmghbeGK8pDei9pL93z\nLTJLKXlvzgYqWCAMuBTK5mi6dcZFIo+lmdH/zRo1xB4eV1ahh/XQeNX3bFhd/RXd\nRSzxBYCGLe2hQXSrScSbSF083DNVyG4mtZCgiCjRAoGAI7JTIxKbPi2bYkLntOcV\nDaLzK8ckUxXmcGqnlkp74/YiDPMSWZ815xybnhJIJoYE18m/9QvsA3a8pm6uyPaG\nFtSHmhKBgP0ifJH3at94hqNQ+4lGOl+wfrDBIrwnWzFzyTDa489w2JjMbaXQDKkF\nm+LtTzKGEEYzRIj1PorsZJU=\n-----END PRIVATE KEY-----\n",
  "client_email": "nexel-kg@mineral-battery-444808-b6.iam.gserviceaccount.com",
  "client_id": "102365341063193228039",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/nexel-kg%40mineral-battery-444808-b6.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# --- ЛОГИ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Google Sheets авторизация ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS_JSON, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open(GOOGLE_SHEET_NAME)

faq_sheet = sheet.worksheet("FAQ")
feedback_sheet = sheet.worksheet("Feedback")

# --- Состояния ---
FEEDBACK_LIKE, FEEDBACK_DISLIKE, FEEDBACK_SUGGEST = range(3)
CONTACT_MESSAGE = 4

main_menu = ReplyKeyboardMarkup(
    [["📌 Частые вопросы", "📝 Оставить фидбек"], ["📩 Написать команде"]],
    resize_keyboard=True
)

# --- Хелперы ---

def get_faq_text():
    faqs = faq_sheet.get_all_values()
    if not faqs or len(faqs) < 2:
        return "FAQ пока пуст."
    text = "📌 Часто задаваемые вопросы:\n\n"
    for row in faqs[1:]:
        if len(row) >= 2:
            q, a = row[0], row[1]
            text += f"❓ {q}\n💬 {a}\n\n"
    return text

def save_feedback(user, like, dislike, suggest):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_sheet.append_row([now, user.full_name, user.username or "-", user.id, like, dislike, suggest])

# --- Хэндлеры ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_path = "welcome.jpg"
    welcome_text = (
        "👋 Привет! Я бот NEXEL.\n"
        "Рад видеть тебя здесь! Выберите действие из меню ниже."
    )
    try:
        with open(photo_path, "rb") as photo_file:
            await update.message.reply_photo(photo=photo_file, caption=welcome_text)
    except Exception:
        await update.message.reply_text(welcome_text)
    await update.message.reply_text("Выберите действие из меню:", reply_markup=main_menu)

async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_faq_text()
    await update.message.reply_text(text)

# --- Фидбек ---

async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👍 Что вам понравилось?", reply_markup=ReplyKeyboardRemove())
    return FEEDBACK_LIKE

async def feedback_dislike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["like"] = update.message.text
    await update.message.reply_text("👎 Что не понравилось?")
    return FEEDBACK_DISLIKE

async def feedback_suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dislike"] = update.message.text
    await update.message.reply_text("💡 Ваши предложения:")
    return FEEDBACK_SUGGEST

async def feedback_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["suggest"] = update.message.text
    user = update.effective_user
    try:
        save_feedback(user, context.user_data["like"], context.user_data["dislike"], context.user_data["suggest"])
        await update.message.reply_text("✅ Спасибо за фидбек!", reply_markup=main_menu)
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        await update.message.reply_text("⚠️ Ошибка при сохранении фидбека.", reply_markup=main_menu)
    return ConversationHandler.END

feedback_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(📝 Оставить фидбек)$"), feedback_start)],
    states={
        FEEDBACK_LIKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_dislike)],
        FEEDBACK_DISLIKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_suggest)],
        FEEDBACK_SUGGEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_save)],
    },
    fallbacks=[]
)

# --- Связь с командой ---

async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ Напишите сообщение команде:", reply_markup=ReplyKeyboardRemove())
    return CONTACT_MESSAGE

async def contact_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = f"📩 Сообщение от @{user.username or user.first_name}:\n\n{update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
    await update.message.reply_text("✅ Сообщение отправлено!", reply_markup=main_menu)
    return ConversationHandler.END

contact_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(📩 Написать команде)$"), contact_start)],
    states={CONTACT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_send)]},
    fallbacks=[]
)

# --- Админ команды для FAQ ---

async def add_faq_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return await update.message.reply_text("⛔ Нет доступа.")
    await update.message.reply_text("📝 Отправь вопрос и ответ через новую строку (в 2 строки):\n\nВопрос\nОтвет")
    return 10

async def add_faq_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return ConversationHandler.END
    lines = update.message.text.strip().split("\n")
    if len(lines) < 2:
        await update.message.reply_text("❗ Нужно 2 строки: вопрос и ответ.")
        return 10
    question, answer = lines[0], lines[1]
    faq_sheet.append_row([question, answer])
    await update.message.reply_text("✅ Вопрос добавлен в FAQ.")
    return ConversationHandler.END

add_faq_conv = ConversationHandler(
    entry_points=[CommandHandler("addfaq", add_faq_start)],
    states={10: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_faq_save)]},
    fallbacks=[]
)

# --- Напоминания (рассылка) ---

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    text = "🔔 Напоминание! Проверьте дедлайны и мероприятия."
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)

async def send_feedback_form(context: ContextTypes.DEFAULT_TYPE):
    chat_id = ADMIN_CHAT_ID
    await context.bot.send_message(chat_id=chat_id, text="📝 Пожалуйста, заполните форму фидбека:\nЧто понравилось?\nЧто не понравилось?\nЕсть ли предложения?")

# --- Вспомогательная функция для вычисления даты следующего понедельника 10:00 ---

def get_next_weekday_time(hour=10, minute=0, weekday=0):
    now = datetime.now()
    days_ahead = weekday - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    target_date = now + timedelta(days=days_ahead)
    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

# --- Основной запуск ---

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(📌 Частые вопросы)$"), show_faq))
    app.add_handler(feedback_conv)
    app.add_handler(contact_conv)
    app.add_handler(add_faq_conv)

    app.job_queue.run_daily(send_reminder, time=time(hour=TIMEZONE_HOUR))

    start_time = get_next_weekday_time(10, 0, 0)
    app.job_queue.run_repeating(send_feedback_form, interval=7*24*60*60, first=start_time)

    logger.info("🚀 Бот NEXEL запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()
