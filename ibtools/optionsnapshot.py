from rx.subject import Subject
from rx.operators import *
from tools import _app, toDate
from IPython.utils import io


def getOptionChainSnapshot(optionChain, onChainSnapshotAvailable=lambda snapshot: None):
    return OptionChainSnapshot(optionChain, onChainSnapshotAvailable)


def getOptionChainsSnapshot(optionChains, onChainsSnapshotAvailable=lambda snapshots: None):
    return OptionChainsSnapshot(optionChains, onChainsSnapshotAvailable)


class OptionSnapshot:

    def __init__(self, marketData, undMarketData):
        self.marketData = marketData
        self.undMarketData = undMarketData
        self.contract = marketData.contract
        self.undContract = undMarketData.contract
        self.symbol = self.contract.symbol
        self.expiration = toDate(self.contract.lastTradeDateOrContractMonth)
        self.strike = self.contract.strike
        self.right = self.contract.right

    def __str__(self):
        return 'Option snapshot '+str(self.symbol) + ' on ' + \
            str(self.expiration) + ' at ' + str(self.strike)+str(self.right)


class OptionChainSnapshot:

    def __init__(self, optionChain, chainSnapshotAvailableListener):
        self.optionChain = optionChain
        self.underlyingContract = optionChain.underlyingContract
        self.chainSnapshotAvailableListener = chainSnapshotAvailableListener
        self.symbol = optionChain.symbol
        self.expiration = optionChain.expiration
        self.isDataAvailable = False
        self.chain = list(optionChain.calls.values())+list(optionChain.puts.values())

        print('Creating option chain snapshot for ' +
              str(self.symbol)+' on '+str(self.expiration)+'...')
        self.__subscribeToMarketData()

    def __subscribeToMarketData(self):
        self.undMarketData = _requestMarketData(self.underlyingContract)

        self.__dataStream = _MarketDataStream()
        self.__dataStream.observable \
            .pipe(
                filter(lambda data: data.contract in self.chain),
                filter(_isMarketDataReady),
                distinct(lambda data: data.contract),
                take(len(self.chain)),
                do_action(lambda data: _cancelMarketData(data.contract)),
                group_by(lambda data: data.contract.right == 'C'),
                flat_map(lambda grp: grp.pipe(to_list()))
            ) .subscribe(on_next=self.__onMarketDataByRight,
                         on_completed=self.__onAllMarketDataReady)

        _requestMarketDataForChain(self.chain)

    def __onMarketDataByRight(self, marketDataByRight):
        if marketDataByRight[0].contract.right == 'C':
            self.calls = _snapshotByStrike(marketDataByRight, self.undMarketData)
        else:
            self.puts = _snapshotByStrike(marketDataByRight, self.undMarketData)

    def __onAllMarketDataReady(self):
        with io.capture_output():
            _cancelMarketData(self.underlyingContract)
        self.isDataAvailable = True
        print('Option chain snapshot for ' + self.symbol+' on '+str(self.expiration) + ' created.')
        self.chainSnapshotAvailableListener(self)

    def __nonzero__(self):
        return self.isDataAvailable

    def __str__(self):
        return 'Option chain snapshot for ' + str(self.symbol) + ' on '+str(self.expiration)


class OptionChainsSnapshot:

    def __init__(self, optionChains, chainsSnapshotAvailableListener):
        self.optionChains = optionChains
        self.symbol = next(iter(optionChains.values())).symbol
        self.expirations = list(optionChains.keys())
        self.chainsSnapshotAvailableListener = chainsSnapshotAvailableListener
        self.isDataAvailable = False
        print('Creating option chains snapshot for ' +
              str(self.symbol)+' on '+str(self.expirations)+'...')
        self.__requestChainsSnapshot(optionChains)

    def __requestChainsSnapshot(self, optionChains):
        sub = Subject()

        sub.pipe(
            take(len(optionChains.values())),
        ) .subscribe(on_completed=self.__onAllChainSnapshotsCreated)

        chainSnapshots = [getOptionChainSnapshot(chain, sub.on_next)
                          for chain in optionChains.values()]
        self.chainSnapshotsByExpiration = {chainSnapshot.expiration: chainSnapshot
                                           for chainSnapshot in chainSnapshots}

    def __onAllChainSnapshotsCreated(self):
        self.isDataAvailable = True
        print('Option chains snapshot for ' + self.symbol +
              ' on '+str(self.expirations) + ' created.')
        self.chainsSnapshotAvailableListener(self)

    def __nonzero__(self):
        return self.isDataAvailable

    def keys(self):
        return self.chainSnapshotsByExpiration.keys()

    def __getitem__(self, expiration):
        return self.chainSnapshotsByExpiration[expiration]

    def __str__(self):
        return 'Option chains snapshots for ' + \
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


class _MarketDataStream:
    def __init__(self):
        self.observable = Subject()
        _app().pendingTickersEvent += self.__onMarketData

    def __onMarketData(self, pendingTickers):
        for marketData in pendingTickers:
            self.observable.on_next(marketData)


def _snapshotByStrike(marketDataSet, undMarketData):
    return {marketData.contract.strike: OptionSnapshot(marketData, undMarketData) for marketData in marketDataSet}


def _isMarketDataReady(marketData):
    return True
    # return not math.isnan(marketData.bidSize)
    # return not math.isnan(marketData.callOpenInterest) and \
    #   not math.isnan(marketData.bid) \
    #  and hasattr(marketData, 'modelGreeks')


def _requestMarketDataForChain(chain):
    for contract in chain:
        _requestMarketData(contract)
        _app().sleep(_markteReqThrottle)


def _requestMarketData(contract):
    return _app().reqMktData(contract, genericTickList=_genericTickList)
    # return _app().reqMktData(contract, snapshot=True)


def _cancelMarketData(contract):
    _app().cancelMktData(contract)
