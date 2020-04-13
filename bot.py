from settings import TOKEN
import patterns
import datetime
import telegramcalendar
import logging
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton)
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          RegexHandler, Updater, Filters)


def start(update, context):
    menu_keyboard = [['/help'], ['/new']]
    menu_markup = ReplyKeyboardMarkup(menu_keyboard, one_time_keyboard=True, resize_keyboard=True)
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + patterns.start_text
    update.message.reply_text(msg, menu_markup)


def help(update, context):
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + patterns.help_text
    update.message.reply_text(msg)


def tutorial(update, context):
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + patterns.tutorial_text
    update.message.reply_text(msg)


def new(update, context):
    now = datetime.datetime.now()
    msg = 'Now, ' + str(now)
    update.message.reply_text(msg)


def set_task(update, context):
    msg = 'Hmm... Ok, I get it. Do you need any deadline?'
    keyboard = [[InlineKeyboardButton("Yeah, set up, please", callback_data='1'),
                 InlineKeyboardButton("No, I have my mind", callback_data='2')], ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(msg, reply_markup=reply_markup)


def okornot(update, context):
    query = update.callback_query
    action = query.data
    if action == "1":
        now = datetime.datetime.now()
        calendar_markup = telegramcalendar.create_calendar(now.year, now.month)
        context.bot.edit_message_text(text='Ok, please set deadline',
                                      chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      reply_markup=calendar_markup)


    elif action == "2":
        context.bot.edit_message_text(text='Ok, you are very confidence',
                                      chat_id=query.message.chat_id,
                                      message_id=query.message.message_id
                                      )


def calendar_handler(update, context):
    now = datetime.datetime.now()
    update.message.reply_text("Please select a date: ",
                              reply_markup=telegramcalendar.create_calendar(now.year, now.month))


def inline_handler(update, context):
    context.bot.send_message()
    selected, date = telegramcalendar.process_calendar_selection(context, update)
    if selected:
        update.message.reply_text(chat_id=update.callback_query.from_user.id,
                                  text="You selected %s" % (date.strftime("%d/%m/%Y")),
                                  reply_markup=ReplyKeyboardRemove())




def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set", set_task))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("tutorial", tutorial))
    dp.add_handler(CommandHandler("new", new))
    dp.add_handler(CommandHandler("calendar", calendar_handler))
    dp.add_handler(CallbackQueryHandler(okornot))
    dp.add_handler(CallbackQueryHandler(inline_handler))
    # dp.add_handler(CommandHandler("all", all))
    # dp.add_handler(ConversationHandler(
    #     entry_points=[CommandHandler("start", start)]))
    # states={CHOOSING: [MessageHandler(Filters.regex(r"^/\d+(@shimekiribot)?$"),
    #                                   remove_deadline_by_index)]},

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
