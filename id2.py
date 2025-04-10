from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes
import logging
import os

# Your bot token
TOKEN = "7331733537:AAGqCPHuCM5mC2RQpZfh_pTEbxQv4agf9tA"

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# /start command with emojis
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome!*\n\n"
        "📤 Send me any media (video, document, photo, or audio), and I’ll give you detailed file info.\n"
        "📥 Or send a `file_id` or `file_unique_id`, and I’ll send the file back if I can!",
        parse_mode="Markdown"
    )

# Handle incoming media and show info
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file_info_text = ""

    if message.document:
        doc = message.document
        file_info_text = (
            "📦 *Document*\n"
            f"• file_id: `{doc.file_id}`\n"
            f"• file_unique_id: `{doc.file_unique_id}`\n"
            f"• file_name: {doc.file_name}\n"
            f"• file_size: {doc.file_size} bytes\n"
            f"• mime_type: {doc.mime_type}"
        )
    elif message.video:
        vid = message.video
        file_info_text = (
            "🎬 *Video*\n"
            f"• duration: {vid.duration} seconds\n"
            f"• width: {vid.width}, height: {vid.height}\n"
            f"• mime_type: {vid.mime_type}\n"
            f"• file_id: `{vid.file_id}`\n"
            f"• file_unique_id: `{vid.file_unique_id}`\n"
            f"• file_size: {vid.file_size} bytes"
        )
    elif message.audio:
        aud = message.audio
        file_info_text = (
            "🎵 *Audio*\n"
            f"• duration: {aud.duration} seconds\n"
            f"• performer: {aud.performer or 'N/A'}\n"
            f"• title: {aud.title or 'N/A'}\n"
            f"• mime_type: {aud.mime_type}\n"
            f"• file_id: `{aud.file_id}`\n"
            f"• file_unique_id: `{aud.file_unique_id}`\n"
            f"• file_size: {aud.file_size} bytes"
        )
    elif message.photo:
        photo = message.photo[-1]  # Highest quality
        file_info_text = (
            "🖼️ *Photo*\n"
            f"• file_id: `{photo.file_id}`\n"
            f"• file_unique_id: `{photo.file_unique_id}`\n"
            f"• width: {photo.width}, height: {photo.height}\n"
            f"• file_size: {photo.file_size or 'N/A'} bytes"
        )
    else:
        file_info_text = "⚠️ Unsupported file type."

    await message.reply_text(file_info_text, parse_mode="Markdown")

# Handle file_id or file_unique_id
async def fetch_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        telegram_file = await context.bot.get_file(text)
        await telegram_file.download_to_drive("tempfile")
        await update.message.reply_document(InputFile("tempfile"))
        os.remove("tempfile")
    except Exception as e:
        logger.error(f"Error fetching file: {e}")
        await update.message.reply_text(
            "❌ Couldn't retrieve the file.\nMake sure the file ID is valid and the bot has seen this file before."
        )

# Start the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.VIDEO | filters.AUDIO | filters.PHOTO,
        handle_file
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_by_id))

    print("Bot is running...")
    app.run_polling()