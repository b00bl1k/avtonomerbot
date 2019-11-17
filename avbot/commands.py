import logging
from telegram import Update
from telegram.ext import (
    CallbackContext, CommandHandler, Filters, MessageHandler)
from utils import UnderscoredCommandHandler

logger = logging.getLogger()


def on_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Для поиска отправьте номер в формате а123аа123."
    )


def on_help(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Бот для поиска по сайту avto-nomer.ru"
    )


def on_search_query(update: Update, context: CallbackContext):
    query = update.message.text
    logger.info(query)


def on_show_plate(update: Update, context: CallbackContext):
    logger.info(context.args)


def on_error(update: Update, context: CallbackContext):
    logger.error(f"Update '{update}' caused error '{context.error}'")


def register_commands(dispatcher):
    dispatcher.add_handler(CommandHandler("start", on_start))
    dispatcher.add_handler(CommandHandler("help", on_help))
    dispatcher.add_handler(MessageHandler(Filters.text, on_search_query))
    dispatcher.add_handler(UnderscoredCommandHandler("show", on_show_plate))
    dispatcher.add_error_handler(on_error)
