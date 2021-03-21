# About
It is very cumbersome for option trades to create the option chains.
With this tool you can create the chains in a simple and effective manner.
It comes with a caching mechanism, which will store already created
contracts, such that at application restart not all have to be requested again.

# Installation
I think python>=3.7 is required, although I did not test it.
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
aapl = Stock(symbol='AAPL', exchange='SMART/AMEX')
chains = ibt.getOptionContractsUpUntilDays(aapl, 60)
print(chains)
```
The chains are accessible via a dictionary, where the key is the expiration date.
Once you selected the expiration date, you can then access further with the OptionChain class:
```python
class OptionChain:
    def __init__(self, symbol, expiration, calls, puts):
        self.symbol = symbol
        self.expiration = expiration
        self.calls = calls
        self.puts = puts

    def __str__(self):
        return 'Option chain for '+str(self.symbol) + '\n'+str(self.expiration)
```

The _calls_ and _puts_ fields are als dictionaries, where keys are the strike prices.
So, to accesss all call contracts of expiration date 2021-03-19, you write
```python
aapl = Stock(symbol='AAPL', exchange='SMART/AMEX')
chains = ibt.getOptionContractsUpUntilDays(aapl, 60)
print(chains[datetime.date(2021, 4, 23)]) #all contracts for this expiration date
print(chains[datetime.date(2021, 4, 23)].calls) #all call contracts for this date
print(chains[datetime.date(2021, 4, 23)].puts) #all put contracts for this date
print(chains[datetime.date(2021, 4, 23)].calls[65.0]) #call contract for this date and strike price
print(chains[datetime.date(2021, 4, 23)].puts[75.0]) #put contract for this date and strike price
```

To request chains for specific expirations dates:
```python
aapl = Stock(symbol='AAPL', exchange='SMART/AMEX')
chains = ibt.getOptionContracts(aapl, datetime.date(2021, 3, 19), '20210326')
print(chains[datetime.date(2021, 3, 19)].calls)
print(chains[datetime.date(2021, 3, 26)].puts)
```
You can also provide a list of dates if you like, since this function takes variadic dates.
Further, you can mix the date formats.
However, accessing option chains is not possible with string dates.
Use the dateformat as described above.

To request chains for a date range:
```python
aapl = Stock(symbol='AAPL', exchange='SMART/AMEX')
chains = ibt.getOptionContractsInDateRange(aapl, '20210319', '20210429')  
```
This will return all chains that fall in between 2021-03-19 and 2021-04-29.

Sometimes you are interested to request chains that fall in between 30 to 60 days from now, because of theta decay ;)
```python
aapl = Stock(symbol='AAPL', exchange='SMART/AMEX')
chains = ibt.getOptionContractsInDaysRange(aapl, 30, 60)  
```
# Misc
Please be aware that this interface is subject to change.

The main selling point is the speed gain if you request chains again.
All cached contracts are stored in binary files where your algorithm runs.
You should see an almost instant loading of already requested chains.

I will later functions to query all necessary data like the greeks...be patient :)

Please let me know if you encounter bugs. Thx.

[ib_insync]: https://github.com/erdewit/ib_insync