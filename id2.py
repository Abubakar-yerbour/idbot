import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)
from telegram.helpers import escape_markdown

# Set your bot token directly
TOKEN = "7331733537:AAGqCPHuCM5mC2RQpZfh_pTEbxQv4agf9tA"

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Send me any file (PDF, ZIP, video, etc.) and I’ll give you the `file_id`, `file_unique_id`, "
        "`size`, `name`, `dimensions`, and `duration` (if available)."
    )
    await update.message.reply_text(message)

# Handle incoming media files
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file_info = None

    if message.document:
        doc = message.document
        file_info = {
            "type": "Document",
            "file_id": doc.file_id,
            "file_unique_id": doc.file_unique_id,
            "file_name": doc.file_name,
            "file_size": doc.file_size,
            "mime_type": doc.mime_type
        }

    elif message.video:
        vid = message.video
        file_info = {
            "type": "Video",
            "file_id": vid.file_id,
            "file_unique_id": vid.file_unique_id,
            "file_name": vid.file_name,
            "file_size": vid.file_size,
            "mime_type": vid.mime_type,
            "width": vid.width,
            "height": vid.height,
            "duration": vid.duration,
            "thumbnail": vid.thumb.file_id if vid.thumb else None,
            "thumb_size": vid.thumb.file_size if vid.thumb else None,
            "thumb_dimensions": (vid.thumb.width, vid.thumb.height) if vid.thumb else None
        }

    elif message.audio:
        aud = message.audio
        file_info = {
            "type": "Audio",
            "file_id": aud.file_id,
            "file_unique_id": aud.file_unique_id,
            "file_name": aud.file_name,
            "file_size": aud.file_size,
            "mime_type": aud.mime_type,
            "duration": aud.duration
        }

    elif message.photo:
        photo = message.photo[-1]
        file_info = {
            "type": "Photo",
            "file_id": photo.file_id,
            "file_unique_id": photo.file_unique_id,
            "file_size": photo.file_size,
            "width": photo.width,
            "height": photo.height
        }

    elif message.voice:
        voice = message.voice
        file_info = {
            "type": "Voice",
            "file_id": voice.file_id,
            "file_unique_id": voice.file_unique_id,
            "file_size": voice.file_size,
            "duration": voice.duration
        }

    if file_info:
        text = f"📦 *{file_info['type']}*\n"
        for key, value in file_info.items():
            if key != "type" and value is not None:
                text += f"• `{key}`: `{value}`\n"
        await message.reply_text(text, parse_mode="Markdown")

# Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_file))
    app.run_polling()

if __name__ == '__main__':
    main()