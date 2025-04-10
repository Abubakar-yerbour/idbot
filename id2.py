from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes
import logging

# Your bot token
TOKEN = "7331733537:AAGqCPHuCM5mC2RQpZfh_pTEbxQv4agf9tA"

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command with friendly emojis
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the File Info & Fetch Bot!\n\n"
        "📤 Send me any media (videos, documents, photos, audio), and I'll give you all the details.\n"
        "📥 Send me a file_id or file_unique_id, and I'll return the original file if I can."
    )

# Handle media files
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
            f"• width: {vid.width}\n"
            f"• height: {vid.height}\n"
            f"• file_name: {vid.file_name or 'N/A'}\n"
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
        photo = message.photo[-1]  # Highest resolution
        file_info_text = (
            "🖼️ *Photo*\n"
            f"• file_id: `{photo.file_id}`\n"
            f"• file_unique_id: `{photo.file_unique_id}`\n"
            f"• width: {photo.width}\n"
            f"• height: {photo.height}\n"
            f"• file_size: {photo.file_size or 'N/A'} bytes"
        )
    else:
        file_info_text = "⚠️ Unsupported file type."

    await message.reply_text(file_info_text, parse_mode='Markdown')

# Handle messages that may be file IDs
async def fetch_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        file = await context.bot.get_file(text)
        await file.download_to_drive(f"temp_file")
        await update.message.reply_document(InputFile("temp_file"))
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("⚠️ Couldn't fetch the file. Make sure the file_id or file_unique_id is valid and known to the bot.")

# Main setup
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.video | filters.audio | filters.photo, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_by_id))

    print("Bot is running...")
    app.run_polling()