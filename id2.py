import logging
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)

# Bot token
TOKEN = "7331733537:AAGqCPHuCM5mC2RQpZfh_pTEbxQv4agf9tA"

# Logging
logging.basicConfig(level=logging.INFO)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Media Info Bot!\n\n"
        "📥 Send me any file, video, photo, or audio and I’ll give you its full info.\n"
        "📤 Or send me a file_id or file_unique_id and I’ll return the file to you!"
    )

# Handle received media
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    file_info = None
    label = "📦 Document"

    if msg.document:
        f = msg.document
        file_info = {
            "file_id": f.file_id,
            "file_unique_id": f.file_unique_id,
            "file_name": f.file_name,
            "file_size": f.file_size,
            "mime_type": f.mime_type
        }

    elif msg.video:
        f = msg.video
        label = "🎞️ Video"
        file_info = {
            "file_id": f.file_id,
            "file_unique_id": f.file_unique_id,
            "file_name": f.file_name,
            "file_size": f.file_size,
            "mime_type": f.mime_type,
            "width": f.width,
            "height": f.height,
            "duration": f"{f.duration // 60}:{f.duration % 60:02d}"
        }

        if f.thumb:
            file_info.update({
                "thumbnail": f.thumb.file_id,
                "thumb_size": f.thumb.file_size,
                "thumb_dimensions": f"{f.thumb.width}x{f.thumb.height}"
            })

    elif msg.audio:
        f = msg.audio
        label = "🎵 Audio"
        file_info = {
            "file_id": f.file_id,
            "file_unique_id": f.file_unique_id,
            "file_name": f.file_name,
            "file_size": f.file_size,
            "mime_type": f.mime_type,
            "duration": f"{f.duration // 60}:{f.duration % 60:02d}"
        }

    elif msg.photo:
        f = msg.photo[-1]
        label = "🖼️ Photo"
        file_info = {
            "file_id": f.file_id,
            "file_unique_id": f.file_unique_id,
            "file_size": f.file_size,
            "dimensions": f"{f.width}x{f.height}"
        }

    if file_info:
        text = f"{label}\n"
        for key, value in file_info.items():
            text += f"• {key}: {value}\n"
        await msg.reply_text(text)

# Handle incoming text to fetch file by ID
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.text.strip()
    try:
        await update.message.reply_document(document=file_id)
    except Exception as e:
        await update.message.reply_text("⚠️ Could not send file. Please make sure the ID is correct or the bot has access to it.")

# Run the bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL | filters.Video.ALL | filters.Audio.ALL | filters.PHOTO, handle_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()