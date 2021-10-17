import logging
from datetime import timedelta

import telegram
from celery import Celery, Task
from requests.exceptions import RequestException

import avtonomer
import cache
import db
import settings

PHOTO_NOT_FOUND = "assets/not-found.png"

app = Celery("avbot", broker=settings.CELERY_BROKER_URL)
bot = telegram.Bot(token=settings.BOT_TOKEN)
logger = logging.getLogger(__name__)


def get_car_caption(car, plate, page, count):
    date = car.date.strftime("%d.%m.%Y")
    plate = avtonomer.translate_to_cyrillic(plate)
    return (
        f"{plate} [{page + 1}/{count}] {date}\n"
        f"{car.make} {car.model}\n"
        f"{car.page_url}"
    )


def get_car_reply_markup(cars_count, search_query_id, page):
    buttons = [[
        telegram.InlineKeyboardButton(
            f"{i + 1}",
            callback_data=f"{search_query_id}-{i}"
        )
        for i in range(cars_count)
        if i != page
    ]]
    return (
        telegram.InlineKeyboardMarkup(buttons)
        if cars_count > 1
        else None
    )


class TelegramTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        bot.send_message(
            args[0],
            "Произошла ошибка во время обработки запроса.",
            reply_to_message_id=args[1],
        )


@app.task(
    base=TelegramTask,
    bind=True,
    autoretry_for=(RequestException, ),
    retry_kwargs={"max_retries": 2},
    default_retry_delay=2,
)
def search_license_plate(self, chat_id, message_id, search_query_id, page, edit):
    search_query = db.get_search_query(search_query_id)
    lp_num = search_query.query_text
    lp_type = search_query.num_type
    key = f"avtonomer.search_{lp_type}({lp_num})"

    result = cache.get(key)
    if not result:
        if lp_type == "ru":
            result = avtonomer.search_ru(lp_num, settings.AN_KEY)
        else:
            result = avtonomer.search_su(lp_num)

    if not result:
        bot.send_message(
            chat_id, "По вашему запросу ничего не найдено",
            reply_to_message_id=message_id,
        )
        return

    cache.add(key, result, timedelta(minutes=5))

    car = result.cars[page]
    cars_count = len(result.cars)
    key = f"avtonomer.load_photo({car.thumb_url})"

    file_id = cache.get(key)
    if not file_id:
        photo = avtonomer.load_photo(car.thumb_url)
        if not photo:
            photo = open(PHOTO_NOT_FOUND, "rb")
    else:
        photo = file_id

    caption = get_car_caption(car, lp_num, page, cars_count)
    markup = get_car_reply_markup(cars_count, search_query_id, page)

    if edit:
        message = bot.edit_message_media(
            media=telegram.InputMediaPhoto(photo, caption=caption),
            reply_markup=markup,
            chat_id=chat_id,
            message_id=message_id,
        )
    else:
        message = bot.send_photo(
            chat_id, photo, caption,
            reply_to_message_id=message_id,
            reply_markup=markup,
        )

    if not file_id:
        cache.add(key, message.photo[-1].file_id, timedelta(minutes=30))


@app.task(
    base=TelegramTask,
    bind=True,
    autoretry_for=(RequestException, ),
    retry_kwargs={"max_retries": 2},
    default_retry_delay=2,
)
def get_series_ru(self, chat_id, message_id, search_query_id):
    search_query = db.get_search_query(search_query_id)
    series_number = search_query.query_text
    key = f"avtonomer.get_series_ru({series_number})"

    result = cache.get(key)
    if not result:
        result = avtonomer.get_series_ru(series_number)

    if result is None:
        logger.warning(f"Not data for query {series_number}")
        bot.send_message(
            chat_id, "Нет данных",
            reply_to_message_id=message_id,
        )
        return

    cache.add(key, result, timedelta(minutes=5))

    url = avtonomer.get_series_ru_url(series_number)
    series_number = avtonomer.translate_to_cyrillic(series_number)
    message = (
        f"В серии [{series_number}]({url}) пока нет ни одного номера"
        if result == 0
        else f"Количество фотографий в серии [{series_number}]({url}): {result}"
    )
    bot.send_message(
        chat_id,
        message,
        parse_mode="Markdown",
        reply_to_message_id=message_id,
    )

@app.task(
    base=TelegramTask,
    bind=True,
    autoretry_for=(RequestException, ),
    retry_kwargs={"max_retries": 2},
    default_retry_delay=2,
)
def get_series_us(self, chat_id, message_id, search_query_id):
    search_query = db.get_search_query(search_query_id)
    result = avtonomer.validate_us_plate_series(search_query.query_text)
    state, series_number = result.groups()
    key = f"avtonomer.get_series_us({state}, {series_number})"
    state_id, ctype_id = avtonomer.US_STATES_ID[state]

    result = cache.get(key)
    if not result:
        result = avtonomer.get_series_us(state_id, ctype_id, series_number)

    if result is None:
        logger.warning(f"Not data for query {series_number}")
        bot.send_message(
            chat_id, "Нет данных",
            reply_to_message_id=message_id,
        )
        return

    cache.add(key, result, timedelta(minutes=5))

    url = avtonomer.get_series_us_url(state_id, ctype_id, series_number)
    message = (
        f"В серии [{series_number}]({url}) штата `{state}` пока нет ни одного номера"
        if result == 0
        else f"Количество фотографий в серии [{series_number}]({url}) штата `{state}`: {result}"
    )
    bot.send_message(
        chat_id,
        message,
        parse_mode="Markdown",
        reply_to_message_id=message_id,
    )
