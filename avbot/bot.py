import logging
from telegram.ext import Updater
import settings
from commands import register_commands

logger = logging.getLogger(__name__)


def main():
    updater = Updater(
        token=settings.BOT_TOKEN,
        request_kwargs=settings.REQUEST_KWARGS,
        use_context=True,
    )
    register_commands(updater.dispatcher)
    updater.bot.set_webhook()
    logger.info("started")
    updater.start_polling(timeout=10)
    updater.idle()


if __name__ == "__main__":
    main()
