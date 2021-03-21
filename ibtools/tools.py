import datetime


def setApplication(app):
    global _app
    _app = app


def toDate(date):
    return toDateFromTWSDate(date)


def toDates(*dates):
    return [toDate(date) for date in dates]


def today():
    return datetime.date.today()


def toDateFromTWSDate(twsDate):
    if isinstance(twsDate, str):
        return datetime.datetime.strptime(twsDate, _twsDateFormat).date()
    return twsDate


def toTWSDateFromDate(date):
    if isinstance(date, str):
        return date
    return date.strftime(_twsDateFormat)


###################################################################
_app = None
_twsDateFormat = '%Y%m%d'


def _app():
    return _app
