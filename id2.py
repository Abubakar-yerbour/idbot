import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters,
    ContextTypes, CommandHandler
)
from telegram.helpers import escape_markdown

# Load bot token from environment variable
TOKEN = os.getenv("TOKEN")

# Store file IDs with optional names
file_ids = {}

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "👋 *Welcome!*\n\n"
        "📎 Send me any file (PDF, ZIP, video, etc.) and I’ll give you the `file_id`.\n"
        "📥 You can also send me a file name or file ID to retrieve it later.\n\n"
        "❓ *Need help?* Contact @Cyb37h4ck37"
    )
    await update.message.reply_text(escape_markdown(message, version=1), parse_mode="Markdown")

# Handle media files
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    document = message.document
    video = message.video

    if document:
        file_id = document.file_id
        file_name = document.file_name or file_id
        file_ids[file_name] = file_id
        file_ids[file_id] = file_id

        await message.reply_text(
            f"📄 *Document saved:*\n{escape_markdown(file_name, 1)}\n\n`{escape_markdown(file_id, 1)}`",
            parse_mode="Markdown"
        )

    elif video:
        file_id = video.file_id
        file_name = f"video_{file_id}"
        file_ids[file_name] = file_id
        file_ids[file_id] = file_id

        await message.reply_text(
            f"🎥 *Video saved:*\n{escape_markdown(file_name, 1)}\n\n`{escape_markdown(file_id, 1)}`",
            parse_mode="Markdown"
        )
    else:
        await message.reply_text("⚠️ Unsupported file type.")

# Handle file ID or file name in text
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("\\_", "_")
    file_id = file_ids.get(text, text)

    try:
        await update.message.reply_document(file_id)
    except Exception:
        try:
            await update.message.reply_video(file_id)
        except Exception:
            await update.message.reply_text(
                "❌ I couldn’t find or access that file.\n"
                "Make sure the file ID is correct and the file still exists on Telegram."
            )

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Exception while handling an update:", exc_info=context.error)

# Run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()
