import settings
import patterns
import datetime
import telegramcalendar
import logging
from mongodb import mdb, search_or_save_user, search_user_task, list_of_tasks
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
    reply_keyboard = [["Create Task", "List All Tasks"]]
    msg = 'Trust in me, (poiled by Rakhat)' + str(update.message.from_user.first_name) + patterns.start_text
    update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(
        reply_keyboard,
        one_time_keyboard=True))
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


# def get_tasks_list(user):
#     # tasks = Task.objects.filter(reporter=user)
#     keyboard = [[InlineKeyboardButton(task.title, callback_data=task.id)]
#                 for task in tasks]
#     keyboard_markup = InlineKeyboardMarkup(keyboard)
#     return keyboard_markup


def list_tasks(bot, update, user_data):
    user = update.message.from_user
    reply_markup = ReplyKeyboardRemove()
    user = search_or_save_user(mdb, update.effective_user, update.message)
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

    user_data['deadline_date'] = date
    print(date)
    # task = user_data["task"]
    # task.due_date = date
    # task.save(update_fields=["due_date"])
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
    try:
        hour, minutes = map(int, notification_time.split(":"))
        notification = datetime
    except ValueError:
        update.message.reply_text(
            "Please enter a valid time in format 'HH:MM'"
        )
        return None

    # task = user_data["task"]
    # task.notification = notification
    # task.save(update_fields=["notification"])
    chat_id = update.message.chat_id
    # job_queue.run_once(alarm, notification, context={
    #     "chat_id": chat_id,
    #     "task_data": f"""You have a task {task.title} {task.description}
    #                  to do before {task.due_date}!"""
    # })
    # {notification:%A}, {notification}
    # update.message.reply_text(
    #     f"""Thanks! I'll send you a notification
    #     on your task on """)

    text = """\nResults: 
    <b>Task: </b> {task_title}
    <b>Deadline: </b> {deadline_date}
    <b>Notification date: </b> {notification_date}
    """.format(**user_data)
    update.message.reply_text(f"""Thanks! I'll send you a notification
        on your task on \n""" + text, parse_mode=ParseMode.HTML)
    user = search_or_save_user(mdb, update.effective_user, update.message)
    task = search_user_task(mdb, user, user_data)
    return ConversationHandler.END


def task_view(bot, update, user_data):
    task_id = update.callback_query.data
    # task = Task.objects.get(id=task_id)
    reply_keyboard = [["Edit", "Delete"]]
    user_data["task"] = task
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"Task {task.title}\nDescription: "
                     f"{task.description}\n"
                     f"Due date: {task.due_date}\nNotification: "
                     f"{task.notification}\n"
                     f"Status: {task.status}",
                     reply_markup=ReplyKeyboardMarkup(
                         reply_keyboard,
                         one_time_keyboard=True)
                     )
    return SELECT_ACTION



# def inline_handler(bot,update):
#     selected,date = telegramcalendar.process_calendar_selection(bot, update)
#     if selected:
#         bot.send_message(chat_id=update.callback_query.from_user.id,
#                         text="You selected %s" % (date.strftime("%d/%m/%Y")),
#                         reply_markup=ReplyKeyboardRemove())

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
    GET_NEW_VALUE
) = range(11)


def main():
    updater = Updater(settings.TOKEN)
    dp = updater.dispatcher
    logging.info('Start bot')

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("help", help),
            CommandHandler("tutorial", tutorial)
        ],
        states={
            GET_COMMAND: [
                RegexHandler("^Create Task$", add_task),
                RegexHandler("^List All Tasks$", list_tasks, pass_user_data=True),
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
