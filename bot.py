import telebot
from settings import TOKEN
from telebot import types

bot = telebot.TeleBot(TOKEN)


# --------------------------Start-------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Trust in me, ' + message.from_user.first_name + '\n\n'
                                                                                       'Use the following commands to control me:\n\n'
                                                                                       '/new – create a new to-do list\n'
                                                                                       '/show – show current to-do list\n'
                                                                                       '/all – show all existing to-do lists\n\n'
                                                                                       '/help – show this help message\n'
                                                                                       '/tutorial – show tutorial\n'
                                                                                       '/settings – settings\n'
                                                                                       '@trustinmesupport – get a support\n'
                                                                                       '@trustinmenews – announcements, news, tips\n'
                                                                                       '@trustinmechat – chat for users')


# --------------------------Help-------------------------------------------------------------------
@bot.message_handler(commands=['help'])
def start_message(message):
    bot.send_message(message.chat.id, 'Trust in me, ' + message.from_user.first_name + '\n\n'
                                                                                       'I will help you to crate to-dos:\n\n'
                                                                                       '@trustinmesupport – get a support\n'
                                                                                       '@trustinmenews – announcements, news, tips\n'
                                                                                       '@trustinmechat – chat for users')


# -------------------------Tutorial---------------------------------------------------------------
@bot.message_handler(commands=['tutorial'])
def start_message(message):
    bot.send_message(message.chat.id, 'Trust in me, ' + message.from_user.first_name + '\n\n'
                                                                                       'I will help you to know me better, that\'s easy:\n\n'
                                                                                       'First step...'
                                                                                       'Second step...')


# -------------------------New---------------------------------------------------------------
@bot.message_handler(commands=['new'])
def start_message(message):
    bot.send_message(message.chat.id, 'Trust in me, ' + message.from_user.first_name + '\n\n'
                                                                                       'I will help you to know me '
                                                                                       'better, that\'s easy:\n\n '
                                                                                       'First step...'
                                                                                       'Second step...')


@bot.message_handler(content_types=["text"])
def any_msg(message):
    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text="Нажми меня", callback_data="test")
    keyboard.add(callback_button)
    bot.send_message(message.chat.id, "Я – сообщение из обычного режима", reply_markup=keyboard)


@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(query):
    kb = types.InlineKeyboardMarkup()
    # Добавляем колбэк-кнопку с содержимым "test"
    kb.add(types.InlineKeyboardButton(text="Нажми меня", callback_data="test"))
    results = []
    single_msg = types.InlineQueryResultArticle(
        id="1", title="Press me",
        input_message_content=types.InputTextMessageContent(message_text="Я – сообщение из инлайн-режима"),
        reply_markup=kb
    )
    results.append(single_msg)
    bot.answer_inline_query(query.id, results)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Если сообщение из чата с ботом
    if call.message:
        if call.data == "test":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пыщь")
    # Если сообщение из инлайн-режима
    elif call.inline_message_id:
        if call.data == "test":
            bot.edit_message_text(inline_message_id=call.inline_message_id, text="Бдыщь")


@bot.message_handler(content_types=["text"])
def default_test(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Перейти на Яндекс", url="https://google.com")
    keyboard.add(url_button)
    bot.send_message(message.chat.id, "Привет! Нажми на кнопку и перейди в поисковик.", reply_markup=keyboard)


if __name__ == '__main__':
    bot.infinity_polling()

bot.polling()
