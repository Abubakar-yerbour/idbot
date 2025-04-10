from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters,
    ContextTypes, CommandHandler
)
from telegram.helpers import escape_markdown
import logging

TOKEN = "7331733537:AAGqCPHuCM5mC2RQpZfh_pTEbxQv4agf9tA"

file_ids = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "👋 *Welcome!*\n\n"
        "📤 *Send me any file (video, document, image, audio, etc.) and I’ll give you full details including:*"
        "\n• File ID\n• Unique File ID\n• File Name\n• Size\n• Dimensions/Duration (if available)"
        "\n\n🗂 *Send me a File ID or Unique File ID and I’ll return the file to you!*"
        "\n\n🧙‍♂️ Group: *Created by Unknown Gods*"
    )
    await update.message.reply_text(escape_markdown(message, version=2), parse_mode="MarkdownV2")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file = None
    kind = "Unknown"

    if message.document:
        file = message.document
        kind = "Document"
    elif message.video:
        file = message.video
        kind = "Video"
    elif message.audio:
        file = message.audio
        kind = "Audio"
    elif message.photo:
        file = message.photo[-1]  # highest resolution
        kind = "Photo"
    else:
        await message.reply_text("Unsupported file type.")
        return

    file_ids[file.file_id] = file.file_id
    file_ids[file.unique_id] = file.file_id

    forwarded_info = ""
    if message.forward_from:
        forwarded_info = (
            f"\n\n👤 *Forwarded From:* `{escape_markdown(message.forward_from.full_name, 2)}`"
            f"\n🆔 *User ID:* `{message.forward_from.id}`"
        )
    elif message.forward_sender_name:
        forwarded_info = f"\n\n👤 *Forwarded From:* `{escape_markdown(message.forward_sender_name, 2)}`"

    details = (
        f"*{kind} Received*\n"
        f"📄 *File Name:* `{escape_markdown(getattr(file, 'file_name', 'N/A'), 2)}`\n"
        f"🆔 *File ID:* `{file.file_id}`\n"
        f"🔐 *Unique File ID:* `{file.unique_id}`\n"
        f"📦 *Size:* `{file.file_size} bytes`"
    )

    if kind == "Video":
        details += f"\n⏱ *Duration:* `{file.duration}s`"
        details += f"\n📏 *Dimensions:* `{file.width}x{file.height}`"
    elif kind == "Audio":
        details += f"\n⏱ *Duration:* `{file.duration}s`"
    elif kind == "Photo":
        details += f"\n📏 *Dimensions:* `{file.width}x{file.height}`"

    details += forwarded_info

    await message.reply_text(details, parse_mode="MarkdownV2")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    file_id = file_ids.get(text, text)

    try:
        await update.message.reply_document(file_id)
    except Exception:
        try:
            await update.message.reply_video(file_id)
        except Exception:
            try:
                await update.message.reply_photo(file_id)
            except Exception:
                try:
                    await update.message.reply_audio(file_id)
                except Exception:
                    await update.message.reply_text(
                        "❌ I couldn’t find or access that file.\n"
                        "Make sure the file ID is correct and the file still exists on Telegram."
                    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Exception while handling an update:", exc_info=context.error)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.video | filters.audio | filters.photo,
        handle_file
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    app.run_polling()


if __name__ == "__main__":
    main()