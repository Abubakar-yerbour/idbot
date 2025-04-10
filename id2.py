from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7331733537:AAGqCPHuCM5mC2RQpZfh_pTEbxQv4agf9tA"

# In-memory storage for file info
files_db = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *File ID Bot*!\n\n"
        "📤 Send me any media (document, video, audio, photo), and I'll give you detailed info about it.\n\n"
        "📥 Or send me a file_id, unique_id, or message_id to retrieve the file.\n\n"
        "Let's get started!",
        parse_mode="Markdown"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file_info = None
    file_type = None

    if message.document:
        file_info = message.document
        file_type = "📦 *Document*"
    elif message.video:
        file_info = message.video
        file_type = "🎞 *Video*"
    elif message.audio:
        file_info = message.audio
        file_type = "🎵 *Audio*"
    elif message.photo:
        file_info = message.photo[-1]
        file_type = "🖼 *Photo*"
    else:
        return

    file_id = file_info.file_id
    unique_id = file_info.file_unique_id
    file_size = file_info.file_size
    file_name = getattr(file_info, 'file_name', 'N/A')
    mime_type = getattr(file_info, 'mime_type', 'N/A')

    files_db[file_id] = file_info
    files_db[unique_id] = file_info
    files_db[str(message.message_id)] = file_info

    forward_info = ""
    if message.forward_from:
        forward_info = (
            f"\n👤 *Forwarded from User:*\n"
            f"• Name: `{message.forward_from.full_name}`\n"
            f"• Username: @{message.forward_from.username}\n"
            f"• User ID: `{message.forward_from.id}`"
        )
    elif message.forward_from_chat:
        forward_info = (
            f"\n📢 *Forwarded from Channel:*\n"
            f"• Title: `{message.forward_from_chat.title}`\n"
            f"• Chat ID: `{message.forward_from_chat.id}`"
        )
    elif message.forward_sender_name:
        forward_info = f"\n👤 *Forwarded from:* `{message.forward_sender_name}`"

    response = (
        f"{file_type}\n"
        f"• file_id: `{file_id}`\n"
        f"• file_unique_id: `{unique_id}`\n"
        f"• file_name: `{file_name}`\n"
        f"• file_size: `{file_size}` bytes\n"
        f"• mime_type: `{mime_type}`\n"
        f"• message_id: `{message.message_id}`"
        f"{forward_info}"
    )

    await message.reply_text(response, parse_mode="Markdown")

async def retrieve_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    file_info = files_db.get(text)
    if file_info:
        try:
            await update.message.reply_document(document=file_info.file_id)
        except:
            await update.message.reply_text("❌ Couldn't send the file. It may no longer be available.")
    else:
        await update.message.reply_text("❌ Couldn't retrieve the file.\nMake sure the file ID is valid and the bot has seen this file before.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), retrieve_file))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.Video.ALL | filters.Audio.ALL | filters.PHOTO, handle_file))
    app.run_polling()

main()