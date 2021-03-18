import datetime
import pickle
from ib_insync import Option
from IPython.utils import io
from datetime import timedelta
from os.path import exists


class OptionChain:
    def __init__(self, symbol, expiration, calls, puts):
        self.symbol = symbol
        self.expiration = expiration
        self.calls = calls
        self.puts = puts

    def __str__(self):
        return 'Option chain for '+str(self.symbol) + '\n'+str(self.expiration)


def setApplication(app):
    global __app__
    __app__ = app


def getOptionContracts(contract, *dates):
    __app__.qualifyContracts(contract)
    expirations = __filterExpirations(__toDates(*dates), contract)
    return __contractsForExpirations(contract, expirations)


def getOptionContractsInDateRange(contract, beginDate, endDate):
    __app__.qualifyContracts(contract)
    return __optionContractsForRange(contract,  __toDate(beginDate), __toDate(endDate))


def getOptionContractsInDaysRange(contract, lowerDaysFromNow, higherDaysFromNow):
    today = __today()
    return getOptionContractsInDateRange(contract,
                                         today+timedelta(days=lowerDaysFromNow),
                                         today+timedelta(days=higherDaysFromNow))


def getOptionContractsUpUntilDays(contract, daysToExpiration):
    return getOptionContractsInDaysRange(contract, 0, daysToExpiration)


###################################################################
__app__ = None
__twsDateFormat = '%Y%m%d'


def __filterExpirations(dates, contract):
    chainExpirations = __expirationsOfChain(contract)
    return [date for date in dates if date in chainExpirations]


def __optionContractsForRange(contract, beginDate, endDate):
    chainExpirations = __expirationsOfChain(contract)
    expirationsInRange = __expirationsInRange(beginDate, endDate, chainExpirations)

    return __contractsForExpirations(contract, expirationsInRange)


def __contractsForExpirations(contract, expirations):
    storedChains = __loadValidOptionChains(contract)
    cachedChains = __cachedChains(storedChains, expirations)
    newChains = __newsChains(contract, storedChains, expirations)
    print("storedChains "+str(storedChains)+'\n')
    print("cachedChains "+str(cachedChains)+'\n')
    print("newChains "+str(newChains)+'\n')

    return __serializeAndReturnChains(contract, cachedChains, newChains, storedChains)


def __cachedChains(storedChains, expirations):
    storedExpirations = list(storedChains.keys())
    cachedExpirations = __cachedExpirations(storedExpirations, expirations)

    return {expiration: storedChains[expiration] for expiration in cachedExpirations}


def __newsChains(contract, storedChains, expirations):
    storedExpirations = list(storedChains.keys())
    notCachedExpirations = __notCachedExpirations(storedExpirations, expirations)

    return {expiration: __createContractsForExpiration(contract, expiration)
            for expiration in notCachedExpirations}


def __serializeAndReturnChains(contract, cachedChains, newChains, storedChains):
    chainsToReturn = {**cachedChains, **newChains}
    chainsToSerialize = {**storedChains, **newChains}
    __serializeOptionChains(contract, chainsToSerialize)
    return chainsToReturn


def __expirationsInRange(beginDate, endDate, expirations):
    return [expiration for expiration in expirations if beginDate <= expiration <= endDate]


def __cachedExpirations(storedExpirations, requestedExpirations):
    return [expiration for expiration in requestedExpirations if expiration in storedExpirations]


def __notCachedExpirations(storedExpirations, requestedExpirations):
    return [expiration for expiration in requestedExpirations if not expiration in storedExpirations]


def __createContractsForExpiration(contract, expiration):
    print("Creating option contracts for " + contract.symbol+" "+str(expiration)+" ...")

    optionChain = __optionChain(contract)
    callContracts = __callContractsByStrikes(optionChain, expiration)
    putContracts = __putContractsByStrikes(optionChain, expiration)

    print("Created option contracts for " + contract.symbol+" "+str(expiration)+".")
    return OptionChain(contract.symbol, expiration, callContracts, putContracts)


def __toDate(date):
    return __toDateFromTWSDate(date)


def __toDates(*dates):
    return [__toDate(date) for date in dates]


def __today():
    return datetime.date.today()


def __expirationsOfChain(contract):
    return __toDates(*__optionChain(contract).expirations)


def __toDateFromTWSDate(twsDate):
    if isinstance(twsDate, str):
        return datetime.datetime.strptime(twsDate, __twsDateFormat).date()
    return twsDate


def __toTWSDateFromDate(date):
    if isinstance(date, str):
        return date
    return date.strftime(__twsDateFormat)


def __timeDeltaInDays(earlyDate, lateDate):
    return (lateDate - earlyDate).days


def __daysUntilExpiration(expiration):
    return __timeDeltaInDays(__today(), expiration)


def __filterExchangeFromOptionChain(optChain, exchange):
    return next(filter(lambda x: x.exchange == exchange, optChain))


def __optionChain(contract):
    optChain = __app__.reqSecDefOptParams(underlyingSymbol=contract.symbol,
                                          futFopExchange='',
                                          underlyingSecType='STK',
                                          underlyingConId=contract.conId)
    return __filterExchangeFromOptionChain(optChain, 'SMART')


def __contract(symbol, expiration, strike, right, exchange):
    return Option(symbol, __toTWSDateFromDate(expiration), strike, right, exchange)


def __contractsForExpiration(optionChain, right, expiration):
    contracts = [__contract(optionChain.tradingClass,
                            expiration,
                            strike,
                            right,
                            optionChain.exchange)
                 for strike in optionChain.strikes]
    with io.capture_output():
        return __app__.qualifyContracts(*contracts)


def __callContractsByStrikes(optionChain, expiration):
    callContracts = __contractsForExpiration(optionChain, "C", expiration)
    return {callContract.strike:  callContract for callContract in callContracts}


def __putContractsByStrikes(optionChain, expiration):
    putContracts = __contractsForExpiration(optionChain, "P", expiration)
    return {putContract.strike:  putContract for putContract in putContracts}


def __fileNameForOptionChains(contract):
    return contract.symbol+'_'+str(contract.conId)+'_optionchains'


def __serializeOptionChains(contract, optionChains):
    filename = __fileNameForOptionChains(contract)
    outfile = open(filename, 'wb')
    pickle.dump(optionChains, outfile)
    outfile.close()


def __deSerializeOptionChains(contract):
    filename = __fileNameForOptionChains(contract)
    if exists(filename) == False:
        emptyoptionChains = dict()
        __serializeOptionChains(contract, emptyoptionChains)
        return emptyoptionChains

    infile = open(filename, 'rb')
    optionChains = pickle.load(infile)
    infile.close()
    return optionChains


def __loadValidOptionChains(contract):
    storedChains = __deSerializeOptionChains(contract)
    validStoredChains = {expiration: chain for expiration, chain in storedChains.items()
                         if __daysUntilExpiration(expiration) >= 0}
    __serializeOptionChains(contract, validStoredChains)
    return validStoredChains
