import logging
from telegram.ext import Updater

import settings
import i18n
from commands import register_commands

logger = logging.getLogger(__name__)
updater = Updater(
    token=settings.BOT_TOKEN,
    request_kwargs=settings.REQUEST_KWARGS,
    use_context=True,
)


def main():
    i18n.load_translations("locale")
    register_commands(updater.dispatcher)
    if settings.WEBHOOK_URL:
        updater.start_webhook(
            listen=settings.WEBHOOK_HOST,
            port=settings.WEBHOOK_PORT,
            url_path=settings.WEBHOOK_PATH,
            webhook_url=settings.WEBHOOK_URL,
        )
        logger.info("listen on {}:{}".format(
            settings.WEBHOOK_HOST, settings.WEBHOOK_PORT
        ))
    else:
        updater.bot.set_webhook()
        updater.start_polling(timeout=10)
        logger.info("started")
    updater.idle()


if __name__ == "__main__":
    main()
