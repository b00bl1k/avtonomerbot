from datetime import timedelta
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto)
from telegram.ext import (
    CallbackContext, CommandHandler, Filters, MessageHandler,
    CallbackQueryHandler)
import avtonomer
import settings
from utils import cached_func

logger = logging.getLogger(__name__)


@cached_func(timedelta(minutes=10))
def get_license_plate(plate_number):
    return avtonomer.search(plate_number, settings.AN_KEY)


def make_search_reply(cars, plate_number, page=0):
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
                callback_data=f"{plate_number}-{i}"
            )
            for i in range(cars_count)
            if i != page
        ]]
        reply_kwargs.update({
            "reply_markup": InlineKeyboardMarkup(buttons)
        })
    return reply_kwargs


def on_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Для поиска отправьте номер в формате а123аа123."
    )


def on_help(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Бот для поиска по сайту avto-nomer.ru"
    )


def on_search_query(update: Update, context: CallbackContext):
    plate_number = avtonomer.translate_to_latin(update.message.text)
    if not avtonomer.validate_plate_number(plate_number):
        update.message.reply_text(
            "Некорректный запрос. Введите номер в формате а001аа99"
        )
    else:
        result = get_license_plate(plate_number)
        if not result:
            update.message.reply_text("Сервис временно недоступен")
        elif result["error"] != 0:
            update.message.reply_text("По вашему запросу ничего не найдено")
        else:
            reply_kwargs = make_search_reply(result["cars"], plate_number)
            update.message.reply_photo(**reply_kwargs)


def on_search_paginate(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    plate_number, page = data.split("-")
    page = int(page)
    result = get_license_plate(plate_number)
    if not result:
        query.reply_text("Сервис временно недоступен")
    elif result["error"] != 0:
        query.reply_text("По вашему запросу ничего не найдено")
    else:
        reply_kwargs = make_search_reply(result["cars"], plate_number, page)
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
