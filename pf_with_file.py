import pickle
from pf_const import ADD, UPDATE, ABSENCE, UNNAME, UNREDMINE, HOUR, ABBREVIATED, HOLIDAY, WORKED, time_send_message, \
    TIMER
import os
from pf_time import Time
import json

"""First column - redmine_id, Second column - telegram_chat_id"""
dict_ids = {}


class ProductionCalendar(object):
    def __init__(self):
        log_in_file('__init__ ProductionCalendar')
        self.__load_calendar = None
        self.__day_number = None
        self.__month_number = None
        self.__year_number = None
        self.__status_day = None
        self.__dispatch_time = None
        self.__time_sent = None

        self.load_calendar()
        self.update()

    @property
    def day_number(self):
        return self.__day_number

    @property
    def status_day(self):
        return self.__status_day

    @property
    def dispatch_time(self):
        if Time().day != self.__day_number:
            self.update()
        return self.__dispatch_time

    @property
    def time_sent(self):
        return self.__time_sent

    @time_sent.setter
    def time_sent(self, value):
        self.__time_sent = value

    def load_calendar(self):
        log_in_file('load_calendar ProductionCalendar')
        if os.path.exists('calendar.json'):
            with open('calendar.json', 'rb') as file:
                self.__load_calendar = json.load(file)
        else:
            self.__load_calendar = None

    def update(self):
        log_in_file('update ProductionCalendar')
        self.__day_number = Time().day
        self.__month_number = Time().month
        self.__year_number = Time().year
        production_calendar = self.__load_calendar
        if production_calendar.get('year') == self.__year_number and self.__load_calendar is not None:
            for ones in production_calendar.get('months'):
                if ones.get('month') == self.__month_number:
                    broken_string = ones.get('days').split(',')
                    if (str(self.__day_number) + '*' in broken_string) or (str(self.__day_number) in broken_string):
                        if str(self.__day_number) + '*' in broken_string:
                            self.__status_day = ABBREVIATED
                            self.__description_days()
                            break
                        else:
                            self.__status_day = HOLIDAY
                            self.__description_days()
                            break
                    else:
                        self.__status_day = WORKED
                        self.__description_days()
                        break

    def __description_days(self):
        log_in_file('__description_days analysis')
        if self.__status_day == ABBREVIATED:
            """
            Если сокращенный день, то отправлять уведомление раньше на один час,
            флаг отправленного уведомления False
            """
            self.__dispatch_time = time_send_message - 1
            self.__time_sent = False
        elif self.__status_day == HOLIDAY:
            """
            Если выходной, то уведомление не отправлять, поэтому ставим флаг в положение 
            уведомление уже отправлено
            """
            self.__time_sent = True
        else:
            """
            Если день не сокарщенный и не выходной, то он рабочий, следовательно 
            восстанавливаем время отправки уведомлений, флаг ставим уведомление не отправлено
            """
            self.__dispatch_time = time_send_message
            self.__time_sent = False
        log_in_file('__description_days ' + self.__status_day + ' dispatch_time:' +
                    str(self.__dispatch_time) + ' time_sent:' + str(self.__time_sent))


class PickleMaster(object):
    """First column - redmine_id, Second column - telegram_chat_id"""

    def __init__(self):
        self.update = None

    def update_file(self, redmine_id, telegram_chat):
        """
        Добавляет или изменяет значение chat id телеграмма пользоателя с redmine id
        :param redmine_id: уникальное значение id пользователя в redmine
        :param telegram_chat: информация из чата пользователя в телеграмм
        :return: возвращает сообщение с информацией о изменении данных пользователя
        """
        self.create_data_file()  # Создает файл "data"  если он не существует
        with open('data', 'rb') as file:
            dict_ids_new = pickle.load(file)
        if dict_ids_new.get(redmine_id) is None:
            self.update = ADD
        else:
            self.update = UPDATE
        dict_ids_new[redmine_id] = telegram_chat.id
        with open('data', 'wb') as file:
            pickle.dump(dict_ids_new, file)
        return update_file_message(self.update)

    def get_chat_id(self, redmine_id):
        """
        Возвращает chat id телеграмма по redmine id
        :param redmine_id: redmine id пользователя
        :return: возвращает chat id в телеграмме
        """
        self.create_data_file()  # Создает файл "data"  если он не существует
        with open('data', 'rb') as file:
            dict_ids_new = pickle.load(file)
        return dict_ids_new[redmine_id]

    def get_redmine_id(self, chat_id):
        """
        Возвращает значение redmine id по идентификатору chat id
        :param chat_id: чат id телеграмма
        :return: возвращает redmine id
        """
        self.create_data_file()  # Создает файл "data"  если он не существует
        with open('data', 'rb') as file:
            dict_ids_new = pickle.load(file)
        result = 0
        for key, value in dict_ids_new.items():
            if value == chat_id:
                result = key
        if result == 0:
            result = update_file_message(ABSENCE)
        return result

    def update_user_list(self):
        """
        Обновляет данные redmine_id по пользователям из файла
        Если пользователей нет, возвращает нулевого пользователя
        :return: список пользователей подписанных на рассылку
        """
        self.create_data_file()  # Создает файл "data"  если он не существует
        result = ''
        with open('data', 'rb') as file:
            dict_ids_new = pickle.load(file)
        for user_identified, user_chat_id in dict_ids_new.items():
            result = str(user_identified) + '|' + result
        if result != '':
            result = result[0:(len(result) - 1)]
        else:
            result = '0'
        return result

    @staticmethod
    def create_data_file():
        """"
        Создает фаайл "data" если он не существует
        """
        if not os.path.exists('data'):
            with open('data', 'wb') as file:
                pickle.dump(dict_ids, file)
                log_in_file('Create data file')


def log_in_file(text):
    """
    Записывает текст в файл, добавляя вначале время
    :param text: текст для записи
    :return: -
    """
    if not os.path.exists('log.txt'):
        with open('log.txt', 'w') as logger:
            logger.write('Create log file' + '\n')
    with open('log.txt', 'a') as logger:
        logger.write(Time().today + ' ' + str(text) + '\n')


def revert_user_list(user_id, user_list):
    """
    Находит пользователя с user_id среди списка user_list
    :param user_id: id пользователя из redmine
    :param user_list: доступные список пользователя
    :return: возврщает булевое значение есть пользователь в списке (True) или нет (False)
    """
    broken_list = user_list.split('|')
    if str(user_id) in broken_list:
        return True
    else:
        return False


def update_file_message(flag):
    report = {
        ADD: "You have been added to the list",
        UPDATE: "You have been update information to the list",
        ABSENCE: "You not identification",
        UNNAME: "Не указано имя пользователя в телеграмм",
        UNREDMINE: "You telegram account is not in Redmine",
        HOUR: "Указано время: ",
        TIMER: "Таймер на {} сек закончился"
    }
    return report[flag]
