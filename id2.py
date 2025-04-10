from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import logging

# Bot token
TOKEN = "7331733537:AAGqCPHuCM5mC2RQpZfh_pTEbxQv4agf9tA"

# File storage
file_ids = {}

# Logging
logging.basicConfig(level=logging.INFO)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "👋 *Welcome!*\n\n"
        "Send me *any file* (video, image, document, etc.), and I’ll reply with its details and ID.\n"
        "You can also *send me a file ID, unique ID, or name* and I’ll return the file.\n\n"
        "Need help? Contact @Cyb37h4ck37"
    )
    await update.message.reply_text(message, parse_mode="Markdown")

# Handle all incoming files
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file = None
    file_type = None

    if message.document:
        file = message.document
        file_type = "Document"
    elif message.video:
        file = message.video
        file_type = "Video"
    elif message.audio:
        file = message.audio
        file_type = "Audio"
    elif message.photo:
        file = message.photo[-1]  # best quality
        file_type = "Photo"
    elif message.voice:
        file = message.voice
        file_type = "Voice"

    if not file:
        await message.reply_text("Unsupported file type.")
        return

    file_id = file.file_id
    unique_id = file.file_unique_id
    file_name = getattr(file, "file_name", None) or f"{file_type}_{unique_id}"
    file_size = file.file_size
    duration = getattr(file, "duration", None)
    width = getattr(file, "width", None)
    height = getattr(file, "height", None)

    file_ids[file_id] = file_id
    file_ids[unique_id] = file_id
    file_ids[file_name] = file_id

    original_sender = ""
    if message.forward_from:
        sender = message.forward_from
        original_sender = f"\nForwarded From User: {sender.full_name} (ID: {sender.id})"
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        original_sender = f"\nForwarded From Channel: {chat.title or chat.username} (ID: {chat.id})"

    details = (
        f"*{file_type} received!*\n\n"
        f"*File Name:* `{file_name}`\n"
        f"*File ID:* `{file_id}`\n"
        f"*Unique ID:* `{unique_id}`\n"
        f"*Size:* {file_size} bytes\n"
    )
    if duration:
        details += f"*Duration:* {duration}s\n"
    if width and height:
        details += f"*Dimensions:* {width}x{height}\n"
    details += original_sender

    await message.reply_text(details, parse_mode="Markdown")

# Handle file requests by ID/name
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("\\_", "_")
    file_id = file_ids.get(text, text)

    try:
        await update.message.reply_document(file_id)
        return
    except:
        pass
    try:
        await update.message.reply_video(file_id)
        return
    except:
        pass
    try:
        await update.message.reply_audio(file_id)
        return
    except:
        pass
    try:
        await update.message.reply_photo(file_id)
        return
    except:
        pass
    try:
        await update.message.reply_voice(file_id)
        return
    except:
        pass

    await update.message.reply_text("❌ Couldn’t find or access that file.")

# Error logging
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Error occurred:", exc_info=context.error)

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.document | filters.video | filters.audio | filters.photo | filters.voice,
        handle_file
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()