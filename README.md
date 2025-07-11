# finance
Webpage built using Flask. CS50 Problem Set 9.

Implement a website via which users can “buy” and “sell” stocks, à la the below.

<img width="1357" alt="Screenshot 2024-03-22 at 14 54 02" src="https://github.com/cmartinezal/finance/assets/84383847/f147ec5e-a2d5-4665-9803-192cbf1afcdd">


## Background

If you’re not quite sure what it means to buy and sell stocks (i.e., shares of a company), head [here](https://www.investopedia.com/articles/basics/06/invest1000.asp) for a tutorial.

You’re about to implement C$50 Finance, a web app via which you can manage portfolios of stocks. Not only will this tool allow you to check real stocks’ actual prices and portfolios’ values, it will also let you buy (okay, “buy”) and sell (okay, “sell”) stocks by querying for stocks’ prices.

Indeed, there are tools (one is known as IEX) that let you download stock quotes via their API (application programming interface) using URLs like `https://api.iex.cloud/v1/data/core/quote/nflx?token=API_KEY`. Notice how Netflix’s symbol (NFLX) is embedded in this URL; that’s how IEX knows whose data to return. That link won’t actually return any data because IEX requires you to use an API key, but if it did, you’d see a response in JSON (JavaScript Object Notation) format like this:

```json
{
  "avgTotalVolume":6787785,
  "calculationPrice":"tops",
  "change":1.46,
  "changePercent":0.00336,
  "close":null,
  "closeSource":"official",
  "closeTime":null,
  "companyName":"Netflix Inc.",
  "currency":"USD",
  "delayedPrice":null,
  "delayedPriceTime":null,
  "extendedChange":null,
  "extendedChangePercent":null,
  "extendedPrice":null,
  "extendedPriceTime":null,
  "high":null,
  "highSource":"IEX real time price",
  "highTime":1699626600947,
  "iexAskPrice":460.87,
  "iexAskSize":123,
  "iexBidPrice":435,
  "iexBidSize":100,
  "iexClose":436.61,
  "iexCloseTime":1699626704609,
  "iexLastUpdated":1699626704609,
  "iexMarketPercent":0.00864679844447232,
  "iexOpen":437.37,
  "iexOpenTime":1699626600859,
  "iexRealtimePrice":436.61,
  "iexRealtimeSize":5,
  "iexVolume":965,
  "lastTradeTime":1699626704609,
  "latestPrice":436.61,
  "latestSource":"IEX real time price",
  "latestTime":"9:31:44 AM",
  "latestUpdate":1699626704609,
  "latestVolume":null,
  "low":null,
  "lowSource":"IEX real time price",
  "lowTime":1699626634509,
  "marketCap":192892118443,
  "oddLotDelayedPrice":null,
  "oddLotDelayedPriceTime":null,
  "open":null,
  "openTime":null,
  "openSource":"official",
  "peRatio":43.57,
  "previousClose":435.15,
  "previousVolume":2735507,
  "primaryExchange":"NASDAQ",
  "symbol":"NFLX",
  "volume":null,
  "week52High":485,
  "week52Low":271.56,
  "ytdChange":0.4790450244167119,
  "isUSMarketOpen":true
}
```

Notice how, between the curly braces, there’s a comma-separated list of key-value pairs, with a colon separating each key from its value. We’re going to be doing something very similar, with Yahoo Finance.


## Running

Start Flask’s built-in web server (within `finance/`):

```sh
$ flask run
```

Visit the URL outputted by flask to see the distribution code in action. You won’t be able to log in or register, though, just yet!

Within `finance/`, run `sqlite3 finance.db` to open `finance.db` with `sqlite3`. If you run `.schema` in the SQLite prompt, notice how ``finance.db`` comes with a table called `users`. Take a look at its structure (i.e., schema). Notice how, by default, new users will receive $10,000 in cash. But if you run `SELECT * FROM users;`, there aren’t (yet!) any users (i.e., rows) therein to browse.


## Specification

### register

Complete the implementation of `register` in such a way that it allows a user to register for an account via a form.

- Require that a user input a username, implemented as a text field whose `name` is `username`. Render an apology if the user’s input is blank or the username already exists.
- Require that a user input a password, implemented as a text field whose `name` is `password`, and then that same password again, implemented as a text field whose `name is `confirmation`. Render an apology if either input is blank or the - passwords do not match.
- Submit the user’s input via `POST` to `/register`.
- `INSERT` the new user into `users`, storing a hash of the user’s password, not the password itself. Hash the user’s password with `generate_password_hash` Odds are you’ll want to create a new template (e.g., `register.html`) that’s quite similar to `login.html`.
Once you’ve implemented register correctly, you should be able to register for an account and log in (since login and logout already work)! And you should be able to see your rows via phpLiteAdmin or `sqlite3`.

### quote

Complete the implementation of `quote` in such a way that it allows a user to look up a stock’s current price.

- Require that a user input a stock’s symbol, implemented as a text field whose `name` is `symbol`.
- Submit the user’s input via `POST` to `/quote`.
- Odds are you’ll want to create two new templates (e.g., `quote.html` and `quoted.html`). When a user visits `/quote` via `GET`, render one of those templates, inside of which should be an HTML form that submits to `/quote` via `POST`. In response to a `POST`, `quote` can render that second template, embedding within it one or more values from `lookup`.

### buy

Complete the implementation of `buy` in such a way that it enables a user to buy stocks.

- Require that a user input a stock’s symbol, implemented as a text field whose `name` is `symbol`. Render an apology if the input is blank or the symbol does not exist (as per the return value of `lookup`).
- Require that a user input a number of shares, implemented as a text field whose `name` is `shares`. Render an apology if the input is not a positive integer.
- Submit the user’s input via `POST` to `/buy`.
- Upon completion, redirect the user to the home page.
- Odds are you’ll want to call `lookup` to look up a stock’s current price.
- Odds are you’ll want to `SELECT` how much cash the user currently has in `users`.
- Add one or more new tables to `finance.db` via which to keep track of the purchase. Store enough information so that you know who bought what at what price and when.
- Use appropriate SQLite types.
     - Define `UNIQUE` indexes on any fields that should be unique.
     - Define (`non-UNIQUE`) indexes on any fields via which you will search (as via `SELECT` with `WHERE`).
     - Render an apology, without completing a purchase, if the user cannot afford the number of shares at the current price.
- You don’t need to worry about race conditions (or use transactions).
Once you’ve implemented buy correctly, you should be able to see users’ purchases in your new table(s) via phpLiteAdmin or `sqlite3`.

### index

Complete the implementation of `index` in such a way that it displays an HTML table summarizing, for the user currently logged in, which stocks the user owns, the numbers of shares owned, the current price of each stock, and the total value of each holding (i.e., shares times price). Also display the user’s current cash balance along with a grand total (i.e., stocks’ total value plus cash).

- Odds are you’ll want to execute multiple `SELECT`s. Depending on how you implement your table(s), you might find `GROUP BY HAVING SUM` and/or `WHERE` of interest.
- Odds are you’ll want to call `lookup` for each stock.

### sell

Complete the implementation of `sell` in such a way that it enables a user to sell shares of a stock (that he or she owns).

- Require that a user input a stock’s symbol, implemented as a `select` menu whose `name` is `symbol`. Render an apology if the user fails to select a stock or if (somehow, once submitted) the user does not own any shares of that stock.
- Require that a user input a number of shares, implemented as a text field whose `name` is `shares`. Render an apology if the input is not a positive integer or if the user does not own that many shares of the stock.
- Submit the user’s input via `POST` to `/sell`.
- Upon completion, redirect the user to the home page.
- You don’t need to worry about race conditions (or use transactions).

### history

Complete the implementation of `history` in such a way that it displays an HTML table summarizing all of a user’s transactions ever, listing row by row each and every buy and every sell.

- For each row, make clear whether a stock was bought or sold and include the stock’s symbol, the (purchase or sale) price, the number of shares bought or sold, and the date and time at which the transaction occurred.
- You might need to alter the table you created for buy or supplement it with an additional table. Try to minimize redundancies.

### personal touch

Implement at least one personal touch of your choice:

- Allow users to change their passwords.
- Allow users to add additional cash to their account.
- Allow users to buy more shares or sell shares of stocks they already own via index itself, without having to type stocks’ symbols manually.
- Require users’ passwords to have some number of letters, numbers, and/or symbols.
- Implement some other feature of comparable scope.


## Testing

Be sure to test your web app manually, as by

- registering a new user and verifying that their portfolio page loads with the correct information,
- requesting a quote using a valid stock symbol,
- purchasing one stock multiple times, verifying that the portfolio displays correct totals,
- selling all or some of a stock, again verifying the portfolio, and
- verifying that your history page shows all transactions for your logged in user.

Also test some unexpected usage, as by

- inputting alphabetical strings into forms when only numbers are expected,
- inputting zero or negative numbers into forms when only positive numbers are expected,
- inputting floating-point values into forms when only integers are expected,
- trying to spend more cash than a user has,
- trying to sell more shares than a user has,
- inputting an invalid stock symbol, and
- including potentially dangerous characters like ' and ; in SQL queries.

<img width="1191" alt="Screenshot 2024-03-21 at 18 58 21" src="https://github.com/cmartinezal/finance/assets/84383847/3a19e950-234a-4233-81c9-f423f2bde867">

