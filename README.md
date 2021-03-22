# About
It is very cumbersome for option traders to create the option chains from the IB TWS API.

With this tool you can create the chains in a simple and effective manner.
It comes with a caching mechanism, which will store already created
contracts, such that at application restart, not all have to be requested again.

# Installation
I think python>=3.6 is required, although I did not test it.
You can install it with
```bat
pip install ibtools
```
This tool needs [ib_insync] to work and your application has to use it.

# Usage
The tool needs the IB object from ib_insync in order to work:
```python
import ibtools as ibt

....

ib = IB()
ibt.setApplication(ib) # Neeeded!
ib.connect(port=7497, clientId=1)
```
The first example shows you how to request option chains for specific expiration dates:
```python
ubx = Stock(symbol='UBX', exchange='SMART/AMEX')
chains = ibt.getOptionChains(ubx, '20210416', '20210521')
#chains = ibt.getOptionChains(ubx, datetime.date(2021, 4, 16))
print(chains)
```
You can pass any number of dates and you can pass them also as datetimes.
A date is ignored, if it does not correspond to a valid expiration.
The `chains` variable holds a dictionary, where the keys are the valid expirations, given as datetimes.

To access a specific option from the chains, you have to specify either calls or puts contracts, and the strike:
```python
print(chains[datetime.date(2021, 4, 16)].calls[5.0])
print(chains[datetime.date(2021, 4, 16)].puts[5.0])
```
The result is an `OptionDetail` object and the output above should give something like:
```python
OptionDetail:
Option: Option(conId=472345688, symbol='UBX', lastTradeDateOrContractMonth='20210416', strike=5.0, right='C', multiplier='100', exchange='SMART', currency='USD', localSymbol='UBX   210416C00005000', tradingClass='UBX')
Underlying: Stock(conId=316544337, symbol='UBX', exchange='SMART', primaryExchange='NASDAQ', currency='USD', localSymbol='UBX', tradingClass='NMS')
```
Here, the option contract and the underlying contract are stored side by side.

The next example shows you how to create chains which fall in a specific date range:
```python
chains=ibt.getOptionChainsInDateRange(ubx, '20210416', '20210521')
print(chains)
```
The given dates are included if they represent valid expirations.

You can also specify days to expiration in a range:
```python
chains=ibt.getOptionChainsInDteRange(ubx, 20, 30)
print(chains)
```
-----------------------------------------------
You can now also subscribe to realtime market data for the option chains.
```python
ubx = Stock(symbol='UBX', exchange='SMART/AMEX')
chains = ibt.getOptionChains(ubx, '20210416', '20210521')
marketDataForChains=ibt.OptionChainsMarketData(chains)
print(marketDataForChains[datetime.date(2021, 4, 16)])

def onChainsMktDataReady(marketData):
    print(str(marketData) + ' is now available')
marketDataForChains.subscribe(onChainsMktDataReady)
```
Here, we first create an `OptionChainsMarketData` object with the chains we have at hand. At this point in time the market data are not yet subscribed. For that, we need to call `subscribe` and pass it a listener function, which will notify us if the received data is ready and complete. You do not have to pass this listener...you can just simply wait until `OptionChainsMarketData` is `true`
```python
ib.loopUntil(marketDataForChains)
# now marketDataForChains has valid market data
```

To access realtime option data you then write
```python
marketDataForChains[datetime.date(2021, 4, 16)].calls[5.0].marketData
marketDataForChains[datetime.date(2021, 4, 16)].calls[5.0].undMarketData
```
The first line shows the option data and the second the data for the underlying.

In order to keep the system performant, you should unsubscribe from the chain data when not needed:
```python
marketDataForChains.unsubscribe()
```
**Note that subscriptions only work when the market is open!**
# Misc
Please be aware that this interface is subject to change.

The main selling point is the speed gain if you request chains again.
All cached contracts are stored in binary files where your algorithm runs.
You should see an almost instant loading of already requested chains.
The tool will also cleanup the cached files, such that outdated chains are removed.
This will keep the file sizes as small as possible.

I will later add functions to query all necessary data for chains(like the greeks)...be patient :)
So far I have only done testing for stocks as underlyings.
Further, the tool will only work for options which are accessible for 'SMART' exchanges.

Please let me know if you encounter bugs.

[ib_insync]: https://github.com/erdewit/ib_insync