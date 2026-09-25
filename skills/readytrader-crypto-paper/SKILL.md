---
name: readytrader-crypto-paper
description: "Paper BTC trading through the ReadyTrader-Crypto MCP tools: price, risk check, paper order. Never live."
version: 2.0.0
author: Bill Wilson (up2itnow0822)
tags: ["trading", "crypto", "bitcoin", "paper-trading", "readytrader", "mcp"]
trigger_patterns:
  - paper trade bitcoin
  - paper trade btc
  - buy btc paper
  - readytrader crypto
  - crypto risk check
  - bitcoin price readytrader
---

# ReadyTrader-Crypto paper trading

The ReadyTrader Crypto plugin registers the ReadyTrader-Crypto MCP server as `readytrader_crypto`.
Its tools are called as `readytrader_crypto.<tool>` with `tool_args`, for example:

```json
{"tool_name": "readytrader_crypto.get_crypto_price", "tool_args": {"symbol": "BTC/USDT"}}
```

The server runs the paper profile only: paper mode, trading halted, live execution disabled, no
exchange keys. Every order is simulated against a paper wallet kept in the plugin folder.

## Rules

- BTC pairs only (`BTC/USDT`, `BTC/USD`). The allowlists apply only on the live path, so you enforce this.
- Never try to enable live trading, change the server's environment, or approve anything. If the user
  asks for a live trade, refuse: live trading is an operator process outside this plugin.
- Read every answer's `ok` first. `ok: false` carries `error.code` and `error.message`; report them.

## Procedure

1. Price: `readytrader_crypto.get_crypto_price` with `{"symbol": "BTC/USDT"}`; use the number in
   `data.price`. It sizes the order; it is not sent with it.
2. Paper funds, if the wallet is empty: `readytrader_crypto.deposit_paper_funds` with
   `{"asset": "USDT", "amount": 10000}`. `readytrader_crypto.get_cex_balance` shows the wallet.
3. Risk check: `readytrader_crypto.validate_trade_risk` with `{"side": "buy", "symbol": "BTC/USDT",
   "amount_usd": <usd>, "portfolio_value": <wallet value>}`. Proceed only when
   `data.result.allowed` is `true`; otherwise report `data.result.reason` and stop. `ok: true` only
   means the check ran.
4. Order: `readytrader_crypto.place_cex_order` with `{"symbol": "BTC/USDT", "side": "buy",
   "amount": <btc>, "order_type": "market"}`, with no `price`: the server fills at its market price.
   Done when `ok` is `true` and `data.mode` is `"paper"`; report `data.fill.price`.
5. A refusal ends the attempt; report it, do not retry with other numbers:
   `risk_blocked` (the Risk Guardian refused; `error.data.risk` says why), `paper_price_required`
   (no market price right now), `limit_not_marketable` (a limit that would rest), `insufficient_funds`.

## Good to know

- Keyless news tools (`get_news`, `get_social_sentiment`, `get_financial_news`) answer
  `not_configured` without provider keys: no data, not an outage. `get_free_news` and
  `get_sentiment` need no keys.
- Order-management tools (`get_cex_order`, `cancel_cex_order`, private streams, `transfer_eth`)
  answer `paper_mode_not_supported`: paper orders fill at once and never rest on an exchange.
- `run_backtest_simulation` executes the strategy code you pass; review it first.
