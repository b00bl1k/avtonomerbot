import logging

from telegram import (
    Update,
    ChatAction,
    InlineKeyboardButton,
    InlineKeyboardMarkup)
from telegram.ext import (
    CallbackContext, CommandHandler, Filters, MessageHandler,
    CallbackQueryHandler)

import avtonomer
import db
import settings
import tasks
from i18n import translations, get_current_lang, setup_locale, _, __

logger = logging.getLogger(__name__)

INPUT_FORMATS = __("""Russia:
• `ru05` — info about region
• `а123аа777` — vehicle plate
• `аа12377` — public transport plate
• `1234аа77` — motorcycle plate
• `ааа777` — info about vehicle plate series

Soviet Union:
• `а0069МО` — private vehicles

United States:
• `pa xxx` — info about Pennsylvania state plate series
• `oh xxx` — info about Ohio state plate series
• `nc xxx` — info about North Carolina state plate series
• `ny xxx` — info about New York state plate series""")

HELP = __("""Bot for searching on the platesmania.com website

Please input one of the following commands:

{info}""")

REPLIES = {}
VIN_LENGTH = 17


def ensure_user_created(telegram_id, from_user):
    return db.get_or_create_user(
        telegram_id, from_user.first_name, from_user.last_name,
        from_user.username, from_user.language_code
    )


def on_start_command(update: Update, context: CallbackContext):
    telegram_id = update.message.chat.id
    ensure_user_created(telegram_id, update.message.from_user)
    update.message.reply_markdown(HELP.format(info=INPUT_FORMATS))


def on_help_command(update: Update, context: CallbackContext):
    update.message.reply_markdown(HELP.format(info=INPUT_FORMATS))


def on_setlang_command(update: Update, context: CallbackContext):
    buttons = [
        [
            InlineKeyboardButton(
                tr.info()["language-team"],
                callback_data=f"setlang-{code}",
            )
        ]
        for code, tr in translations.items()
    ]
    markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(
        "Выберите язык / Choose language:",
        reply_markup=markup,
    )


def on_setlang_query(update: Update, context: CallbackContext):
    command, lang = update.callback_query.data.split("-")
    user = context.user_data.get("user")
    if lang in translations:
        user.language_code = lang
        db.session.commit()
        setup_locale(lang)
    update.callback_query.message.edit_text(
        _("Current language: {}").format(
            translations[user.language_code].info()["language-team"]
        ),
        reply_markup=None,
    )


def on_search_query(update: Update, context: CallbackContext):
    if update.message:
        context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        user = ensure_user_created(chat_id, update.message.from_user)
        query = update.message.text
        if query.startswith("/"):  # handle like normal request
            query = query[1:]

        ru_query = avtonomer.translate_to_latin(query)
        su_query = avtonomer.translate_to_cyr(query)
        lang = get_current_lang()

        if avtonomer.validate_ru_plate_number(ru_query):
            search_query = db.add_search_query(user, ru_query)
            tasks.search_license_plate.delay(
                chat_id, message_id, search_query.id, page=0, edit=False,
                language=lang)
        elif avtonomer.validate_ru_pt_plate_number(ru_query):
            ru_query = avtonomer.reformat_ru_pt_query(ru_query)
            search_query = db.add_search_query(user, ru_query, "ru-pt")
            tasks.search_license_plate.delay(
                chat_id, message_id, search_query.id, page=0, edit=False,
                language=lang)
        elif avtonomer.validate_ru_moto_plate_number(ru_query):
            search_query = db.add_search_query(user, ru_query, "ru-moto")
            tasks.search_license_plate.delay(
                chat_id, message_id, search_query.id, page=0, edit=False,
                language=lang)
        elif avtonomer.validate_su_plate_number(su_query):
            search_query = db.add_search_query(user, su_query, "su")
            tasks.search_license_plate.delay(
                chat_id, message_id, search_query.id, page=0, edit=False,
                language=lang)
        elif avtonomer.validate_ru_plate_series(ru_query):
            search_query = db.add_search_query(user, ru_query)
            tasks.get_series_ru.delay(
                chat_id, message_id, search_query.id,
                language=lang)
        elif avtonomer.validate_us_plate_series(query):
            search_query = db.add_search_query(user, query, "us")
            tasks.get_series_us.delay(
                chat_id, message_id, search_query.id,
                language=lang)
        elif avtonomer.validate_ru_region(query):
            search_query = db.add_search_query(user, query)
            tasks.get_ru_region.delay(
                chat_id, message_id, search_query.id,
                language=lang)
        else:
            is_vin = (len(query) == VIN_LENGTH)
            if settings.FWD_CHAT_ID:
                msg = update.message.forward(settings.FWD_CHAT_ID)
                if is_vin:
                    REPLIES.update({msg.message_id: update.message.message_id})
            if not is_vin:
                update.message.reply_markdown(
                    _("Invalid request. Please input:\n{}")
                    .format(INPUT_FORMATS),
                    quote=True,
                )


def on_query_callback(update: Update, context: CallbackContext):
    command, arg = update.callback_query.data.split("-")
    if command == "setlang":
        on_setlang_query(update, context)
    else:
        on_search_paginate(update, context)


def on_search_paginate(update: Update, context: CallbackContext):
    query = update.callback_query
    search_query_id, page_str = query.data.split("-")
    page = int(page_str)
    search_query = db.get_search_query(int(search_query_id))
    if not search_query:
        logger.warning("Invalid search query id %s", search_query_id)
        query.message.reply_text(
            _("Something went wrong, please try again.")
        )
        return

    db.add_inline_query(search_query, page_str)
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    lang = get_current_lang()
    tasks.search_license_plate.delay(
        chat_id, message_id, search_query.id, page=page, edit=True,
        language=lang)


def on_unsupported_msg(update: Update, context: CallbackContext):
    if settings.FWD_CHAT_ID:
        update.message.forward(settings.FWD_CHAT_ID)
    update.message.reply_markdown(
        _("Unsupported request. Please input:\n{}")
        .format(INPUT_FORMATS),
        quote=True,
    )


def on_reply_msg(update: Update, context: CallbackContext):
    if not settings.FWD_CHAT_ID:
        return
    if update.message.chat.id != int(settings.FWD_CHAT_ID):
        logger.warning("unknown replied user")
        return
    if update.message.reply_to_message:
        replied_id = update.message.reply_to_message.message_id
        original_message_id = REPLIES.pop(replied_id, None)
        if original_message_id:
            context.bot.send_message(
                chat_id=update.message.reply_to_message.forward_from.id,
                reply_to_message_id=original_message_id,
                text=update.message.text,
            )
        else:
            logger.warning("original message not found")
    else:
        logger.warning("no reply {}".format(update.message.reply_to_message))


def on_error(update: Update, context: CallbackContext):
    logger.error("update cause error", exc_info=context.error, extra={
        "update": update.to_dict() if update else None,
    })


def on_preprocess_update(update: Update, context: CallbackContext):
    lang = "en"
    user = None

    if update.message:
        msg = update.message
        user = ensure_user_created(msg.chat.id, msg.from_user)
    elif update.callback_query and update.callback_query.message:
        msg = update.callback_query.message
        user = db.get_user(msg.chat.id)

    if user:
        context.user_data["user"] = user
        lang = user.language_code

    setup_locale(lang)


def register_commands(dispatcher):
    dispatcher.add_handler(MessageHandler(Filters.update, on_preprocess_update))
    dispatcher.add_handler(CommandHandler("start", on_start_command), 1)
    dispatcher.add_handler(CommandHandler("help", on_help_command), 1)
    dispatcher.add_handler(CommandHandler("setlang", on_setlang_command), 1)
    dispatcher.add_handler(MessageHandler(Filters.reply, on_reply_msg), 1)
    dispatcher.add_handler(MessageHandler(Filters.text, on_search_query), 1)
    dispatcher.add_handler(MessageHandler(Filters.update, on_unsupported_msg), 1)
    dispatcher.add_handler(CallbackQueryHandler(on_query_callback), 1)
    dispatcher.add_error_handler(on_error)
