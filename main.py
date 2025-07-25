import logging
from datetime import time, datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, ConversationHandler, filters
)
import gspread
from google.oauth2.service_account import Credentials

# --- НАСТРОЙКИ ---
BOT_TOKEN = "7589448484:AAGPmfUoP5rdkMoDWauxTn8LMP2yDTiEmaA"
ADMIN_CHAT_ID = [7723022511, 5005318439]
GOOGLE_SHEET_NAME = "NEXEL_Bot_Data"
TIMEZONE_HOUR = 9  # Часовой пояс

# --- ЛОГИ ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Авторизация Google Sheets ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
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
    welcome_text = (
        "👋 Привет! Я бот NEXEL.\n"
        "Рад видеть тебя здесь! Выберите действие из меню ниже."
    )
    try:
        with open("welcome.jpg", "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=welcome_text)
    except Exception:
        await update.message.reply_text(welcome_text)
    await update.message.reply_text("Выберите действие из меню:", reply_markup=main_menu)

async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_faq_text())

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
    try:
        save_feedback(update.effective_user, context.user_data["like"], context.user_data["dislike"], context.user_data["suggest"])
        await update.message.reply_text("✅ Спасибо за фидбек!", reply_markup=main_menu)
    except Exception as e:
        logger.error(f"Ошибка сохранения фидбека: {e}")
        await update.message.reply_text("⚠️ Не удалось сохранить фидбек.", reply_markup=main_menu)
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

# --- Контакт ---
async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ Напишите сообщение команде:", reply_markup=ReplyKeyboardRemove())
    return CONTACT_MESSAGE

async def contact_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"📩 Сообщение от @{update.effective_user.username or update.effective_user.first_name}:\n\n{update.message.text}"
    for admin_id in ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=admin_id, text=msg)
    await update.message.reply_text("✅ Сообщение отправлено!", reply_markup=main_menu)
    return ConversationHandler.END

contact_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(📩 Написать команде)$"), contact_start)],
    states={CONTACT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_send)]},
    fallbacks=[]
)

# --- FAQ admin ---
async def add_faq_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_CHAT_ID:
        return await update.message.reply_text("⛔ Нет доступа.")
    await update.message.reply_text("📝 Отправь вопрос и ответ через новую строку (в 2 строки):\n\nВопрос\nОтвет")
    return 10

async def add_faq_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_CHAT_ID:
        return ConversationHandler.END
    lines = update.message.text.strip().split("\n")
    if len(lines) < 2:
        await update.message.reply_text("❗ Нужно 2 строки: вопрос и ответ.")
        return 10
    faq_sheet.append_row([lines[0], lines[1]])
    await update.message.reply_text("✅ Вопрос добавлен.")
    return ConversationHandler.END

add_faq_conv = ConversationHandler(
    entry_points=[CommandHandler("addfaq", add_faq_start)],
    states={10: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_faq_save)]},
    fallbacks=[]
)

# --- Напоминания ---
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    text = "🔔 Напоминание! Проверьте дедлайны и мероприятия."
    for admin_id in ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=admin_id, text=text)

async def send_feedback_form(context: ContextTypes.DEFAULT_TYPE):
    text = "📝 Пожалуйста, заполните форму фидбека:\nЧто понравилось?\nЧто не понравилось?\nЕсть ли предложения?"
    for admin_id in ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=admin_id, text=text)

def get_next_weekday_time(hour=10, minute=0, weekday=0):
    now = datetime.now()
    days_ahead = weekday - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return now + timedelta(days=days_ahead, hours=hour - now.hour, minutes=minute - now.minute)

# --- main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(📌 Частые вопросы)$"), show_faq))
    app.add_handler(feedback_conv)
    app.add_handler(contact_conv)
    app.add_handler(add_faq_conv)

    # job_queue
    app.job_queue.run_daily(send_reminder, time=time(hour=TIMEZONE_HOUR))
    app.job_queue.run_repeating(send_feedback_form, interval=7*24*60*60, first=get_next_weekday_time(10, 0, 0))

    logger.info("🚀 Бот NEXEL запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()
