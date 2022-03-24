"""Uses module"""
from pf_const import BOT_ADMIN, TOKEN
from pf_redmine import MyRedmine
import telebot
import threading
from pf_with_file import log_in_file

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def c_identification(message):
    bot.send_message(message.chat.id, 'Функционал временно отключен')
    # redmine.identification(bot, message.chat)


@bot.message_handler(commands=['time'])
def c_time(message):
    redmine.time_entry(bot, message)  # Ошибка, пользвателю выводится ошибка, там ключ


@bot.message_handler(commands=['log'])
def c_text(message):
    try:
        log_file = open('log.txt', 'rb')
        bot.send_document(message.chat.id, log_file)
        log_file.close()
    except Exception as EX:
        bot.send_message(message.chat.id, EX)


@bot.message_handler(commands=['start_bot'])
def c_start_bot(message):
    if message.chat.id == BOT_ADMIN:
        if not redmine.updated:
            log_in_file('c_start_bot')  # # # Ошибка, неправильный вызов
            redmine_polling2 = threading.Thread(target=redmine.pooling, args=(bot,))
            redmine_polling2.start()
        else:
            bot.send_message(message.chat.id, 'It`s started')
            log_in_file(str(message.chat.username) + ' It`s started')


@bot.message_handler(content_types=['text'])
def c_text(message):
    bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    bot_polling = threading.Thread(target=bot.polling).start()
    """Working copy"""
    try:
        redmine = MyRedmine()
        log_in_file('Create redmine connection')
        print('Start Bot')
        redmine.endless_cycle(bot)
    except Exception as ex:
        log_in_file('Not create redmine:' + '\n' + str(ex))
        print(ex)
