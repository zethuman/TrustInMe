import json
from functools import reduce
import settings
import patterns
import datetime
import telegramcalendar
import logging
from bson import ObjectId
from mongodb import mdb, search_or_save_user, search_or_save_task
import logging
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, ParseMode)
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          RegexHandler, Updater, Filters)


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log')


def start(bot, update):
    user = search_or_save_user(mdb, update.effective_user, update.message)
    print(user)
    reply_keyboard = [["Create Task", 'List All Tasks'], ["Help", "Tutorial"], ["Restart"]]
    msg = 'Trust in me, (poiled by Rakhat)' + str(update.message.from_user.first_name) + patterns.start_text
    update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(
        reply_keyboard,
        resize_keyboard=True))
    return GET_COMMAND


def add_task(bot, update):
    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text(
        "Please send me a tasks's title",
        reply_markup=reply_markup
    )
    return TASK_CREATE


def task_create(bot, update, user_data):
    user_data['task_title'] = update.message.text
    # user = search_or_save_user(mdb, update.effective_user, update.message)
    # task = search_user_task(mdb, user, user_data)
    # print(task)
    reply_keyboard = [["Yes", "No"]]
    update.message.reply_text(
        "Does the task have the deadline?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True)
    )
    return ADD_DEADLINE


def get_username(update):
    return update.effective_user.username


def get_tasks_list(user):
    tasks = mdb.tasks.find({'user_id': user.id}, {'task_title': 1,'deadline_data': 1, 'notification_date':1, '_id': 1})
    keyboard = [[InlineKeyboardButton(task['task_title'], callback_data=str(task['_id']))] for task in tasks]
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return keyboard_markup


def list_tasks(bot, update, user_data):
    user = update.message.from_user
    reply_markup = ReplyKeyboardRemove()
    message = update.message.reply_text(
        "Getting tasks...", reply_markup=reply_markup
    )
    message.reply_text(
         "Choose a task to view:", reply_markup=get_tasks_list(user))
    return TASK_VIEW


def no_deadline(bot, update):
    reply_keyboard = [["Yes", "No"]]
    update.message.reply_text("Ok, you are very confidence\n"
                              "Do you want to get notification?",
                              reply_markup=ReplyKeyboardMarkup(
                                  reply_keyboard,
                                  one_time_keyboard=True
                              )
                              )
    return ADD_NOTIFICATION


def calendar_handler(bot, update):
    update.message.reply_text("Please select a date: ",
                              reply_markup=telegramcalendar.create_calendar())
    return GET_DEADLINE


def deadline_handler(bot, update, user_data):
    selected, date = telegramcalendar.process_calendar_selection(bot, update)
    print(type(date))
    user_data['deadline_date'] = date
    user_data['updated_date'] = date
    print(date)
    reply_keyboard = [["Yes", "No"]]
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"""You selected {date}.
                     Do you want to get notification?""",
                     reply_markup=ReplyKeyboardMarkup(
                         reply_keyboard,
                         one_time_keyboard=True)
                     )
    return ADD_NOTIFICATION


def add_notification(bot, update, user_data):
    update.message.reply_text("Please select a date: ",
                              reply_markup=telegramcalendar.create_calendar())
    return GET_NOTIFICATION


def notification_handler(bot, update, user_data):
    selected, date = telegramcalendar.process_calendar_selection(bot, update)
    user_data.update(notification_date=date)
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"""You selected {date}.
                     Enter notification time in format 'HH:MM'""",
                     reply_markup=ReplyKeyboardRemove())
    return ADD_NOTIFICATION_TIME


def add_notification_date(bot, update, job_queue, user_data):
    notification_time = update.message.text
    notification_date = user_data["notification_date"]
    user_data['task_status'] = True
    try:
        hour, minutes = map(int, notification_time.split(":"))
        notification = datetime
    except ValueError:
        update.message.reply_text(
            "Please enter a valid time in format 'HH:MM'"
        )
        return None

    text = """\nResults: 
    <b>Task: </b> {task_title}
    <b>Deadline: </b> {deadline_date}
    <b>Notification date: </b> {notification_date}
    """.format(**user_data)
    update.message.reply_text(f"""Thanks! I'll send you a notification
        on your task on \n""" + text, parse_mode=ParseMode.HTML)
    user = search_or_save_user(mdb, update.effective_user, update.message)
    task = search_or_save_task(mdb, update.effective_user, user_data)
    # return ConversationHandler.END
    return RESTART


def task_view(bot, update, user_data):
    taskId = update.callback_query.data
    oid = ObjectId(taskId)
    user_data['oid'] = ObjectId(taskId)
    print(repr(oid))
    task = mdb.tasks.find_one({'_id': ObjectId(taskId)})
    print(task)
    reply_keyboard = [["Edit", "Delete"]]
    # title = task['task_title']
    # deadline = task['deadline_date']
    # notification = task['notification_date']
    if task['task_status'] == True:
        status = 'Undone'
    else:
        status = 'Done'
    # print(title, deadline)

    bot.send_message(chat_id=update.callback_query.from_user.id,
                         text=f"Task {task['task_title']}\n"
                         f"Due date: {task['deadline_date']}\nNotification: "
                         f"{task['notification_date']}\n"
                         f"Status: {status}",
                         reply_markup=ReplyKeyboardMarkup(
                             reply_keyboard,
                             one_time_keyboard=True, resize_keyboard= True)
                         )
    return SELECT_ACTION


def get_task_fields():
    doc = reduce( lambda all_keys, rec_keys: all_keys | set(rec_keys), map(lambda d: d.keys(), mdb.tasks.find({}, {'_id':0, 'user_id':0})), set() )
    for key in doc:
        print(key)
    keyboard = [[InlineKeyboardButton(name, callback_data=name)]
                for name in doc]
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return keyboard_markup


def list_edit_options(bot, update, user_data):
    update.message.reply_text(
        "Choose a property to edit:", reply_markup=get_task_fields())
    return GET_EDIT_ACTION


def get_edit_action(bot, update, user_data):
    field = update.callback_query.data
    user_data["edit"] = field
    keyboard = [['Done', 'Undone']]
    if field == 'task_title':
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text=f"Please, send a new value for the task`s title.")
    if field == 'task_status':
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text=f"Please, send a new value for the task`s status", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    elif field == 'deadline_date':
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text=f"Please, send a new value for the task`s deadline in format month/day/year h:m:s")
    elif field == 'notification_date':
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text=f"Please, send a new value for the task`s notification in format month/day/year h:m:s")
    return GET_NEW_VALUE



def edit_task(bot, update, user_data):
    field = user_data["edit"]
    oid = user_data['oid']
    if field == 'task_title':
        value = update.message.text
    elif field == 'task_status':
        handler = update.message.text
        if handler == 'Undone':
            value = True
        elif handler == 'Done':
            value = False
    elif field == 'deadline_date':
        datetime_str = update.message.text
        value = datetime.datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
    elif field == 'notification_date':
        datetime_str = update.message.text
        value = datetime.datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
    try:
        mdb.tasks.update_one({'_id': ObjectId(oid)},
                        {'$set': {field: value}})
    except ValueError:
        update.message.reply_text("Please send a valid value")
        return
    if field == 'task_title':
        update.message.reply_text(f"The task title is updated to {value}")
    if field == 'dateline_data':
        update.message.reply_text(f"The task deadline is updated to {value}")
    if field == 'notification_data':
        update.message.reply_text(f"The task deadline is updated to {value}")
    if field == 'task_status':
        update.message.reply_text(f"The task status is changed to {value}")
    user_data.clear()
    # return ConversationHandler.END
    return RESTART


def delete_task(bot, update, user_data):
    oid = user_data['oid']
    mdb.tasks.remove({'_id': ObjectId(oid)}, 1)
    user_data.clear()
    update.message.reply_text(
        f"The task is deleted.",
        reply_markup=ReplyKeyboardRemove()
    )
    # return ConversationHandler.END
    return RESTART

def cancel(bot, update):
    update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove()
    )


def say_goodbye(bot, update, user_data):
    user_data.clear()
    update.message.reply_text("Thank you! I hope we can talk again some day.")
    return ConversationHandler.END


def help(bot, update):
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + patterns.help_text
    update.message.reply_text(msg)


def tutorial(bot, update):
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + patterns.tutorial_text
    update.message.reply_text(msg)



(
    GET_COMMAND,
    TASK_CREATE,
    GET_DEADLINE,
    ADD_NOTIFICATION,
    ADD_DEADLINE,
    GET_NOTIFICATION,
    ADD_NOTIFICATION_TIME,
    TASK_VIEW,
    SELECT_ACTION,
    GET_EDIT_ACTION,
    GET_NEW_VALUE,
    RESTART
) = range(12)


def main():
    updater = Updater(settings.TOKEN)
    dp = updater.dispatcher
    logging.info('Start bot')

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("help", help),
            CommandHandler("tutorial", tutorial),
        ],
        states={
            GET_COMMAND: [
                RegexHandler("^Create Task$", add_task),
                RegexHandler("^List All Tasks$", list_tasks, pass_user_data=True),
                RegexHandler("^Help$", help),
                RegexHandler("^Tutorial$", tutorial),
                RegexHandler("^Restart$", start),
            ],
            TASK_CREATE: [
                MessageHandler(
                    Filters.text,
                    task_create,
                    pass_user_data=True),
            ],
            ADD_DEADLINE: [
                RegexHandler(
                    "^Yes$",
                    calendar_handler),
                RegexHandler(
                    "^No$",
                    no_deadline),
            ],
            GET_DEADLINE: [
                CallbackQueryHandler(
                    deadline_handler,
                    pass_user_data=True)
            ],
            ADD_NOTIFICATION: [
                RegexHandler(
                    "^Yes$",
                    add_notification,
                    pass_user_data=True),
                RegexHandler(
                    "^No$",
                    say_goodbye,
                    pass_user_data=True),
            ],
            GET_NOTIFICATION: [
                CallbackQueryHandler(
                    notification_handler,
                    pass_user_data=True)
            ],
            ADD_NOTIFICATION_TIME: [
                MessageHandler(
                    Filters.text,
                    add_notification_date,
                    pass_user_data=True,
                    pass_job_queue=True),
            ],
            TASK_VIEW: [
                CallbackQueryHandler(
                    task_view,
                    pass_user_data=True)
            ],
            SELECT_ACTION: [
                RegexHandler(
                    "^Edit$",
                    list_edit_options,
                    pass_user_data=True),
                RegexHandler(
                    "^Delete$",
                    delete_task,
                    pass_user_data=True),

            ],
            GET_EDIT_ACTION: [
                CallbackQueryHandler(
                    get_edit_action,
                    pass_user_data=True)
            ],
            GET_NEW_VALUE: [
                MessageHandler(
                    Filters.text,
                    edit_task,
                    pass_user_data=True),
            ],
            RESTART: [
                start
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True
    )

    updater.dispatcher.add_handler(conv_handler)
    # dp.add_handler(CallbackQueryHandler(inline_handler))
    # dp.add_handler(CommandHandler("start", start))
    # dp.add_handler(CommandHandler("set", set_task))
    # dp.add_handler(CommandHandler("help", help))
    # dp.add_handler(CommandHandler("tutorial", tutorial))
    # dp.add_handler(CommandHandler("new", new))
    # dp.add_handler(CommandHandler("calendar", calendar_handler))
    # dp.add_handler(CallbackQueryHandler(okornot))
    # dp.add_handler(MessageHandler(Filters.regex('start'), start))
    # dp.add_handler(MessageHandler(Filters.regex('set'), set_task))
    # dp.add_handler(MessageHandler(Filters.regex('help'), help))
    # dp.add_handler(MessageHandler(Filters.regex('tutorial'), tutorial))
    # dp.add_handler(CommandHandler("all", all))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
