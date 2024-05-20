import logging
import re

from telegram import (
    Update,
    ChatAction,
    InlineKeyboardButton,
    InlineKeyboardMarkup)
from telegram.ext import (
    CallbackContext, CommandHandler, Filters, MessageHandler,
    CallbackQueryHandler)

from avbot import cache, db, models, settings, tasks
from avbot.i18n import translations, get_current_lang, setup_locale, _, __
from avbot.plate_formats import PLATE_FORMATS, get_plate_format_by_type
from avbot.utils import validate_vin

logger = logging.getLogger(__name__)

INTRO = __("""Welcome to @avtonomerbot

Input /help for the detailed information.
Type /setlang to change language.""")

HELP = __("""Bot for searching on the platesmania.com website

Please input one of the following commands:
""")


def ensure_user_created(telegram_id, from_user):
    return db.get_or_create_user(
        telegram_id, from_user.first_name, from_user.last_name,
        from_user.username, from_user.language_code
    )


def on_start_command(update: Update, context: CallbackContext):
    update.message.reply_markdown(str(INTRO))


def on_help_command(update: Update, context: CallbackContext):
    message = [str(HELP)]
    for country_code, plates in PLATE_FORMATS.items():
        message.append("*{}*".format(models.COUNTRY_LABELS[country_code]))
        for plate in plates:
            message.append("• `{}` — {}".format(
                plate.example,
                plate.description,
            ))
        message.append("")
    update.message.reply_markdown("\n".join(message))


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


def on_setlang_query(update: Update, context: CallbackContext, lang: str):
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


def on_setcountry_command(update: Update, context: CallbackContext):
    buttons = [
        [
            InlineKeyboardButton(
                str(label),
                callback_data=f"setcountry-{code}",
            )
        ]
        for code, label in models.COUNTRY_LABELS.items()
    ]
    markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(
        _("Choose country:"),
        reply_markup=markup,
    )


def on_setcountry_query(update: Update, context: CallbackContext, arg: str):
    country = int(arg)
    user = context.user_data.get("user")
    if country in models.COUNTRY_LABELS:
        user.country = country
        db.session.commit()
    update.callback_query.message.edit_text(
        _("Current country: {}").format(
            models.COUNTRY_LABELS[country]
        ),
        reply_markup=None,
    )


def on_vin_command(update: Update, context: CallbackContext):
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    user = context.user_data.get("user")
    query = update.message.text
    if not validate_vin(query):
        update.message.reply_text(
            _("VIN contains invalid characters"),
            quote=True,
        )
    else:
        tasks.vin_get_info.delay(
            chat_id, message_id, query, user.id, language=get_current_lang())


def on_search_query(update: Update, context: CallbackContext):
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    user = context.user_data.get("user")
    query = update.message.text
    if query.startswith("/"):  # handle like normal request
        query = query[1:]

    found = []
    for country_code, plates in PLATE_FORMATS.items():
        for plate in plates:
            validated = plate.validate(query)
            if validated:
                found.append((validated, country_code, plate))

    found_count = len(found)
    # TODO reduce results using user.country_code
    if found_count == 0:
        update.message.reply_text(
            _("Invalid request, try /help command"),
            quote=True,
        )
    elif found_count == 1:
        (validated_query, country_code, plate) = found[0]
        search_query = db.add_search_query(
            user, validated_query, plate.num_type)
        plate.task.delay(
            chat_id, message_id, search_query.id,
            language=get_current_lang())
        context.bot.send_chat_action(
            update.effective_user.id, ChatAction.TYPING)
    else:
        buttons = [
            [
                InlineKeyboardButton(
                    "{} - {}".format(
                        models.COUNTRY_LABELS[country_code],
                        plate.description,
                    ),
                    callback_data="specifyplate-{}/{}".format(
                        plate.num_type,
                        validated_query.encode("utf-8").hex(),
                    ),
                )
            ]
            for validated_query, country_code, plate in found
        ]
        markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(
            _("Request: {}\nSpecify type of the plate:").format(query),
            reply_markup=markup,
        )


def on_specifyplate_query(update: Update, context: CallbackContext, arg: str):
    num_type, query = arg.split("/")
    validated_query = bytes.fromhex(query).decode("utf-8")
    plate = get_plate_format_by_type(num_type)
    user = context.user_data.get("user")
    new_message = _("Request: {}\nSpecify type of the plate:").format(
        validated_query,
    )
    update.callback_query.message.edit_text(
        "{} {}".format(new_message, plate.description),
        reply_markup=None,
    )
    search_query = db.add_search_query(
        user, validated_query, plate.num_type)
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    plate.task.delay(
        chat_id, message_id, search_query.id,
        language=get_current_lang())
    context.bot.send_chat_action(
        update.effective_user.id, ChatAction.TYPING)


def on_query_callback(update: Update, context: CallbackContext):
    command, arg = update.callback_query.data.split("-", maxsplit=1)
    if command == "setlang":
        on_setlang_query(update, context, arg)
    elif command == "setcountry":
        on_setcountry_query(update, context, arg)
    elif command == "specifyplate":
        on_specifyplate_query(update, context, arg)
    else:
        on_search_paginate(update, context)


def on_search_paginate(update: Update, context: CallbackContext):
    query = update.callback_query
    search_query_id, page_str = query.data.split("-", maxsplit=1)
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
    plate_format = get_plate_format_by_type(search_query.num_type)
    plate_format.task.delay(
        chat_id, message_id, search_query.id, page=page, edit=True,
        language=lang)


def on_unsupported_msg(update: Update, context: CallbackContext):
    if settings.FWD_CHAT_ID:
        update.message.forward(settings.FWD_CHAT_ID)
    update.message.reply_markdown(
        _("Unsupported request. Use /help"),
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
        original_message_id = cache.get(f"forwarding-{replied_id}")
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


def register_commands(dp):
    dp.add_handler(MessageHandler(Filters.update, on_preprocess_update), 0)
    dp.add_handler(CallbackQueryHandler(on_preprocess_update), 0)
    dp.add_handler(CommandHandler("start", on_start_command), 1)
    dp.add_handler(MessageHandler(Filters.regex(
        re.compile(r"help", re.IGNORECASE)
    ), on_help_command), 1)
    dp.add_handler(MessageHandler(Filters.regex(
        re.compile(r"setlang", re.IGNORECASE)
    ), on_setlang_command), 1)
    dp.add_handler(MessageHandler(Filters.regex(
        re.compile(r"setcountry", re.IGNORECASE)
    ), on_setcountry_command), 1)
    dp.add_handler(MessageHandler(Filters.regex(
        re.compile(r"[0-9a-z]{17}", re.IGNORECASE)
    ), on_vin_command), 1)
    dp.add_handler(MessageHandler(Filters.reply, on_reply_msg), 1)
    dp.add_handler(MessageHandler(Filters.text, on_search_query), 1)
    dp.add_handler(MessageHandler(Filters.update, on_unsupported_msg), 1)
    dp.add_handler(CallbackQueryHandler(on_query_callback), 1)
    dp.add_error_handler(on_error)
