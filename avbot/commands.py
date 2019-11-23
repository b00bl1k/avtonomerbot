from datetime import timedelta
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto)
from telegram.ext import (
    CallbackContext, CommandHandler, Filters, MessageHandler,
    CallbackQueryHandler)

import avtonomer
import cache
import db
import settings

logger = logging.getLogger(__name__)


@cache.cached_func(timedelta(minutes=10))
def get_license_plate(plate_number):
    return avtonomer.search(plate_number, settings.AN_KEY)


def ensure_user_created(telegram_id, from_user):
    return db.get_or_create_user(
        telegram_id, from_user.first_name, from_user.last_name,
        from_user.username, from_user.language_code
    )


def make_search_reply(cars, search_query, page=0):
    car = cars[page]
    cars_count = len(cars)
    reply_kwargs = {
        "photo": car["photo"]["medium"],
        "caption": f"{page + 1}/{cars_count} {car['make']} {car['model']} "
                   f"{car['photo']['link']}",
    }
    if len(cars) > 1:
        buttons = [[
            InlineKeyboardButton(
                f"{i + 1}",
                callback_data=f"{search_query.id}-{i}"
            )
            for i in range(cars_count)
            if i != page
        ]]
        reply_kwargs.update({
            "reply_markup": InlineKeyboardMarkup(buttons)
        })
    return reply_kwargs


def on_start(update: Update, context: CallbackContext):
    telegram_id = update.message.chat.id
    ensure_user_created(telegram_id, update.message.from_user)
    update.message.reply_text(
        "Для поиска отправьте номер в формате а123аа123."
    )


def on_help(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Бот для поиска по сайту avto-nomer.ru"
    )


def on_search_query(update: Update, context: CallbackContext):
    telegram_id = update.message.chat.id
    user = ensure_user_created(telegram_id, update.message.from_user)
    plate_number = avtonomer.translate_to_latin(update.message.text)
    if not avtonomer.validate_plate_number(plate_number):
        update.message.reply_text(
            "Некорректный запрос. Введите номер в формате а001аа199"
        )
    else:
        search_query = db.add_search_query(user, plate_number)
        result = get_license_plate(plate_number)
        if not result:
            update.message.reply_text("Сервис временно недоступен")
        elif result["error"] != 0:
            update.message.reply_text("По вашему запросу ничего не найдено")
        else:
            reply_kwargs = make_search_reply(result["cars"], search_query)
            update.message.reply_photo(**reply_kwargs)


def on_search_paginate(update: Update, context: CallbackContext):
    query = update.callback_query
    search_query_id, page_str = query.data.split("-")
    page = int(page_str)
    search_query = db.get_search_query(int(search_query_id))
    db.add_inline_query(search_query, page_str)
    if not search_query:
        logger.warning("Invalid search query id %s", search_query_id)
    else:
        result = get_license_plate(search_query.query_text)
        if result and result["error"] == 0:
            reply_kwargs = make_search_reply(result["cars"], search_query, page)
            photo = reply_kwargs.pop("photo")
            caption = reply_kwargs.pop("caption")
            reply_kwargs.update({
                "media": InputMediaPhoto(photo, caption=caption),
                "chat_id": query.message.chat_id,
                "message_id": query.message.message_id
            })
            context.bot.edit_message_media(**reply_kwargs)


def on_error(update: Update, context: CallbackContext):
    logger.error(f"update '{update}' cause error", exc_info=context.error)


def register_commands(dispatcher):
    dispatcher.add_handler(CommandHandler("start", on_start))
    dispatcher.add_handler(CommandHandler("help", on_help))
    dispatcher.add_handler(MessageHandler(Filters.text, on_search_query))
    dispatcher.add_handler(CallbackQueryHandler(on_search_paginate))
    dispatcher.add_error_handler(on_error)
