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
  "private_key_id": "8a0223fa864f0aaf59663620d23cb8954dcd9d5c",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCbcYBV64iQIUCG\nEI66P12KB1ROEh+DSkSBXevvtNwMxMXT7TSOVnd2mB2rbunUw0kQkjVVlBj7PnLz\nrdzHuJvs00Fk1a0byuVrwQ/zNap5TeoyRHvLEneSa9Aufyk6S4iIP+i2vpjuCYLO\nzLwIWAny9l5DMoLGSQGuZBNAbbd8v1UPdw5AFVitbAAx4W8zqSB1LP6zxtNDn1M+\nsiux4Sh+M+ssFwQg7F4pVHn3q9dCZgF3as880uImkGO+oQSXbNAM+4e1Z2Qkymbi\ndSM8uqUc1KYaHmExNUP0ALO8KV6aUlQblpt1Vi62MPM6HP0GOwGMJMp69DDRsDXR\n1shbV7xrAgMBAAECggEAIzpPV+mHqwZmLZvuBMach84ObJ0N2D7KFLl44XvPDPPB\nU7yj1whAjbd+rd32j1nsop1ICguEt9fYzGHgMcEkUUE1RklosG5EnS2FVFyatGAU\njezYU1btk1jstsTpzoTUvfAh6Nx8IyIzq3NZv9hX9OChzz/QxGhCQcf7VvQmi9Yk\nYLZVRxGTPLSgk0uoOu/N/g7aI+0hk1W+lLNeEGJd/pT5ZsjHXxRJ+Gs64/d8FXHa\nnAuaMOPUo3qPvvUgsxFNju+8Xbiy2jLx0NuRPKoabVTjgVHWwcQw31pXIdW4HLDp\nT73x29g8VeRy8i0uXnYtMDlBwLjImtoOKCHcpO90JQKBgQDI6r3Q96Y/86JtlZHX\neFzFBdAcdYKP6MKnOaKQSmOo0HR+W+fZbZHPw/Z10OTl9XjxgH83hA/Yw8fv0X/B\ni1bS7nFjnN+w358lpt7BExMhg2wgM22lvJeorwFIX6PV0yJVLXaJSJbT4Aftsi8J\ndWY5QoTzl0rTAOcErSjvwAwCDQKBgQDGDzfFKnZ8Uey2XkqM+YL2aFvoEHLB8ksY\nyhsHsdbuPauRvLrqNJIHqn1JMAAoOYceQUpnmTglsOBoP5troo63nEFLuPRY3BVo\nYSWj3x6N0kg74q+GPuZrE5P4LYM3iXkYJN8bLy9M8Sfg0NhI6HnrXWmUlQnJ26rz\nc6wMfa6yVwKBgQCZ45qx9Q2kjCLMFrTXOfysd/BX6/Wt7lUxqqaGKEQ/KDMiGZjy\n48a8QVeEFBVOwX76Uzadugw9Nm/skyVshCJje3jkGGMJYa7PMwoJDmgn0ja+T0Xb\nnSD4ddrgqUie3ZG9dg4FxtCnxj+sYz892msKzpVw0l/gUB+iaFMjl5Ba/QKBgHUT\ngdAW7btHYjnbOw5iX7vwrINdVbi31RRuQ9Qkl/x0j/qyKXtQYBIQAcdFjJI6j1if\nF7Btrfb5u21kTCcwDFUVFLQCPM5aKn1tD6byuUj0SKa9tSwR+nrJM+q8XJhztxVC\nlm+nULqWww/t5CwU4Bz1NvgRsZuVMlR+x/EKSj45AoGAA4YaFT8Pv4HJLPCyVVgv\nK56HJNty0b4VMvXtv6nChrnWEznM9a5uzJDLHJhoZ3X555CWNgZn6Aczy1E6NKpm\nF1wcKbu658KZdu4N+1QXLV+UYiJcMDe7SBSBaGszI0mwA1nk1GNJJvewyBZUPZnP\np3Bit159NI+fsUoDyY09/GA=\n-----END PRIVATE KEY-----\n",
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
