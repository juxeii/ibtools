import pickle
from ib_insync import Option
from IPython.utils import io
from datetime import timedelta
from os.path import exists
from tools import _app, today, toDate, toDates, toTWSDateFromDate


class OptionChain:
    def __init__(self, underlyingContract, expiration, calls, puts):
        self.underlyingContract = underlyingContract
        self.symbol = underlyingContract.symbol
        self.expiration = expiration
        self.calls = calls
        self.puts = puts

    def __str__(self):
        return 'Option chain for '+str(self.symbol) + ' on '+str(self.expiration)


def getOptionChains(underlyingContract, *dates):
    _app().qualifyContracts(underlyingContract)
    expirations = _filterExpirations(toDates(*dates), underlyingContract)
    return _chainsForExpirations(underlyingContract, expirations)


def getOptionChainsInDateRange(underlyingContract, beginDate, endDate):
    _app().qualifyContracts(underlyingContract)
    chainExpirations = _expirationsOfChain(underlyingContract)
    expirationsInRange = _expirationsInDateRange(toDate(beginDate),
                                                 toDate(endDate),
                                                 chainExpirations)
    return _chainsForExpirations(underlyingContract, expirationsInRange)


def getOptionChainsInDteRange(underlyingContract, lowerDte, higherDte):
    currentDay = today()
    return getOptionChainsInDateRange(underlyingContract,
                                      currentDay+timedelta(days=lowerDte),
                                      currentDay+timedelta(days=higherDte))


###################################################################


def _filterExpirations(dates, contract):
    chainExpirations = _expirationsOfChain(contract)
    return [date for date in dates if date in chainExpirations]


def _chainsForExpirations(underlyingContract, expirations):
    storedChains = _loadValidChains(underlyingContract)
    print(underlyingContract.symbol+":storedChains "+str(storedChains))
    cachedChains = _cachedChains(storedChains, expirations)
    print(underlyingContract.symbol+":cachedChains "+str(cachedChains))
    newChains = _newChains(underlyingContract, storedChains, expirations)
    print(underlyingContract.symbol+":newChains "+str(newChains))

    return _serializeAndReturnChains(underlyingContract, cachedChains, newChains, storedChains)


def _cachedChains(storedChains, expirations):
    storedExpirations = list(storedChains.keys())
    cachedExpirations = _cachedExpirations(storedExpirations, expirations)

    return {expiration: storedChains[expiration] for expiration in cachedExpirations}


def _newChains(underlyingContract, storedChains, expirations):
    storedExpirations = list(storedChains.keys())
    notCachedExpirations = _notCachedExpirations(storedExpirations, expirations)

    return {expiration: _createContractsForExpiration(underlyingContract, expiration)
            for expiration in notCachedExpirations}


def _serializeAndReturnChains(underlyingContract, cachedChains, newChains, storedChains):
    chainsToReturn = {**cachedChains, **newChains}
    chainsToSerialize = {**storedChains, **newChains}
    _serializeChains(underlyingContract, chainsToSerialize)
    return chainsToReturn


def _expirationsInDateRange(beginDate, endDate, expirations):
    return [expiration for expiration in expirations if beginDate <= expiration <= endDate]


def _cachedExpirations(storedExpirations, requestedExpirations):
    return [expiration for expiration in requestedExpirations if expiration in storedExpirations]


def _notCachedExpirations(storedExpirations, requestedExpirations):
    return [expiration for expiration in requestedExpirations if not expiration in storedExpirations]


def _chain(contract):
    optChain = _app().reqSecDefOptParams(underlyingSymbol=contract.symbol,
                                         futFopExchange='',
                                         underlyingSecType='STK',
                                         underlyingConId=contract.conId)
    return _filterExchangeFromChain(optChain, 'SMART')


def _contract(symbol, expiration, strike, right, exchange):
    return Option(symbol, toTWSDateFromDate(expiration), strike, right, exchange)


def _contractsForExpiration(chain, right, expiration):
    contracts = [_contract(chain.tradingClass,
                           expiration,
                           strike,
                           right,
                           chain.exchange)
                 for strike in chain.strikes]
    with io.capture_output():  # Trying to suppress Error 200 from TWS
        return _app().qualifyContracts(*contracts)


def _contractsByStrikes(chain, right, expiration):
    contracts = _contractsForExpiration(chain, right, expiration)
    return {contract.strike:  contract for contract in contracts}


def _createContractsForExpiration(underlyingContract, expiration):
    print("Creating option contracts for " + underlyingContract.symbol+" "+str(expiration)+" ...")

    chain = _chain(underlyingContract)
    callContracts = _contractsByStrikes(chain, "C", expiration)
    putContracts = _contractsByStrikes(chain, "P", expiration)

    print("Created option contracts for " + underlyingContract.symbol+" "+str(expiration)+".")
    return OptionChain(underlyingContract, expiration, callContracts, putContracts)


def _expirationsOfChain(contract):
    return toDates(*_chain(contract).expirations)


def _timeDeltaInDays(earlyDate, lateDate):
    return (lateDate - earlyDate).days


def _dte(expiration):
    return _timeDeltaInDays(today(), expiration)


def _filterExchangeFromChain(chain, exchange):
    return next(filter(lambda x: x.exchange == exchange, chain))


def _fileNameForChains(contract):
    return contract.symbol+'_'+str(contract.conId)+'_optionchains'


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


def _loadValidChains(contract):
    storedChains = _deSerializeChains(contract)
    validStoredChains = _filterOutdatedChains(storedChains)
    _serializeChains(contract, validStoredChains)
    return validStoredChains
