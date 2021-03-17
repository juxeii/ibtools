# About
It is very cumbersome for option trades to create the option chains.
With this tool you can create the chains in a simple and effective manner.
It comes with a caching mechanism, which will store already created
contracts, such that at application restart not all have to be requested again.

# Installation
I think python>=3.7 is required, although I did not tested it.
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
ibt.setApplication(ib)
ib.connect(port=7497, clientId=1)
```

To request all option chains for the next 60 days:
```python
chain = ibt.getOptionContractsUpUntilDays(aapl, 60)
print(chain)
```
The chains are stored in dictionaries, where the first level key is the expiration date.
The second key is the contract type, like calls or puts.
The third key is the strike price.
So, to accesss all call contracts of expiration date 2021-03-19, you write
```python
aapl=Stock(symbol='AAPL', exchange='SMART/AMEX')
chains = ibt.getOptionContractsUpUntilDays(aapl, 60)
print(chains[datetime.date(2021, 3, 19)]) #all contracts for this expiration date
print(chains[datetime.date(2021, 3, 19)]['calls']) #all call contracts for this date
print(chains[datetime.date(2021, 3, 19)]['puts']) #all call contracts for this date
print(chains[datetime.date(2021, 3, 19)]['puts'][122.0]) #put contract for this date and strike price)
```

To request a single option chain for a specific expiration date:
```python
aapl=Stock(symbol='AAPL', exchange='SMART/AMEX')
chain = ibt.getOptionContracts(aapl, datetime.date(2021, 3, 19))
print(chain['calls'])
print(chain['puts'])
```
Here you can also provide a date in the usual string format of TWS:
```python
chain = ibt.getOptionContracts(aapl, '20210319'))
```
However, accessing option chains is not possible with string dates.
Use the dateformat as described above.

[ci-image]: https://github.com/erdewit/ib_insync
[ci-link]: https://github.com/juxeii/memoization/actions?query=workflow%3Abuild
[memoization]: https://en.wikipedia.org/wiki/Memoization