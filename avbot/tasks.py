import logging
from datetime import timedelta
from functools import wraps

import telegram
from celery import Celery, Task
from requests.exceptions import RequestException

from avbot import avtonomer, cache, db, settings, vininfo
from avbot.i18n import setup_locale

PHOTO_NOT_FOUND = "assets/not-found.png"
TASKS_TIME_LIMIT = 15

app = Celery("avbot", broker=settings.CELERY_BROKER_URL)
bot = telegram.Bot(token=settings.BOT_TOKEN)
logger = logging.getLogger(__name__)


def use_translation(fun):
    @wraps(fun)
    def _inner(*args, **kwargs):
        setup_locale(kwargs.pop("language", None))
        return fun(*args, **kwargs)
    return _inner


def get_car_caption(car, plate, page, count):
    date = car.date.strftime("%d.%m.%Y")
    plate = plate.upper().replace(" ", "")
    return (
        f"{plate} {date}\n"
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
            (
                "Error has occurred, try again later / "
                "Произошла ошибка, попробуйте ещё раз"
            ),
            reply_to_message_id=args[1],
        )


@app.task(
    base=TelegramTask,
    bind=True,
    autoretry_for=(RequestException, ),
    retry_kwargs={"max_retries": 2},
    default_retry_delay=2,
    soft_time_limit=TASKS_TIME_LIMIT,
)
@use_translation
def an_paginated_search(
    self, chat_id, message_id, search_query_id, page=0, edit=False
):
    search_query = db.get_search_query(search_query_id)
    lp_num = search_query.query_text
    lp_type = search_query.num_type

    from avbot.plate_formats import get_plate_format_by_type
    plate_format = get_plate_format_by_type(lp_type)
    cache_key = f"an_paginated_search-{lp_type}-{lp_num}"

    result = cache.get(cache_key)
    if not result:
        result = plate_format.search(lp_num)

    if not result:
        logger.warning(f"No data for query {lp_num} {lp_type}")
        bot.send_message(
            chat_id, plate_format.msg_no_data(),
            reply_to_message_id=message_id,
        )
        return

    if not result.total_results:
        bot.send_message(
            chat_id, plate_format.msg_no_results(lp_num),
            reply_to_message_id=message_id,
        )
        return

    cache.add(cache_key, result, timedelta(minutes=5))

    car = result.cars[page]
    cars_count = len(result.cars)
    cache_key_photo = f"avtonomer.load_photo({car.thumb_url})"

    file_id = cache.get(cache_key_photo)
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
        cache.add(
            cache_key_photo,
            message.photo[-1].file_id, timedelta(minutes=30),
        )


@app.task(
    base=TelegramTask,
    bind=True,
    autoretry_for=(RequestException, ),
    retry_kwargs={"max_retries": 2},
    default_retry_delay=2,
    soft_time_limit=TASKS_TIME_LIMIT,
)
@use_translation
def an_listed_search(self, chat_id, message_id, search_query_id):
    search_query = db.get_search_query(search_query_id)
    lp_num = search_query.query_text
    lp_type = search_query.num_type

    from avbot.plate_formats import get_plate_format_by_type
    plate_format = get_plate_format_by_type(lp_type)

    cache_key = f"an_listed_search-{lp_type}-{lp_num}"

    result = cache.get(cache_key)
    if not result:
        result = plate_format.search(lp_num)

    if result is None:
        logger.warning(f"No data for query {lp_type} {lp_num}")
        bot.send_message(
            chat_id, plate_format.msg_no_data(),
            reply_to_message_id=message_id,
        )
        return

    cache.add(cache_key, result, timedelta(minutes=5))

    message = (
        plate_format.msg_with_results(lp_num, result)
        if result.total_results > 0
        else plate_format.msg_no_results(lp_num)
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
    soft_time_limit=TASKS_TIME_LIMIT,
)
@use_translation
def vin_get_info(self, chat_id, message_id, vin, user_id):
    result = vininfo.get_vin_info(vin)
    if not result:
        if settings.FWD_CHAT_ID:
            msg = bot.forward_message(settings.FWD_CHAT_ID, chat_id, message_id)
            key = f"forwarding-{msg.message_id}"
            cache.add(key, message_id, time=timedelta(minutes=60))
    else:
        user = db.get_user_by_id(user_id)
        db.add_search_query(user, vin, "vin")
        message = vininfo.format_msg(result)
        bot.send_message(
            chat_id,
            message,
            reply_to_message_id=message_id,
        )
