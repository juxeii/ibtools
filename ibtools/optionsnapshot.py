
import math
import rx
from rx.subject import Subject
from rx.operators import *
from IPython.utils import io
from ibtools.tools import getApplication, _marketDataObservable


class OptionMarketData:

    def __init__(self, optionDetail):
        self.optionDetail = optionDetail
        self.symbol = optionDetail.symbol
        self.expiration = optionDetail.expiration
        self.strike = optionDetail.strike
        self.right = optionDetail.right
        self.isDataAvailable = False

    def subscribe(self, marketDataReadyListener=lambda snapshot: None):
        self.__marketDataReadyListener = marketDataReadyListener
        self.undMarketData = _requestMarketData(self.optionDetail.underlying)

        _marketDataObservable().observable \
            .pipe(
                filter(lambda data: data.contract == self.optionDetail.option),
                filter(_isMarketDataReady),
                distinct(lambda data: data.contract),
                take(1)
        ) .subscribe(on_completed=self.__onMarketDataComplete)

        self.marketData = _requestMarketData(self.optionDetail.option)

    def __onMarketDataComplete(self):
        self.isDataAvailable = True
        self.__marketDataReadyListener(self)
        del self.__marketDataReadyListener

    def unsubscribe(self):
        if hasattr(self, 'undMarketData'):
            with io.capture_output():
                _cancelMarketData(self.optionDetail.underlying)
                _cancelMarketData(self.optionDetail.option)
            del self.undMarketData
            del self.marketData
            self.isDataAvailable = False

    def __nonzero__(self):
        return self.isDataAvailable

    def __str__(self):
        return 'Option market data '+str(self.symbol) + \
            ' on ' + str(self.expiration) + \
            ' at strike ' + str(self.strike) + str(self.right)


class OptionChainMarketData:

    def __init__(self, optionChain):
        self.optionChain = optionChain
        self.underlying = optionChain.underlying
        self.symbol = optionChain.symbol
        self.expiration = optionChain.expiration
        self.calls = _fromOptionDetailsToOptionMarketData(optionChain.calls)
        self.puts = _fromOptionDetailsToOptionMarketData(optionChain.puts)
        self.__allOptionMarketData = list(self.calls.values()) + \
            list(self.puts.values())
        self.__chainSize = len(self.calls) + len(self.puts)
        self.__isDataAvailable = False

    def subscribe(self, marketDataReadyListener=lambda snapshot: None):
        self.__marketDataReadyListener = marketDataReadyListener
        _subscribeAllItems(self.__chainSize,
                           self.__onAllSnapshotsSubscribed,
                           self.__subscibeAllOptions)

    def __subscibeAllOptions(self, observable):
        for optionMarketData in self.__allOptionMarketData:
            optionMarketData.subscribe(observable.on_next)
            getApplication().sleep(_markteReqThrottle)

    def __onAllSnapshotsSubscribed(self):
        self.__isDataAvailable = True
        print('Option chain market data for ' + self.symbol +
              ' on '+str(self.expiration) + ' is now subscribed.')
        self.__marketDataReadyListener(self)
        del self.__marketDataReadyListener

    def unsubscribe(self):
        for optionMarketData in self.__allOptionMarketData:
            optionMarketData.unsubscribe()
        self.__isDataAvailable = False
        print('Option chain market data for ' + self.symbol +
              ' on '+str(self.expiration) + ' is now unsubscribed.')

    def __len__(self):
        return self.__chainSize

    def __nonzero__(self):
        return self.__isDataAvailable

    def __str__(self):
        return 'Option chain market data for ' + str(self.symbol) + ' on '+str(self.expiration)


class OptionChainsMarketData:

    def __init__(self, optionChains):
        self.optionChains = optionChains
        self.symbol = next(iter(optionChains.values())).symbol
        self.expirations = list(optionChains.keys())
        self.chains = {chainMarketData.expiration: chainMarketData
                       for chainMarketData in [OptionChainMarketData(chain)
                                               for chain in optionChains.values()]}
        self.__noOfChains = len(self.chains)
        self.__isDataAvailable = False

    def subscribe(self, marketDataReadyListener=lambda snapshot: None):
        self.__marketDataReadyListener = marketDataReadyListener
        _subscribeAllItems(len(self.optionChains.values()),
                           self.__onAllChainMarketDataSubscribed,
                           self.__subscibeAllChains)

    def __subscibeAllChains(self, observable):
        for optionChainMarketData in self.chains.values():
            optionChainMarketData.subscribe(observable.on_next)

    def unsubscribe(self):
        for optionChainMarketData in self.chains.values():
            optionChainMarketData.unsubscribe()
        self.__isDataAvailable = False
        print('Option chains market data for ' + self.symbol +
              ' on expirations '+str(self.expirations) + ' are now unsubscribed.')

    def __onAllChainMarketDataSubscribed(self):
        self.__isDataAvailable = True
        print('Option chains market data for ' + self.symbol +
              ' on expirations '+str(self.expirations) + ' are now subscribed.')
        self.__marketDataReadyListener(self)
        del self.__marketDataReadyListener

    def __nonzero__(self):
        return self.__isDataAvailable

    def keys(self):
        return self.chains.keys()

    def __getitem__(self, expiration):
        return self.chains[expiration]

    def __len__(self):
        return self.__noOfChains

    def __str__(self):
        return 'Option chains market data for ' + \
            str(self.symbol) + ' on expirations ' + \
            str(self.expirations)

###################################################################


_markteReqThrottle = 0.1

_putCallVolume = 100
_openInterest = 101
_histVolatility = 104
_avOptionVolume = 105
_impliedVolatility = 106
_tickList = [_putCallVolume, _openInterest,
             _histVolatility, _avOptionVolume, _impliedVolatility]
_genericTickList = ','.join([str(i) for i in _tickList])


def _isMarketDataReady(marketData):
    return not math.isnan(marketData.callOpenInterest) and \
        not math.isnan(marketData.bid) \
        and hasattr(marketData, 'modelGreeks')


def _requestMarketData(contract):
    return getApplication().reqMktData(contract, genericTickList=_genericTickList)


def _cancelMarketData(contract):
    getApplication().cancelMktData(contract)


def _fromOptionDetailsToOptionMarketData(optionDetails):
    return rx.of(*list(optionDetails.values())).pipe(
        map(lambda detail: OptionMarketData(detail)),
        to_dict(lambda marketData: marketData.strike,
                lambda marketData: marketData)
    ).run()


def _subscribeAllItems(noOfItems, onCompleted, subscribeAllFunc):
    observable = Subject()
    observable.pipe(
        take(noOfItems)
    ) .subscribe(on_completed=onCompleted)
    subscribeAllFunc(observable)
