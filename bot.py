import telebot
from settings import TOKEN
import patterns
from telebot import types
import datetime
import telegram
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          RegexHandler, Updater, Filters)

bot = telebot.TeleBot(TOKEN)

def start(update, context):
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + patterns.start_text
    update.message.reply_text(msg)


def help(update, context):
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + patterns.help_text
    update.message.reply_text(msg)


def tutorial(update, context):
    msg =  'Trust in me, ' + str(update.message.from_user.first_name) + patterns.tutorial_text
    update.message.reply_text(msg)

def new(update,context):
    now = datetime.datetime.now()
    msg =  'Now, ' + str(now)
    update.message.reply_text(msg)

def set(update,context):
    full_message = str(update.message.text)
    now = datetime.datetime.now()
    msg = 'Now, ' + str(now) + " " + full_message
    update.message.reply_text(msg)



def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("tutorial", tutorial))
    dp.add_handler(CommandHandler("new", new))
    dp.add_handler(CommandHandler("set", set))
    # dp.add_handler(CommandHandler("all", all))
    # dp.add_handler(ConversationHandler(
    #     entry_points=[CommandHandler("start", start)]))
        # states={CHOOSING: [MessageHandler(Filters.regex(r"^/\d+(@shimekiribot)?$"),
        #                                   remove_deadline_by_index)]},

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

