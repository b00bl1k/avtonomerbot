import logging
from telegram import Update, MessageEntity
from telegram.ext import CommandHandler, Updater

logger = logging.getLogger()


class UnderscoredCommandHandler(CommandHandler):

    def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:
            message = update.effective_message
            if (message.entities
                    and message.entities[0].type == MessageEntity.BOT_COMMAND
                    and message.entities[0].offset == 0):
                command = message.text[1:message.entities[0].length]
                args = command.split("_")
                command_name = args[0]
                args = args[1:]
                if command_name.lower() not in self.command:
                    return None

                filter_result = self.filters(update)
                if filter_result:
                    return args, filter_result
                else:
                    return False
