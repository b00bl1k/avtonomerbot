import logging

from telegram import (
    Update,
    ChatAction)
from telegram.ext import (
    CallbackContext, CommandHandler, Filters, MessageHandler,
    CallbackQueryHandler)

import avtonomer
import db
import tasks

logger = logging.getLogger(__name__)

INPUT_FORMATS = """• `а123аа777` — информация о номере РФ
• `ааа777` — информация о серии РФ
• `ru05` — информация о регионе РФ
• `а0069МО` — информация о номере СССР"""
HELP = f"Бот для поиска по сайту avto-nomer.ru\n\nВведите:\n{INPUT_FORMATS}"


def ensure_user_created(telegram_id, from_user):
    return db.get_or_create_user(
        telegram_id, from_user.first_name, from_user.last_name,
        from_user.username, from_user.language_code
    )


def on_start_command(update: Update, context: CallbackContext):
    telegram_id = update.message.chat.id
    ensure_user_created(telegram_id, update.message.from_user)
    update.message.reply_markdown(HELP,)


def on_help_command(update: Update, context: CallbackContext):
    update.message.reply_markdown(HELP)


def on_search_query(update: Update, context: CallbackContext):
    if update.message:
        context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        user = ensure_user_created(chat_id, update.message.from_user)
        query = update.message.text
        if query.startswith("/"):  # handle as normal request
            query = query[1:]

        ru_query = avtonomer.translate_to_latin(query)
        su_query = avtonomer.translate_to_cyr(query)

        if avtonomer.validate_ru_plate_number(ru_query):
            search_query = db.add_search_query(user, ru_query)
            tasks.search_license_plate.delay(
                chat_id, message_id, search_query.id, page=0, edit=False)
        elif avtonomer.validate_su_plate_number(su_query):
            search_query = db.add_search_query(user, su_query, "su")
            tasks.search_license_plate.delay(
                chat_id, message_id, search_query.id, page=0, edit=False)
        elif avtonomer.validate_ru_plate_series(ru_query):
            search_query = db.add_search_query(user, ru_query)
            tasks.get_series_ru.delay(chat_id, message_id, search_query.id)
        elif avtonomer.validate_us_plate_series(query):
            search_query = db.add_search_query(user, query, "us")
            tasks.get_series_us.delay(chat_id, message_id, search_query.id)
        elif avtonomer.validate_ru_region(query):
            search_query = db.add_search_query(user, query)
            tasks.get_ru_region.delay(chat_id, message_id, search_query.id)
        else:
            update.message.reply_markdown(
                f"Некорректный запрос. Введите:\n{INPUT_FORMATS}",
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
    dispatcher.add_handler(CommandHandler("start", on_start_command))
    dispatcher.add_handler(CommandHandler("help", on_help_command))
    dispatcher.add_handler(MessageHandler(Filters.text, on_search_query))
    dispatcher.add_handler(CallbackQueryHandler(on_search_paginate))
    dispatcher.add_error_handler(on_error)
