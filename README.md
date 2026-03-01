# ReadyTrader Crypto — Agent Zero Plugin

An Agent Zero plugin that connects your agent to the [ReadyTrader-Crypto](https://github.com/up2itnow0822/ReadyTrader-Crypto) MCP server. Your agent gets real-time crypto prices, OHLCV chart data, sentiment analysis, risk validation, and backtesting — all through a running ReadyTrader-Crypto instance.

## What it does

- **Get prices** — fetch live crypto prices from Binance, Coinbase, or Kraken
- **Pull chart data** — OHLCV candles at any timeframe
- **Check sentiment** — aggregated news and social sentiment
- **Validate risk** — run proposed trades through risk management rules before executing
- **Backtest strategies** — test trading logic against historical data
- **Detect regimes** — identify whether a market is trending, ranging, or volatile

## Setup

1. Install and run the [ReadyTrader-Crypto](https://github.com/up2itnow0822/ReadyTrader-Crypto) MCP server
2. Drop this plugin into your Agent Zero plugins directory
3. Configure the MCP server URL in Settings → Agent → ReadyTrader Crypto

The plugin defaults to paper trading mode. Switch to live in the settings when you're ready.

## Configuration

All settings are configurable through the Agent Zero UI or `default_config.yaml`:

| Setting | Default | Description |
|---------|---------|-------------|
| `mcp_server_url` | `http://localhost:8000` | ReadyTrader-Crypto server address |
| `trading_mode` | `paper` | `paper` or `live` |
| `default_exchange` | `binance` | Exchange for price lookups |
| `max_position_size_usd` | `1000` | Per-trade size cap |
| `max_portfolio_risk_pct` | `5.0` | Max portfolio risk percentage |

## License

MIT
