import logging

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto,
    ChatAction)
from telegram.ext import (
    CallbackContext, CommandHandler, Filters, MessageHandler,
    CallbackQueryHandler)

import avtonomer
import db
import settings
import tasks

logger = logging.getLogger(__name__)


def ensure_user_created(telegram_id, from_user):
    return db.get_or_create_user(
        telegram_id, from_user.first_name, from_user.last_name,
        from_user.username, from_user.language_code
    )


def on_start(update: Update, context: CallbackContext):
    telegram_id = update.message.chat.id
    ensure_user_created(telegram_id, update.message.from_user)
    update.message.reply_markdown(
        "Для поиска отправьте номер в формате `а123аа777` или `ааа777`"
    )


def on_help(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Бот для поиска по сайту avto-nomer.ru"
    )


def on_search_query(update: Update, context: CallbackContext):
    if update.message:
        context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        user = ensure_user_created(chat_id, update.message.from_user)
        query = avtonomer.translate_to_latin(update.message.text)

        if avtonomer.validate_plate_number(query):
            search_query = db.add_search_query(user, query)
            tasks.search_license_plate.delay(
                chat_id, message_id, search_query.id, page=0, edit=False)
        elif avtonomer.validate_plate_series(query):
            search_query = db.add_search_query(user, query)
            tasks.get_series_info.delay(chat_id, message_id, search_query.id)
        else:
            update.message.reply_markdown(
                "Некорректный запрос. Введите номер в формате "
                "`а123аа777` или `ааа777`.",
                quote=True,
            )


def on_search_paginate(update: Update, context: CallbackContext):
    query = update.callback_query
    search_query_id, page_str = query.data.split("-")
    page = int(page_str)
    search_query = db.get_search_query(int(search_query_id))
    if not search_query:
        logger.warning("Invalid search query id %s", search_query_id)
        query.message.reply_text("Произошла ошибка. Введите номер повторно.")
        return

    db.add_inline_query(search_query, page_str)
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    tasks.search_license_plate.delay(
        chat_id, message_id, search_query.id, page=page, edit=True)


def on_error(update: Update, context: CallbackContext):
    logger.error(f"update cause error", exc_info=context.error, extra={
        "update": update.to_dict() if update else None,
    })


def register_commands(dispatcher):
    dispatcher.add_handler(CommandHandler("start", on_start))
    dispatcher.add_handler(CommandHandler("help", on_help))
    dispatcher.add_handler(MessageHandler(Filters.text, on_search_query))
    dispatcher.add_handler(CallbackQueryHandler(on_search_paginate))
    dispatcher.add_error_handler(on_error)
