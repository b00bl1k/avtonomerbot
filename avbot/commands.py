from datetime import timedelta
from dateutil.parser import parse
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


@cache.cached_func(timedelta(minutes=30))
def get_series_info(series_number):
    return avtonomer.get_series(series_number)


def ensure_user_created(telegram_id, from_user):
    return db.get_or_create_user(
        telegram_id, from_user.first_name, from_user.last_name,
        from_user.username, from_user.language_code
    )


def get_car_caption(cars, search_query, page):
    car = cars[page]
    url = car["photo"]["link"].replace("http", "https")
    datetime = parse(car["date"])
    date = datetime.date().strftime("%d.%m.%Y")
    plate = avtonomer.translate_to_cyrillic(search_query.query_text)
    return (
        f"{plate} [{page + 1}/{len(cars)}] {date}\n"
        f"{car['make']} {car['model']}\n"
        f"{url}"
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
    update.message.reply_markdown(
        "Для поиска отправьте номер в формате `а123аа777` или `ааа777`"
    )


def on_help(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Бот для поиска по сайту avto-nomer.ru"
    )


def search_license_plate(update: Update, user, plate_number):
    search_query = db.add_search_query(user, plate_number)
    result = get_license_plate(plate_number)
    if not result:
        update.message.reply_text("Сервис временно недоступен", quote=True)
    elif result["error"] != 0:
        update.message.reply_text(
            "По вашему запросу ничего не найдено", quote=True
        )
    else:
        page = 0
        cars = result["cars"]
        car = cars[page]
        photo, key = avtonomer.get_car_photo(car)
        logger.info(f"{photo} {key}")
        message = update.message.reply_photo(
            photo=photo,
            caption=get_car_caption(cars, search_query, page),
            reply_markup=get_car_reply_markup(cars, search_query, page),
            quote=True,
        )
        if key:
            avtonomer.cache_car_photo(key, message.photo[-1].file_id)


def show_series_info(update: Update, user, series_number):
    db.add_search_query(user, series_number)
    result = get_series_info(series_number)
    if result is False:
        update.message.reply_text("Сервис временно недоступен", quote=True)
    elif result is not None:
        logger.info(f"{series_number} {result}")
        if result == 0:
            update.message.reply_markdown(
                f"В серии `{series_number}` пока нет ни одного номера",
                quote=True,
            )
        else:
            update.message.reply_markdown(
                f"Количество фотографий в серии `{series_number}`: {result}",
                quote=True,
            )
    else:
        update.message.reply_text(
            "Во время запроса произошла ошибка", quote=True,
        )


def on_search_query(update: Update, context: CallbackContext):
    if update.message:
        telegram_id = update.message.chat.id
        user = ensure_user_created(telegram_id, update.message.from_user)
        query = avtonomer.translate_to_latin(update.message.text)
        if avtonomer.validate_plate_number(query):
            search_license_plate(update, user, query)
        elif avtonomer.validate_plate_series(query):
            show_series_info(update, user, query)
        else:
            update.message.reply_text(
                "Некорректный запрос. Введите номер в формате `а123аа777` или `ааа777`.",
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
    else:
        db.add_inline_query(search_query, page_str)
        result = get_license_plate(search_query.query_text)
        if result and result["error"] == 0:
            cars = result["cars"]
            car = cars[page]
            photo, key = avtonomer.get_car_photo(car)
            logger.info(f"{photo} {key}")
            caption = get_car_caption(cars, search_query, page)
            message = context.bot.edit_message_media(
                media=InputMediaPhoto(photo, caption=caption),
                reply_markup=get_car_reply_markup(cars, search_query, page),
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
            )
            if key:
                avtonomer.cache_car_photo(key, message.photo[-1].file_id)


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
