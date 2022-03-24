import datetime


class Time(object):

    def __init__(self):
        self.update = None

    @property
    def date_for_redmine(self):
        return datetime.datetime.now().date()

    @property
    def minute(self):
        return datetime.datetime.now().minute

    @property
    def hour(self):
        return datetime.datetime.now().hour

    @property
    def day(self):
        return datetime.datetime.now().day

    @property
    def month(self):
        return datetime.datetime.now().month

    @property
    def year(self):
        return datetime.datetime.now().year

    @property
    def today(self):
        return str(datetime.datetime.now().today())
