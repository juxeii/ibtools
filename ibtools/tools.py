import datetime
from ib_insync import Option


class OptionDetail:

    def __init__(self, option, underlying):
        self.option = option
        self.underlying = underlying
        self.symbol = underlying.symbol
        self.expiration = toDate(option.lastTradeDateOrContractMonth)
        self.strike = option.strike
        self.right = option.right

    def __str__(self):
        return 'OptionDetail:\n' + 'Option: '+str(self.option) + '\n' + 'Underlying: ' + str(self.underlying)


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


def _createOption(symbol, expiration, strike, right, exchange):
    return Option(symbol, toTWSDateFromDate(expiration), strike, right, exchange)
