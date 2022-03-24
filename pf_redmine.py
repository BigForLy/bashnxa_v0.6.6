import time
from pf_const import BOT_ADMIN, notification_list_id, url, UNNAME, UNREDMINE, HOUR, start_day_time, end_day_time, \
    REDMINE_API, ISSUE, SEND_TIME, USERS
from pf_with_file import PickleMaster, log_in_file, revert_user_list, update_file_message, \
    ProductionCalendar
from redminelib import Redmine
from contextlib import contextmanager
import threading
import _thread
from pf_time import Time


class RequestParams:
    """
    Параметры для составления запроса в redmine
    """

    def __init__(self, resource=None, spent_on=None, user_id=None, status_id=None, project_id=None, assigned_to_id=None,
                 values=None):
        self.__resource = resource  # Тип данных (задания, проекты, пользователи)
        self.__spent_on = spent_on  # Дата/Время
        self.__user_id = user_id  # Список пользователей
        self.__status_id = status_id  # Список статусов заданий, по которым происходит оповещение
        self.__project_id = project_id  # Номер проекта
        self.__fixed_version_id = '!101'  # Номер релиза, убираем релиз с номером 101, где релиз 101=(пусто)
        self.__assigned_to_id = assigned_to_id  # Список пользователей редмайн, для которых включено оповещение
        self.__values = values  # Список параметров, для показа

    @property
    def resource(self):
        return self.__resource

    @property
    def spent_on(self):
        return self.__spent_on

    @property
    def user_id(self):
        return self.__user_id

    @property
    def status_id(self):
        return self.__status_id

    @property
    def project_id(self):
        return self.__project_id

    @property
    def fixed_version_id(self):
        return self.__fixed_version_id

    @property
    def assigned_to_id(self):
        return self.__assigned_to_id

    @property
    def values(self):
        return self.__values


def method_in_log(method):
    def wrapper(self, *args):
        try:
            log_in_file(method.__name__ + ' start')
            method_result = method(self, *args)
            log_in_file(method.__name__ + '   end')
            return method_result
        except Exception as ex:
            log_in_file(str(ex))
        finally:
            if method.__name__ != '__request_method':  # request выполняется внутри, отделять нет необходимости
                log_in_file('************************************')

    return wrapper


class RequestManager:
    def __init__(self):
        self.__value = None

    @property
    def value(self):
        return self.__value

    def manager(self, request_issue):
        xx = threading.Thread(target=self.__request_method, args=(request_issue,))
        xx.start()
        time.sleep(8 - time.time() % 1)
        log_in_file('xx join')
        xx.join()
        log_in_file('del xx')
        del xx
        if self.__value is None:  # Если не переписали значение значит сработал таймер
            raise Exception(f"Something went wrong {request_issue.resource}")

    @method_in_log
    def __request_method(self, method_params):
        try:
<<<<<<< Updated upstream
            redmine_connection = Redmine('http://92.50.164.2:3000/redmine')
            log_in_file(f'redmine api: {REDMINE_API} True, resource is {method_params.resource}')
=======
            redmine_connection = Redmine(***)
            log_in_file(f'session: {REDMINE_API} True, resource is {method_params.resource}')
>>>>>>> Stashed changes
            if method_params.resource is ISSUE:
                with redmine_connection.session(key=REDMINE_API) as session:
                    set_issues_update = list(
                        session.issue.filter(status_id=method_params.status_id,
                                             project_id=method_params.project_id,
                                             fixed_version_id=method_params.fixed_version_id,
                                             assigned_to_id=method_params.assigned_to_id
                                             ).values(*method_params.values)
                    )
                    self.__value = set_issues_update
            elif method_params.resource is SEND_TIME:
                with redmine_connection.session(key=REDMINE_API) as session:
                    time_per_day = list(
                        session.time_entry.filter(spent_on=method_params.spent_on,
                                                  user_id=method_params.user_id
                                                  ).values(*method_params.values)
                    )
                    self.__value = time_per_day
            elif method_params.resource is USERS:
                with redmine_connection.session(key=REDMINE_API) as session:
                    all_users = list(
                        session.user.all().values(*method_params.values)
                                    )
                    self.__value = all_users
            log_in_file('try request')
        finally:
            del redmine_connection


class MyRedmine:
    def __init__(self):
        self.updated = False
        self.list_users_to_string = PickleMaster().update_user_list()
        self.issues = None
        self.__bot = None
        self.__chat = None
        self.__time_sent = False

        self.__update_self_issue(self, '')

    @method_in_log
    def endless_cycle(self, bot, time_sleep=120):  # по факту уже не нужен
        self.__bot = bot
        production_calendar = ProductionCalendar()
        while True:  # # # Сделать условие, что количество ошибок больше определенного
            try:
                self.pooling(production_calendar)
                time.sleep(time_sleep - time.time() % 1)
            except Exception as ex:
                log_in_file(ex)

    @method_in_log
    def identification(self, bot, chat):
        """
        Метод для идентификации пользователя
        :param bot: параметры бота, для отправки сообщений
        :param chat: информация из чата пользователя в телеграмм
        :return: -
        """
        try:
            self.__bot = bot
            self.__chat = chat
            finding_in_redmine = self.__search_user_in_telegram()
            if not finding_in_redmine:
                bot.send_message(chat.id, update_file_message(UNREDMINE))
                log_in_file('chat_username:' + str(chat.username) + ' You telegram account is not in Redmine')
            self.__chat = None
        except Exception as ex:
            error_report = 'Error identification' + str(ex)
            bot.send_message(BOT_ADMIN, error_report)
            log_in_file(error_report)

    def __search_user_in_telegram(self):
        """
        Метод нахождния пользователя в redmine по имени пользователя телеграмм
        :return: -
        """
        chat = self.__chat
        bot = self.__bot
        if chat.username is not None:
            users_id_and_telegram = self.__update_all_users(self)
            for user in users_id_and_telegram:
                username_telegram = self.get_custom_field_value(user, 'Telegram')
                if confirm_username_telegram(username_telegram) == chat.username:
                    message_to_identified = PickleMaster().update_file(user.get('id'), chat)
                    self.list_users_to_string = PickleMaster().update_user_list()  # # # Некорректно, пользователю
                    # будет отправлено сообщение о ксках со статусами, которые были до подключения к боту
                    bot.send_message(chat.id, message_to_identified)
                    log_in_file('chat_username:' + str(chat.username) + ' ' + message_to_identified)
                    finding_in_redmine = True
                    return finding_in_redmine
        else:
            bot.send_message(chat.id, update_file_message(UNNAME))
            log_in_file('chat_username:' + str(chat.id) + ' ' + update_file_message(UNNAME))
            finding_in_redmine = False
            return finding_in_redmine

    @staticmethod
    def get_custom_field_value(user_custom_field, custom_field_name):
        for field in user_custom_field.get('custom_fields'):
            if field.get('name') == custom_field_name:
                custom_field_value = field.get('value')
                return custom_field_value

    @method_in_log
    def pooling(self, production_calendar, time_sleep=120):
        try:
            log_in_file('Started now')
            while Exception:
                if Time().hour == production_calendar.dispatch_time and not production_calendar.time_sent:
                    self.__auto_send_time_message(production_calendar)
                elif start_day_time <= Time().hour <= end_day_time:
                    self.__auto_send_message_user(self)
                    time.sleep(time_sleep - 10 - time.time() % 1)
                elif Time().hour > end_day_time:  # Ожидаем до начала рабочего дня
                    log_in_file('Ожидаем до начала рабочего дня')
                    time_out = (start_day_time + 24 - Time().hour) * 60 - Time().minute  # Время в минутах для сна
                    time.sleep(time_out * 60 - time.time() % 1)
                elif Time().hour < start_day_time:  # Ожидаем до начала рабочего дня
                    log_in_file('Ожидаем до начала рабочего дня')
                    time_out = (start_day_time - Time().hour) * 60 - Time().minute  # Время в минутах для сна
                    time.sleep(time_out * 60 - time.time() % 1)
        except Exception as ex:
            log_in_file(str(ex))
        finally:
            self.updated = False
            del production_calendar
            log_in_file('Bot Finally')

    @method_in_log
    def __update_self_issue(self, *args):
        set_issues_update = RequestManager()
        """Записываем параметры запроса"""
        request_issue = RequestParams(resource=ISSUE, status_id=notification_list_id, project_id=21,
                                      assigned_to_id=self.list_users_to_string,
                                      values=['id', 'status', 'assigned_to',
                                              'fixed_version', 'subject'])
        set_issues_update.manager(request_issue)
        self.issues = set_issues_update.value
        del set_issues_update

    @method_in_log
    def __auto_send_time_message(self, production_calendar):
        """
        Выставляет булевое значение флага __time_sent отправлено ли сообщение, если
        сейчас 17 часов и сообщение не отправлено меняет значение флага на сообщение отправлено, если
        сейчас больше 17 часов и сообщение было отправлено, ставим не отправлено, чтобы
        отправить сообщение на следующий день
        :return: -
        """
        production_calendar.time_sent = True
        memo = {}
        bot = self.__bot
        set_issues_update = RequestManager()
        request_time = RequestParams(resource=SEND_TIME, spent_on=Time().date_for_redmine,
                                     user_id=PickleMaster().update_user_list(), values=['hours', 'user'])
        set_issues_update.manager(request_time)
        time_per_day = set_issues_update.value
        del set_issues_update
        for one_line in time_per_day:
            if one_line.get('user').get('id') not in memo:
                memo[one_line.get('user').get('id')] = one_line.get('hours')
            else:
                memo[one_line.get('user').get('id')] = memo[one_line.get('user').get('id')] + one_line.get('hours')
        user_list = self.list_users_to_string.split('|')
        for user in user_list:
            if memo.get(int(user)) is not None:
                report_value = memo[int(user)]
            else:
                report_value = 0.0
            if float(report_value) < 8.0:
                hour, minute = divmod(report_value, 1)
                report_value = '{}:{}'.format(int(hour), int(minute * 60))
                report = update_file_message(HOUR) + report_value
                bot.send_message(PickleMaster().get_chat_id(int(user)), report)
                log_in_file(user + ' ' + report)
            else:
                report = update_file_message(HOUR) + str(report_value)
                log_in_file(user + ' NO SEND  ' + report)

    @method_in_log
    def __auto_send_message_user(self, *args):
        """
        Отправляет сообщения подписанным пользователям о измененных задачах
        :return: -
        """
        bot = self.__bot
        set_issues_update = RequestManager()
        """Записываем параметры запроса"""
        request_issue = RequestParams(resource=ISSUE, status_id=notification_list_id, project_id=21,
                                      assigned_to_id=self.list_users_to_string,
                                      values=['id', 'status', 'assigned_to',
                                              'fixed_version', 'subject'])
        set_issues_update.manager(request_issue)
        init_issue, updated_issue = self.issues, set_issues_update.value
        del set_issues_update
        log_in_file('updated_issue_count: ' + str(len(updated_issue)))
        if init_issue != updated_issue:
            list_changed_issues = [updated_issue[i] for i in range(len(updated_issue))
                                   if (updated_issue[i] not in init_issue)]
            log_in_file('Изменения: ' + str(list_changed_issues) + ' Пользователи: ' +
                        str(self.list_users_to_string))
            for i in range(len(list_changed_issues)):
                if revert_user_list(list_changed_issues[i].get('assigned_to').get('id'),
                                    self.list_users_to_string):
                    report = str(list_changed_issues[i].get('status').get('name')) + ' КС ' + \
                             url + str(list_changed_issues[i].get('id')) + ' ' + \
                             str(list_changed_issues[i].get('subject'))
                    bot.send_message(PickleMaster().get_chat_id(list_changed_issues[i].
                                                                get('assigned_to').get('id')), report)
                    # возможно не нужно str
                    report = 'ADMIN ' + str(list_changed_issues[i].get('assigned_to').get('name')) + ' ' + report
                    bot.send_message(BOT_ADMIN, report)
                    log_in_file(report)
            self.issues = updated_issue

    @method_in_log
    def __update_all_users(self):
        """
        Обновляет список пользователей в редмайн
        :return: возвращает список пользователей редмайн
        """
        set_issues_update = RequestManager()
        request_issue = RequestParams(resource=USERS, values=['id', 'firstname', 'lastname', 'custom_fields'])
        set_issues_update.manager(request_issue)
        users = set_issues_update.value
        del set_issues_update
        return users

    @method_in_log
<<<<<<< Updated upstream
=======
    def request_method(self, method_params):
        """
        Общий метод для запросов к redmine
        :param method_params: Парметры для запроса
        :return: list данных
        """
        redmine_connection = Redmine(***)
        try:
            log_in_file(f'session: {REDMINE_API} True, resource is {method_params.resource}')
            if method_params.resource is ISSUE:
                with redmine_connection.session(key=REDMINE_API):
                    set_issues_update = list(
                        redmine_connection.issue.filter(status_id=method_params.status_id,
                                                        project_id=method_params.project_id,
                                                        fixed_version_id=method_params.fixed_version_id,
                                                            assigned_to_id=method_params.assigned_to_id
                                                            ).values(*method_params.values)
                    )
                    return set_issues_update
            elif method_params.resource is SEND_TIME:
                with redmine_connection.session(key=REDMINE_API):
                    time_per_day = list(
                        redmine_connection.time_entry.filter(spent_on=method_params.spent_on,
                                                                 user_id=method_params.user_id
                                                                 ).values(*method_params.values)
                        )
                    return time_per_day
            elif method_params.resource is USERS:
                with redmine_connection.session(key=REDMINE_API):
                    all_users = list(
                        redmine_connection.user.all().values(*method_params.values)
                )
                return all_users
        finally:
            log_in_file('try request')

    @method_in_log
>>>>>>> Stashed changes
    def time_entry(self, bot, message):
        try:
            user_id = PickleMaster().get_redmine_id(message.chat.id)
            if type(user_id) == int:  # С помощью get_redmine_id через message.chat.id получаем redmine_id,
                # если пользователя нет, то возвращаем уведомление с типом str
                set_issues_update = RequestManager()
                request_issue = RequestParams(resource=SEND_TIME, spent_on=Time().date_for_redmine,
                                              user_id=user_id,
                                              values=['hours'])
                set_issues_update.manager(request_issue)
                time_per_day = set_issues_update.value
                del set_issues_update
                hours_per_day = 0.0
                for i in range(len(time_per_day)):
                    hours_per_day = hours_per_day + time_per_day[i].get('hours')
                report = 'Время за работой сегодня: ' + str(hours_per_day)
                log_in_file(str(message.chat.username) + ' ' + report)
                bot.send_message(message.chat.id, report)
            else:
                log_in_file(str(message.chat.id) + ' ' + user_id)
                bot.send_message(message.chat.id, user_id)
        except Exception as ex:
            error_report = 'Error time_entry ' + str(ex)
            bot.send_message(BOT_ADMIN, error_report)
            log_in_file(error_report)


def confirm_username_telegram(username_telegram):
    """
    Убирает лишний знак из поля в телеграмм
    :param username_telegram: значение имени телеграмма в редмайн
    :return: значение имени без собачки
    """
    if username_telegram != '':
        if username_telegram[0] == '@':
            return username_telegram[1:len(username_telegram)]
        else:
            return username_telegram


def date():
    return time.strftime('%Y' + '-' + '%m' + '-' + '%d')


@contextmanager
def time_limit(seconds):
    timer = threading.Timer(seconds, lambda: _thread.interrupt_main())
    timer.start()
    try:
        yield
    except KeyboardInterrupt as ex:
        raise ex
    finally:
        timer.cancel()
