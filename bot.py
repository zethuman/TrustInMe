import json
from functools import reduce
import settings
import patterns
import datetime
import pickle
import telegramcalendar
from threading import Event
from time import sleep, time
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
    reply_keyboard = [["\U0000270F Create Task", '\U0001F56E List All Tasks'],
                      ["\U00002795 Help", "\U0001F468 Tutorial"],
                      ["\U0001F680 Restart", "\U0000274C Cancel"], ['\U0000FF05 Statistics']]
    msg = 'Trust in me, (poiled by Rakhat)' + str(update.message.from_user.first_name) + ' \U0000270C' + patterns.start_text
    update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(
        reply_keyboard,
        resize_keyboard=True))
    return GET_COMMAND


def get_keyboard():
    reply_keyboard = [["\U0000270F Create Task", '\U0001F56E List All Tasks'],
                      ["\U00002795 Help", "\U0001F468 Tutorial"],
                      ["\U0001F680 Restart", "\U0000274C Cancel"], ['\U0000FF05 Statistics']]
    return reply_keyboard


def get_chat_user(bot, update):
    chat_user = bot.getChatMember(chat_id=update.message.chat_id, user_id='494692644')
    print(chat_user)


def statistics(bot, update):
    count = mdb.tasks.count_documents({})
    done_count = mdb.tasks.count_documents({'task_status': True})
    undone_count = mdb.tasks.count_documents({'task_status': False})
    per_done = round((done_count * 100) / count)
    per_undone = round((undone_count * 100) / count)
    update.message.reply_text('Trust in me ' + str(
        update.message.from_user.first_name) + ' \U0000270C' + '\n\nI can give some statistics based on your tasks:\n'
                              + '\n\U00002705  Done tasks:  ' + str(per_done) + '%'
                              + '\n\U0000274C  Undone tasks: ' + str(per_undone) + '%')


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
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ADD_DEADLINE


def get_username(update):
    return update.effective_user.username


def alarm(bot, job):
    bot.send_message(job.context["chat_id"], text=job.context["task_data"])


def get_tasks_with_unicode(task):
    if task['task_status']:
        return task['task_title']
    else:
        return task['task_title'] + ' \U00002705'


def get_tasks_list(user):
    tasks = mdb.tasks.find({'user_id': user.id},
                           {'task_title': 1, 'deadline_data': 1, 'notification_date': 1, '_id': 1, 'task_status': 1})
    # title = {}
    # for task in tasks:
    #     if task['task_status']:
    #         title = task['task_title'] + ' \U00002705'
    #     else:
    #         title = task['task_title']
    #
    #     print(title)
    keyboard = [[InlineKeyboardButton(get_tasks_with_unicode(task), callback_data=str(task['_id']))] for task in tasks]
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
                     text=f"""You selected {date}. Do you want to get notification?""",
                     reply_markup=ReplyKeyboardMarkup(
                         reply_keyboard,
                         one_time_keyboard=True,
                         resize_keyboard=True)
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
                     text=f"""You selected {date}. Enter notification time in format 'HH:MM'""",
                     reply_markup=ReplyKeyboardRemove())
    return ADD_NOTIFICATION_TIME


def add_notification_date(bot, update, job_queue, user_data):
    notification_time = update.message.text
    notification_date = user_data["notification_date"]
    user_data['task_status'] = True
    try:
        hour, minutes = map(int, notification_time.split(":"))
        notification = datetime.datetime(year=notification_date.year,
                                         month=notification_date.month,
                                         day=notification_date.day,
                                         hour=hour,
                                         minute=minutes)
    except ValueError:
        update.message.reply_text(
            "Please enter a valid time in format 'HH:MM'"
        )
        return None
    user_data["notification_date"] = notification
    chat_id = update.message.chat_id
    job_queue.run_once(alarm, notification, context={
        "chat_id": chat_id,
        "task_data": f"""You have a task {user_data['task_title']} to do before {user_data['deadline_date']}!"""
    })

    text = """\nResults: 
    <b>Task: </b> {task_title}
    <b>Deadline: </b> {deadline_date}
    <b>Notification date: </b> {notification_date}
    """.format(**user_data)
    update.message.reply_text(
        f"""Thanks! I'll send you a notification on your task on {notification:%A}, {notification} \n""" + text,
        reply_markup = ReplyKeyboardMarkup(get_keyboard()),
        parse_mode=ParseMode.HTML)
    user = search_or_save_user(mdb, update.effective_user, update.message)
    task = search_or_save_task(mdb, update.effective_user, user_data)
    return ConversationHandler.END


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
                         one_time_keyboard=True, resize_keyboard=True)
                     )
    return SELECT_ACTION


def get_norm_names(name):
    if name == 'task_title':
        return 'Title'
    elif name == 'deadline_date':
        return 'Deadline'
    elif name == 'notification_date':
        return 'Notification'
    elif name == 'task_status':
        return 'Status'

def get_task_fields():
    doc = reduce(lambda all_keys, rec_keys: all_keys | set(rec_keys),
                 map(lambda d: d.keys(), mdb.tasks.find({}, {'_id': 0, 'user_id': 0})), set())
    for key in doc:
        print(key)
    keyboard = [[InlineKeyboardButton(get_norm_names(name), callback_data=name)]
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
                         text=f"Please, send a new value for the task`s status",
                         reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
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
        update.message.reply_text(f"The task status is changed to {value}", reply_markup = ReplyKeyboardMarkup(get_keyboard()))
    user_data.clear()
    return ConversationHandler.END


def delete_task(bot, update, user_data):
    oid = user_data['oid']
    mdb.tasks.remove({'_id': ObjectId(oid)}, 1)
    user_data.clear()
    update.message.reply_text(
        f"The task is deleted.",
        reply_markup=ReplyKeyboardMarkup(get_keyboard())
    )
    return ConversationHandler.END


def cancel(bot, update):
    update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove()
    )


def say_goodbye(bot, update, user_data):
    user_data.clear()
    update.message.reply_text("Thank you! I hope we can talk again some day.", reply_markup=ReplyKeyboardMarkup(get_keyboard()))
    return ConversationHandler.END


def help(bot, update):
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + ' \U0000270C' + patterns.help_text
    update.message.reply_text(msg, reply_markup = ReplyKeyboardMarkup(get_keyboard()))


def tutorial(bot, update):
    msg = 'Trust in me, ' + str(update.message.from_user.first_name) + ' \U0000270C' + patterns.tutorial_text
    update.message.reply_text(msg, reply_markup = ReplyKeyboardMarkup(get_keyboard()))


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
    GET_NEW_VALUE
) = range(11)

# JOBS_PICKLE = "/var/data/job_tuples.pickle"
JOBS_PICKLE = 'job_tuples.pickle'


def load_jobs(jq):
    now = time()

    with open(JOBS_PICKLE, "rb") as fp:
        while True:
            try:
                next_t, job = pickle.load(fp)
            except EOFError:
                break  # Loaded all job tuples

            # Create threading primitives
            enabled = job._enabled
            removed = job._remove

            job._enabled = Event()
            job._remove = Event()

            if enabled:
                job._enabled.set()

            if removed:
                job._remove.set()

            next_t -= now  # Convert from absolute to relative time

            jq._put(job, next_t)


def save_jobs(jq):
    if jq:
        job_tuples = jq._queue.queue
    else:
        job_tuples = []

    with open(JOBS_PICKLE, "wb") as fp:
        for next_t, job in job_tuples:
            # Back up objects
            _job_queue = job._job_queue
            _remove = job._remove
            _enabled = job._enabled

            # Replace un-pickleable threading primitives
            job._job_queue = None  # Will be reset in jq.put
            job._remove = job.removed  # Convert to boolean
            job._enabled = job.enabled  # Convert to boolean

            # Pickle the job
            pickle.dump((next_t, job), fp)

            # Restore objects
            job._job_queue = _job_queue
            job._remove = _remove
            job._enabled = _enabled


def save_jobs_job(bot, job):
    save_jobs(job.job_queue)

def getKeyboard(bot, update):
    update.message.reply_text('Do you need to keyboard? Catch it', reply_markup=ReplyKeyboardMarkup(get_keyboard()))


def main():
    updater = Updater(settings.TOKEN)
    dp = updater.dispatcher
    job_queue = updater.job_queue

    job_queue.run_repeating(save_jobs_job, datetime.timedelta(minutes=1))

    try:
        load_jobs(job_queue)
    except FileNotFoundError:
        # First run
        pass

    logging.info('Start bot')

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("help", help),
            CommandHandler("tutorial", tutorial),
            CommandHandler("keyboard", getKeyboard),
            MessageHandler(Filters.regex('List All Tasks'), list_tasks, pass_user_data=True),
            MessageHandler(Filters.regex('Create Task'), add_task),
        ],
        states={
            GET_COMMAND: [
                MessageHandler(Filters.regex('Create Task'), add_task),
                MessageHandler(Filters.regex('List All Tasks'), list_tasks, pass_user_data=True),
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
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True
    )

    updater.dispatcher.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.regex('Restart'), start))
    dp.add_handler(MessageHandler(Filters.regex('Help'), help))
    dp.add_handler(MessageHandler(Filters.regex('Tutorial'), tutorial))
    dp.add_handler(MessageHandler(Filters.regex('Cancel'), cancel))
    dp.add_handler(MessageHandler(Filters.regex('Statistics'), statistics))
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
    save_jobs(job_queue)


if __name__ == '__main__':
    main()
