import os
import logging
import base64
import requests
from typing import Optional, Dict

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Debug: Print loaded tokens
print(f"Loaded bot token: {os.environ.get('TELEGRAM_BOT_TOKEN')}")

# -------------------------
# API Setup
# -------------------------
# Gemini API Setup for text-based questions
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

chat_session = model.start_chat(history=[])

# Groq API Setup for image analysis
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# -------------------------
# Telegram Bot Setup
# -------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No token found! Make sure TELEGRAM_BOT_TOKEN is set in .env file")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------------
# Helper Functions
# -------------------------
GRADE_LEVELS = {
    "1-5": "elementary",
    "6-8": "middle",
    "9-12": "high"
}

user_grades: Dict[int, str] = {}

def get_homework_help(question: str, grade_level: str) -> Optional[str]:
    """
    Uses the Gemini API to get help with homework questions.
    Returns direct answers based on grade level.
    """
    prompt = (
        f"You are helping with {grade_level} school homework. Question: {question}\n\n"
        "Provide ONLY the direct answer. No explanations unless specifically asked.\n"
        "Format the answer neatly and clearly."
    )

    try:
        response = chat_session.send_message(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error getting homework help: {e}")
        return None

def analyze_homework_image(image_bytes: bytes, grade_level: str) -> Optional[str]:
    """
    Analyzes homework image and provides direct answers.
    """
    try:
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(image_bytes))

        prompt = f"""You are helping with {grade_level} school homework.
        Look at the image, solve any problems shown, and provide the answers.
        If there are multiple questions, number your answers.
        Provide ONLY the solution/answer without explanations unless specifically asked.
        If you see a math problem, show the final answer.
        If you see a question, provide the direct answer."""

        response = model.generate_content([prompt, image])
        return response.text.strip() if response.text else None

    except Exception as e:
        logger.error(f"Error analyzing homework image: {str(e)}")
        return None

# -------------------------
# Message Handlers
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Grades 1-5", callback_data="grade_1-5"),
            InlineKeyboardButton("Grades 6-8", callback_data="grade_6-8"),
            InlineKeyboardButton("Grades 9-12", callback_data="grade_9-12"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to the Homework Answer Bot!\n\n"
        "Please select your child's grade level:",
        reply_markup=reply_markup
    )

async def change_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Grades 1-5", callback_data="grade_1-5"),
            InlineKeyboardButton("Grades 6-8", callback_data="grade_6-8"),
            InlineKeyboardButton("Grades 9-12", callback_data="grade_9-12"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select new grade level:",
        reply_markup=reply_markup
    )

async def handle_grade_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    grade_range = query.data.replace("grade_", "")
    user_id = query.from_user.id
    user_grades[user_id] = GRADE_LEVELS[grade_range]

    await query.edit_message_text(
        f"Grade level set to: {grade_range}\n\n"
        "You can now send homework questions or photos to get direct answers.\n"
        "Use /change_grade to change the grade level."
    )

async def handle_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_grades:
        await update.message.reply_text(
            "Please set your child's grade level first using /start"
        )
        return

    question = update.message.text
    grade_level = user_grades[user_id]

    answer = get_homework_help(question, grade_level)
    if answer:
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text(
            "Sorry, I couldn't process that question. Please try again."
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_grades:
        await update.message.reply_text(
            "Please set your child's grade level first using /start"
        )
        return

    try:
        await update.message.reply_text("Analyzing homework...")
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()

        grade_level = user_grades[user_id]
        analysis = analyze_homework_image(photo_bytes, grade_level)

        if analysis:
            await update.message.reply_text(analysis)
        else:
            await update.message.reply_text(
                "Sorry, I couldn't read that image. Please try a clearer photo."
            )
    except Exception as e:
        logger.error(f"Error in handle_photo: {str(e)}")
        await update.message.reply_text(
            "Sorry, there was an error processing your photo. Please try again."
        )

# -------------------------
# Main Function
# -------------------------
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change_grade", change_grade))
    application.add_handler(CallbackQueryHandler(handle_grade_selection, pattern="^grade_"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_question))

    print("Starting homework answer bot...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot stopped gracefully!")
