import ibtools as ibt
from tools import toTWSDateFromDate, today, toDate, toDates, OptionDetail
import pickle
from IPython.utils import io
from datetime import timedelta
from os.path import exists
from ib_insync import Option, FuturesOption


class OptionChain:

    def __init__(self, underlying, expiration, calls, puts):
        self.underlying = underlying
        self.symbol = underlying.symbol
        self.expiration = expiration
        self.calls = calls
        self.puts = puts
        self.callContracts = self.__getContracts(self.calls)
        self.putContracts = self.__getContracts(self.puts)

    def __getContracts(self, detailsByStrike):
        return [detail.option for detail in detailsByStrike.values()]

    def __str__(self):
        return 'Option chain for '+str(self.symbol) + ' on '+str(self.expiration)


def getOptionChains(underlying, *dates):
    typedDates = toDates(*dates)
    def isExpiration(expiration): return expiration in typedDates

    return _chainsForValidDates(underlying, isExpiration)


def getOptionChainsInDateRange(underlying, beginDate, endDate):
    typedBeginDate = toDate(beginDate)
    typedEndDate = toDate(endDate)

    def isExpiration(expiration): return _isDateInRange(expiration,
                                                        typedBeginDate,
                                                        typedEndDate)

    return _chainsForValidDates(underlying, isExpiration)


def getOptionChainsInDteRange(underlying, lowerDte, higherDte):
    currentDay = today()
    return getOptionChainsInDateRange(underlying,
                                      currentDay+timedelta(days=lowerDte),
                                      currentDay+timedelta(days=higherDte))


###################################################################

def _chainsForValidDates(underlying, isExpiration):
    ibt.app.qualifyContracts(underlying)

    twsChains = _chainByExpiration(underlying)
    validDates = [expiration for expiration in twsChains if isExpiration(expiration)]
    storedChains = _loadValidChains(underlying)
    cachedChains = _cachedChains(storedChains, validDates)
    if len(cachedChains) == len(validDates):
        return cachedChains

    newChains = _newChainsFromTwsChains(underlying, twsChains, validDates, cachedChains)
    return _serializeAndReturnChains(underlying, cachedChains, newChains, storedChains)


def _cachedChains(storedChains, validDates):
    return {expiration: storedChains[expiration] for expiration in validDates
            if expiration in storedChains}


def _newChainsFromTwsChains(underlying, twsChains, validDates, cachedChains):
    fromTwsChains = {expiration: twsChains[expiration] for expiration in validDates
                     if expiration not in cachedChains}
    return {expiration: _createContractsForExpiration(underlying,
                                                      chain,
                                                      expiration)
            for expiration, chain in fromTwsChains.items()}


def _chainByExpiration(underlying):
    chains = _chainsForSecType(underlying)
    return {toDate(expiration): chain for chain in chains for expiration in chain.expirations}


def _loadValidChains(contract):
    storedChains = _deSerializeChains(contract)
    validStoredChains = _filterOutdatedChains(storedChains)
    _serializeChains(contract, validStoredChains)

    return validStoredChains


def _createContractsForExpiration(underlying, chain, expiration):
    calls = _contractsByStrikes(underlying, chain, "C", expiration)
    puts = _contractsByStrikes(underlying, chain, "P", expiration)
    return OptionChain(underlying, expiration, calls, puts)


def _filterExchangeFromChains(chains, exchange):
    return [chain for chain in chains if chain.exchange == exchange]


def _serializeAndReturnChains(underlying, cachedChains, newChains, storedChains):
    chainsToReturn = {**cachedChains, **newChains}
    print(f"{underlying.symbol} loaded chains: {chainsToReturn}")
    chainsToSerialize = {**storedChains, **newChains}
    _serializeChains(underlying, chainsToSerialize)

    return chainsToReturn


def _isDateInRange(date, beginDate, endDate):
    return beginDate <= date <= endDate


def _chains(contract):
    futFopExchange = contract.exchange if _isFuture(contract) else ''
    return ibt.app.reqSecDefOptParams(underlyingSymbol=contract.symbol,
                                      futFopExchange=futFopExchange,
                                      underlyingSecType=contract.secType,
                                      underlyingConId=contract.conId)


def _isFuture(contract):
    return contract.secType == 'FUT'


def _chainsForExchange(contract, exchange):
    return _filterExchangeFromChains(_chains(contract), exchange)


def _chainsForSecType(contract):
    if _isFuture(contract):
        return _chainsForExchange(contract, contract.exchange)
    return _chainsForExchange(contract, 'SMART')


def _createOption(underlying, strike, right, expiration):
    option = FuturesOption() if _isFuture(underlying) else Option()
    option.symbol = underlying.symbol
    option.lastTradeDateOrContractMonth = toTWSDateFromDate(expiration)
    option.strike = strike
    option.right = right
    option.exchange = underlying.exchange
    return option


def _optionDetailsForExpiration(underlying, chain, right, expiration):
    options = [_createOption(underlying, strike, right, expiration) for strike in chain.strikes]
    return _filterValidOptions(underlying, options)


def _filterValidOptions(underlying, options):
    with io.capture_output():  # Trying to suppress Error 200 from TWS
        validOptions = ibt.app.qualifyContracts(*options)
    return [OptionDetail(option, underlying) for option in validOptions]


def _contractsByStrikes(underlying, chain, right, expiration):
    optionDetails = _optionDetailsForExpiration(underlying, chain, right, expiration)
    return {optionDetail.strike:  optionDetail for optionDetail in optionDetails}


def _timeDeltaInDays(earlyDate, lateDate):
    return (lateDate - earlyDate).days


def _dte(expiration):
    return _timeDeltaInDays(today(), expiration)


def _fileNameForChains(contract):
    return f"{ibt.cacheFilePath} {contract.symbol} {contract.conId}_optionchains"


def _deSerializeChains(contract):
    filename = _fileNameForChains(contract)
    if exists(filename) == False:
        emptyChains = dict()
        _serializeChains(contract, emptyChains)
        return emptyChains

    infile = open(filename, 'rb')
    storedChains = pickle.load(infile)
    infile.close()

    return storedChains


def _serializeChains(contract, chains):
    filename = _fileNameForChains(contract)
    outfile = open(filename, 'wb')
    pickle.dump(chains, outfile)
    outfile.close()


def _filterOutdatedChains(storedChains):
    return {expiration: chain for expiration, chain in storedChains.items()
            if _dte(expiration) >= 0}
