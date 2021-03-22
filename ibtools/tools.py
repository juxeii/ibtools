import datetime
from rx.subject import Subject


class OptionDetail:

    def __init__(self, option, underlying):
        _app.qualifyContracts(underlying)

        self.option = option
        self.underlying = underlying
        self.symbol = underlying.symbol
        self.expiration = toDate(option.lastTradeDateOrContractMonth)
        self.strike = option.strike
        self.right = option.right

    def __str__(self):
        return 'OptionDetail:\n' + \
            'Option: '+str(self.option) + '\n' + \
            'Underlying: ' + str(self.underlying)


def setApplication(app):
    global _app
    _app = app
    global _marketDataObservable
    _marketDataObservable = _MarketDataStream()


def getApplication():
    return _app


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
_marketDataObservable = None
_twsDateFormat = '%Y%m%d'


class _MarketDataStream:
    def __init__(self):
        self.observable = Subject()
        _app.pendingTickersEvent += self.__onMarketData

    def __onMarketData(self, pendingTickers):
        for marketData in pendingTickers:
            self.observable.on_next(marketData)


def _marketDataObservable():
    return _marketDataObservable
