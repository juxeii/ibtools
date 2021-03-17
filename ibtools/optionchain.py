from os.path import exists
import datetime
import pickle
import ib_insync
from IPython.utils import io


def getOptionContracts(contract, expiration):
    __ibs__.qualifyContracts(contract)

    if isinstance(expiration, str):
        expiration = __toDateFromTWSDate(expiration)

    if not __toTWSDateFromDate(expiration) in __optionChain(contract).expirations:
        print(str(expiration)+" for " + contract.symbol+" is not a valid expiration date!")
        return {'calls': {}, 'puts': {}}

    storedChains = __loadValidOptionChains(contract)
    if expiration in storedChains.keys():
        return storedChains[expiration]

    optionContracts = __optionContractsForExpiration(contract, expiration)
    __serializeOptionChains(contract, dict([(expiration, optionContracts)]))

    return optionContracts


def getOptionContractsUpUntilDays(contract, daysToExpiration):
    __ibs__.qualifyContracts(contract)

    storedChains = __loadValidOptionChains(contract)
    storedExpirations = list(storedChains.keys())
    chainExpirations = __datesFromTWSDates(__optionChain(contract).expirations)

    expirationsUntilDays = __getExpirationsUpUntilDays(storedExpirations,
                                                       chainExpirations, daysToExpiration)

    validStoredChains = {expiration: chain for expiration, chain in storedChains.items()
                         if __daysUntilExpiration(expiration) >= 0}

    newChains = {expiration: getOptionContracts(contract, expiration)
                 for expiration in expirationsUntilDays}

    optionChains = {**validStoredChains, **newChains}
    __serializeOptionChains(contract, optionChains)

    return optionChains


###################################################################
__ibs__ = None

__twsDateFormat = '%Y%m%d'


def __optionContractsForExpiration(contract, expiration):
    print("Creating option contracts for " + contract.symbol+" "+str(expiration)+" ...")
    optionChain = __optionChain(contract)
    callsByStrike = __callOptionContractsByStrikes(optionChain, expiration)
    putsByStrike = __putOptionContractsByStrikes(optionChain, expiration)
    print("Created option contracts for " + contract.symbol+" "+str(expiration)+".")

    return {'calls': callsByStrike, 'puts': putsByStrike}


def __getExpirationsUpUntilDays(storedExpirations, chainExpirations, daysToExpiration):
    filteredExpirations = [expiration for expiration in chainExpirations
                           if not expiration in storedExpirations]

    return __expirationsUntilDays(filteredExpirations, daysToExpiration)


def __toDateFromTWSDate(twsDate):
    return datetime.datetime.strptime(twsDate, __twsDateFormat).date()


def __toTWSDateFromDate(date):
    return date.strftime(__twsDateFormat)


def __datesFromTWSDates(twsDates):
    return [__toDateFromTWSDate(twsDate) for twsDate in twsDates]


def __timeDeltaInDays(earlyDate, lateDate):
    delta = (lateDate - earlyDate).total_seconds()
    return delta/86400


def __daysUntilExpiration(expiration):
    return __timeDeltaInDays(datetime.date.today(), expiration)


def __expirationsUntilDays(expirations, maxDays):
    return [expiration for expiration in expirations if __daysUntilExpiration(expiration) <= maxDays]


def __filterExchangeFromOptionChain(optChain, exchange):
    return next(filter(lambda x: x.exchange == exchange, optChain))


def __optionChain(contract):
    optChain = __ibs__.reqSecDefOptParams(underlyingSymbol=contract.symbol, futFopExchange='',
                                          underlyingSecType='STK', underlyingConId=contract.conId)
    return __filterExchangeFromOptionChain(optChain, 'SMART')


def __optionContract(symbol, expiration, strike, right, exchange):
    return ib_insync.Option(
        symbol, __toTWSDateFromDate(expiration), strike, right, exchange)


def __optionContractsForStrikes(optionChain, right, expiration):
    optionContracts = [__optionContract(optionChain.tradingClass, expiration, strike, right, optionChain.exchange)
                       for strike in optionChain.strikes]
    with io.capture_output():
        return __ibs__.qualifyContracts(*optionContracts)


def __callOptionContractsForExpiration(optionChain, expiration):
    return __optionContractsForStrikes(optionChain, "C", expiration)


def __callOptionContractsByStrikes(optionChain, expiration):
    callContracts = __callOptionContractsForExpiration(optionChain, expiration)
    return dict([(contract.strike, contract) for contract in callContracts])


def __putOptionContractsForExpiration(optionChain, expiration):
    return __optionContractsForStrikes(optionChain, "P", expiration)


def __putOptionContractsByStrikes(optionChain, expiration):
    putContracts = __putOptionContractsForExpiration(optionChain, expiration)
    return dict([(contract.strike, contract) for contract in putContracts])


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
