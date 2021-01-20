import config
import telebot
import utils
import advices

bot = telebot.TeleBot(config.token)
questions = utils.read_csv(config.path_to_csv)
question_asked = 0


@bot.message_handler(commands=["start"])
def cmd_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Хочу ответить на вопрос!', callback_data='question'))
    bot.send_message(message.chat.id, "Привет! Я - бот, помогающий улучшить ответы на вопросы mail.ru",
                     reply_markup=markup)

    global question_asked
    question_asked = 0


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    global question_asked
    if call.data == 'question':
        question = utils.get_random_question(questions)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text='Другой вопрос', callback_data='another_question'))

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, question, reply_markup=markup)
        question_asked = 1

    if call.data == 'another_question':
        question = utils.get_random_question(questions)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text='Другой вопрос', callback_data='another_question'))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=question, reply_markup=markup)
        question_asked = 1

    if call.data == 'fix_answer':
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        question_asked = 1


@bot.message_handler(func=lambda message: question_asked == 1, content_types=['text'])
def answer_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')
    list_of_advices = advices.explore_answer(message.text)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Исправить ответ', callback_data='fix_answer'))
    markup.add(telebot.types.InlineKeyboardButton(text='Другой вопрос', callback_data='question'))

    if len(list_of_advices) > 1:
        text = 'Ваш ответ можно улучшить. Попробуйте: \n'
        for i, item in enumerate(list_of_advices, start=1):
            text += str(i) + ') ' + str(item) + ' \n '
        bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        text = list_of_advices[0]
        bot.send_message(message.chat.id, text, reply_markup=markup)

    global question_asked
    question_asked = 0


@bot.message_handler(func=lambda message: question_asked == 0, content_types=['text'])
def answer_handler_without_question(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Задать вопрос', callback_data='question'))
    bot.send_message(message.chat.id, 'Вопрос еще не задан', reply_markup=markup)


if __name__ == '__main__':
    bot.infinity_polling()
