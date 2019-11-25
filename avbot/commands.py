from datetime import timedelta
from dateutil.parser import parse
import logging
import requests
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto)
from telegram.ext import (
    CallbackContext, CommandHandler, Filters, MessageHandler,
    CallbackQueryHandler)

import avtonomer
import cache
import db
import settings

PHOTO_NOT_FOUND = "assets/not-found.png"
logger = logging.getLogger(__name__)


@cache.cached_func(timedelta(minutes=10))
def get_license_plate(plate_number):
    return avtonomer.search(plate_number, settings.AN_KEY)


def ensure_user_created(telegram_id, from_user):
    return db.get_or_create_user(
        telegram_id, from_user.first_name, from_user.last_name,
        from_user.username, from_user.language_code
    )


def get_car_photo(car):
    url = car["photo"]["medium"]
    resp = requests.head(url)
    if resp.status_code != 404:
        return url, False
    file_id = cache.get(PHOTO_NOT_FOUND)
    if file_id:
        return file_id, False
    return open(PHOTO_NOT_FOUND, "rb"), True


def cache_not_found_photo(not_found_file_id):
    cache.add(PHOTO_NOT_FOUND, not_found_file_id)


def get_car_caption(cars, search_query, page):
    car = cars[page]
    datetime = parse(car["date"])
    date = datetime.date().strftime("%d.%m.%Y")
    plate = avtonomer.translate_to_cyrillic(search_query.query_text)
    return (
        f"{plate} [{page + 1}/{len(cars)}] {date}\n"
        f"{car['make']} {car['model']}\n"
        f"{car['photo']['link']}"
    )


def get_car_reply_markup(cars, search_query, page):
    cars_count = len(cars)
    buttons = [[
        InlineKeyboardButton(
            f"{i + 1}",
            callback_data=f"{search_query.id}-{i}"
        )
        for i in range(cars_count)
        if i != page
    ]]
    return (
        InlineKeyboardMarkup(buttons)
        if cars_count > 1
        else None
    )


def on_start(update: Update, context: CallbackContext):
    telegram_id = update.message.chat.id
    ensure_user_created(telegram_id, update.message.from_user)
    update.message.reply_text(
        "Для поиска отправьте номер в формате а123аа123"
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
            page = 0
            cars = result["cars"]
            car = cars[page]
            photo, add_to_cache = get_car_photo(car)
            logger.info(f"{photo} {add_to_cache}")
            message = update.message.reply_photo(
                photo=photo,
                caption=get_car_caption(cars, search_query, page),
                reply_markup=get_car_reply_markup(cars, search_query, page)
            )
            if add_to_cache:
                cache_not_found_photo(message.photo[-1].file_id)


def on_search_paginate(update: Update, context: CallbackContext):
    query = update.callback_query
    search_query_id, page_str = query.data.split("-")
    page = int(page_str)
    search_query = db.get_search_query(int(search_query_id))
    if not search_query:
        logger.warning("Invalid search query id %s", search_query_id)
        query.message.reply_text("Произошла ошибка. Введите номер повторно.")
    else:
        db.add_inline_query(search_query, page_str)
        result = get_license_plate(search_query.query_text)
        if result and result["error"] == 0:
            cars = result["cars"]
            car = cars[page]
            photo, add_to_cache = get_car_photo(car)
            logger.info(f"{photo} {add_to_cache}")
            caption = get_car_caption(cars, search_query, page)
            message = context.bot.edit_message_media(
                media=InputMediaPhoto(photo, caption=caption),
                reply_markup=get_car_reply_markup(cars, search_query, page),
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
            )
            if add_to_cache:
                cache_not_found_photo(message.photo[-1].file_id)


def on_error(update: Update, context: CallbackContext):
    logger.error(f"update cause error", exc_info=context.error, extra={
        "update": update.to_dict(),
    })


def register_commands(dispatcher):
    dispatcher.add_handler(CommandHandler("start", on_start))
    dispatcher.add_handler(CommandHandler("help", on_help))
    dispatcher.add_handler(MessageHandler(Filters.text, on_search_query))
    dispatcher.add_handler(CallbackQueryHandler(on_search_paginate))
    dispatcher.add_error_handler(on_error)
