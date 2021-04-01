import datetime
from numpy import apply_over_axes
from rx.subject import Subject


class OptionDetail:

    def __init__(self, option, underlying):
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


class MarketDataStream:

    def __init__(self, app):
        self.observable = Subject()
        app.pendingTickersEvent += self.__onMarketData

    def __onMarketData(self, pendingTickers):
        for marketData in pendingTickers:
            self.observable.on_next(marketData)


def toDate(date):
    return toDateFromTWSDate(date)


def toDates(*dates):
    return [toDate(date) for date in dates]


def today():
    return datetime.date.today()


def toDateFromTWSDate(twsDate):
    if isinstance(twsDate, str):
        return datetime.datetime.strptime(twsDate, twsDateFormat).date()
    return twsDate


def toTWSDateFromDate(date):
    if isinstance(date, str):
        return date
    return date.strftime(twsDateFormat)


global app
app = None

global marketDataObservable
marketDataObservable = None

global cacheFilePath
cacheFilePath = ''

global twsDateFormat
twsDateFormat = '%Y%m%d'
