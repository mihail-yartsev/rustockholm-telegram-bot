import logging
import os
import random
import sys

from telegram.ext import Updater, CommandHandler,  MessageHandler, Filters
import pymongo
import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Filters, Updater, MessageHandler, CommandHandler, CallbackQueryHandler
from random import shuffle

#MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
#MONGO_USER = os.getenv("MONGO_USER")
#MONGO_HOST = os.getenv("MONGO_HOST")
#
#client = pymongo.MongoClient(f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/admin?retryWrites=true&w=majority")
#actions_db = client.actions


# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")

if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error("No MODE specified!")
    sys.exit(1)


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Привет. Я - акула-вахтер! Рад знакомству!.")


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Доступные команды: \n\n/id')


def id(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text(update.effective_chat.id)


def hodor(update, context):
    try:
        for new_member in update.message.new_chat_members:
            callback_id = str(new_member.id)
            context.bot.restrict_chat_member(
                int(os.environ['CHAT_ID']),
                new_member.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False)
            )

            keyboard_items = [
                InlineKeyboardButton("🥩", callback_data=callback_id + ',steak'),
                InlineKeyboardButton("🥝", callback_data=callback_id + ',kiwi'),
                InlineKeyboardButton("🥛", callback_data=callback_id + ',milk'),
                InlineKeyboardButton("🥓", callback_data=callback_id + ',bacon'),
                InlineKeyboardButton("🥥", callback_data=callback_id + ',coconut'),
                InlineKeyboardButton("🍩", callback_data=callback_id + ',donut'),
                InlineKeyboardButton("🌮", callback_data=callback_id + ',taco'),
                InlineKeyboardButton("🍕", callback_data=callback_id + ',pizza'),
                InlineKeyboardButton("🥗", callback_data=callback_id + ',salad'),
                InlineKeyboardButton("🍌", callback_data=callback_id + ',banana'),
                InlineKeyboardButton("🌰", callback_data=callback_id + ',chestnut'),
                InlineKeyboardButton("🍭", callback_data=callback_id + ',lollipop'),
                InlineKeyboardButton("🥑", callback_data=callback_id + ',avocado'),
                InlineKeyboardButton("🍗", callback_data=callback_id + ',chicken'),
                InlineKeyboardButton("🥪", callback_data=callback_id + ',sandwich'),
                InlineKeyboardButton("🥒", callback_data=callback_id + ',cucumber')
            ]

            shuffle(keyboard_items)
            keyboard = []

            counter = 0
            for i in range(4):  # create a list with nested lists
                keyboard.append([])
                for n in range(4):
                    keyboard_item = keyboard_items[counter]
                    keyboard[i].append(keyboard_item)  # fills nested lists with data
                    counter += 1

            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text(
                'Привет, ' +
                new_member.first_name +
                ' и Добро Пожаловать! Простая формальность, прежде чем мы разрешим отправлять сообщения: Пожалуйста, докажи, что ты не робот, взяв себе напиток ниже. Спасибо!',
                reply_markup=reply_markup
            )
    except AttributeError:
        pass


def button(update, context):
    query = update.callback_query
    person_who_pushed_the_button = int(query.data.split(",")[0])
    print("Query user: " + str(query.from_user))
    print("Query data: " + str(query.data))

    if query.from_user.id == person_who_pushed_the_button:
        if 'milk' in query.data:
            context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id
            )
            context.bot.restrict_chat_member(
                int(os.environ['CHAT_ID']),
                person_who_pushed_the_button,
                permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True)
            )
        else:
            query.edit_message_text(text="🚨 Хм... Похоже здесь был пойман робот! 🚨")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    updater.dispatcher.add_handler(CommandHandler("id", id))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    updater.dispatcher.add_error_handler(error)

    updater.dispatcher.add_handler(MessageHandler(Filters.chat(int(os.environ['CHAT_ID'])), hodor))
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    run(updater)
