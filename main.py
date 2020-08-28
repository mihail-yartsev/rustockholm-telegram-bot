import logging
import os
import random
from random import shuffle
import sys

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    Filters,
    Updater,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler
)

# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
BAN_WAITING_TIME = int(os.getenv("BAN_WAITING_TIME", 10))

if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook(
            f"https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}"
        )
else:
    logger.error("No MODE specified!")
    sys.exit(1)


# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Привет. Я - Сторож Карл! Рад знакомству!.")


def help(update, context):
    """Send a message when the command /help is issued."""
    #update.message.reply_text("Доступные команды: \n\n/id")
    update.message.reply_text("Прости, лично я пока ничем не готов помочь...")


def guard(update, context):
    try:
        for new_member in update.message.new_chat_members:
            callback_id = str(new_member.id)
            context.bot.restrict_chat_member(
                int(os.environ["CHAT_ID"]),
                new_member.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False)
            )

            keyboard = [[
                InlineKeyboardButton("🍕", callback_data=callback_id + ",pizza"),
            ]]

            reply_markup = InlineKeyboardMarkup(keyboard)

            reply_message = update.message.reply_text(
                "Привет, " +
                new_member.first_name + (
                ", и добро пожаловать! В закрепленном сообщении наверху"
                " есть много полезной информации, а также вопросы, с помощью "
                "которых вы можете представиться сообществу. Не забудьте это "
                "сделать!\n"
                "Но прежде всего, покажите что вы не робот,"
                " нажав на иконку пиццы ниже :)"
                ),
                reply_markup=reply_markup,
                disable_notification=True
            )
            job_context = {
                "user_id": callback_id,
                "chat_id": update.effective_chat.id,
                "message_id": reply_message.message_id,
                "welcome_message_id": update.message.message_id,
                "new_member": f"{new_member.first_name} {new_member.last_name}",
            }
            logger.info(f"running callback for {job_context}")
            logger.info(f"message id {update.message.message_id}")
            context.job_queue.run_once(
                job_callback,
                BAN_WAITING_TIME,
                context=job_context
            )

    except AttributeError:
        pass


def ban_user(bot, user_id, chat_id):
    bot.kickChatMember(chat_id, user_id)


def unban_user(bot, user_id, chat_id):
    bot.unbanChatMember(chat_id, user_id)


def kick_user(bot, user_id, chat_id):
    logger.info(f"user {user_id} kicked")
    ban_user(bot, user_id, chat_id)
    unban_user(bot, user_id, chat_id)


def guard_button(update, context):
    query = update.callback_query
    person_who_pushed_the_button = int(query.data.split(",")[0])
    print("Query user: " + str(query.from_user))
    print("Query data: " + str(query.data))

    if query.from_user.id == person_who_pushed_the_button:
        if "pizza" in query.data:
            logger.info(update.callback_query.message.message_id)
            context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id
            )
            context.bot.restrict_chat_member(
                int(os.environ["CHAT_ID"]),
                person_who_pushed_the_button,
                permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=False,
                can_pin_messages=False,
                can_send_pools=True,
                can_invite_users=True,
                can_change_info=False,
                can_add_web_page_previews=True)
            )
        else:
            query.edit_message_text(
                text="🚨 Хм... Похоже здесь был пойман робот! 🚨"
            )
            # here we need to kick user


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning("Update '%s' caued error '%s'", update, context.error)



def job_callback(context):
    # here we are getting message that need to be deleted in button method
    # it's passed via context var
    # and trying to delete it.
    # in case if message is deleted, kicking user
    logger.info("processing callback")
    message_id: int = context.job.context.get("message_id")
    welcome_message_id: int = context.job.context.get("welcome_message_id")
    chat_id: int = context.job.context.get("chat_id")
    user_id: int = context.job.context.get("user_id")
    new_member: str = context.job.context.get("new_member")

    try:
        logger.info(f"processing user {new_member}")
        context.bot.delete_message(chat_id, message_id)
    except telegram.error.BadRequest as e:
        # in case if message is deleted, means user made some action
        # just skip
        logger.info(f"user {user_id} hasn't been kicked")
        pass
    else:
        kick_user(context.bot, user_id, chat_id)
        # print some message
        # log that bot kicked some user
        context.bot.delete_message(chat_id, welcome_message_id)
    finally:
        logger.info("job's done")


if __name__ == "__main__":
    logger.info("Starting bot")
    updater = Updater(TOKEN, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    updater.dispatcher.add_handler(CallbackQueryHandler(guard_button))

    updater.dispatcher.add_error_handler(error)

    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.chat(int(os.environ["CHAT_ID"])), guard
        )
    )
    run(updater)
