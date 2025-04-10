from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.helpers import escape_markdown
import logging

TOKEN = "7331733537:AAGqCPHuCM5mC2RQpZfh_pTEbxQv4agf9tA"

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
        "Send me any file (📄 PDF, 🎥 Video, 📦 ZIP, etc.) and I’ll give you the *file ID* and *unique file ID*.\n"
        "You can also send me a *file ID*, *unique file ID*, or *message ID* to retrieve the file.\n\n"
        "Need help? Contact @Cyb37h4ck37"
    )
    await update.message.reply_text(message, parse_mode="Markdown")

# Handle incoming media
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    file_info = None

    # Handle any media file
    media = msg.document or msg.video or msg.audio or msg.voice or msg.photo[-1] if msg.photo else None

    if media:
        file_id = media.file_id
        unique_id = media.unique_id
        file_name = getattr(media, 'file_name', None) or f"media_{unique_id}"
        file_size = media.file_size if hasattr(media, 'file_size') else 'Unknown'
        mime_type = getattr(media, 'mime_type', 'Unknown')

        file_ids[file_id] = file_id
        file_ids[unique_id] = file_id
        file_ids[file_name] = file_id

        sender_info = "❓ Unknown"
        if msg.forward_from:
            sender_info = f"👤 @{msg.forward_from.username or msg.forward_from.full_name} (ID: `{msg.forward_from.id}`)"
        elif msg.forward_from_chat:
            sender_info = f"📢 {msg.forward_from_chat.title or msg.forward_from_chat.username} (ID: `{msg.forward_from_chat.id}`)"

        file_info = (
            f"*File Info:*\n"
            f"• *Name:* `{escape_markdown(file_name, 2)}`\n"
            f"• *File ID:* `{file_id}`\n"
            f"• *Unique ID:* `{unique_id}`\n"
            f"• *Size:* `{file_size}` bytes\n"
            f"• *MIME Type:* `{mime_type}`\n"
            f"• *Sender:* {sender_info}"
        )

        await msg.reply_text(file_info, parse_mode="MarkdownV2")
    else:
        await msg.reply_text("⚠️ Unsupported file type.")

# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        file_id = file_ids.get(text, text)
        await update.message.reply_document(file_id)
    except Exception:
        try:
            await update.message.reply_video(file_id)
        except Exception:
            try:
                await update.message.reply_audio(file_id)
            except Exception:
                try:
                    await update.message.reply_photo(file_id)
                except Exception:
                    await update.message.reply_text("❌ Couldn't find or access the file.\nMake sure the ID is valid.")

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Error occurred:", exc_info=context.error)

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.Document.ALL |
        filters.Video.ALL |
        filters.Audio.ALL |
        filters.VOICE |
        filters.PHOTO,
        handle_file
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()