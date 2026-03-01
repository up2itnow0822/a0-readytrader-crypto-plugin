"""
ReadyTrader Crypto tools for Agent Zero.
Wraps the ReadyTrader-Crypto MCP server to give agents access to
cryptocurrency market data, risk validation, backtesting, and trading.
"""
import json
import os
from typing import Optional

import httpx

from python.helpers.tool import Tool, Response
from python.helpers.plugins import get_plugin_config


def _cfg(agent) -> dict:
    defaults = {
        "mcp_server_url": "http://localhost:8000",
        "trading_mode": "paper",
        "default_exchange": "binance",
        "default_timeframe": "1h",
        "max_position_size_usd": 1000.0,
    }
    cfg = get_plugin_config("readytrader-crypto", agent=agent) or {}
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    return cfg


async def _call_mcp(base_url: str, tool_name: str, args: dict) -> dict:
    """Call an MCP tool on the ReadyTrader-Crypto server."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base_url}/mcp/call_tool",
            json={"name": tool_name, "arguments": args},
        )
        resp.raise_for_status()
        return resp.json()


class GetCryptoPrice(Tool):
    """Fetch the current price of a cryptocurrency."""

    async def execute(self, **kwargs) -> Response:
        cfg = _cfg(self.agent)
        symbol = self.args.get("symbol", "BTC/USDT")
        exchange = self.args.get("exchange", cfg["default_exchange"])
        try:
            result = await _call_mcp(
                cfg["mcp_server_url"],
                "get_crypto_price",
                {"symbol": symbol, "exchange": exchange},
            )
            return Response(message=json.dumps(result, indent=2), break_loop=False)
        except Exception as e:
            return Response(message=f"Error fetching price: {e}", break_loop=False)


class FetchOHLCV(Tool):
    """Fetch OHLCV candle data for a crypto pair."""

    async def execute(self, **kwargs) -> Response:
        cfg = _cfg(self.agent)
        symbol = self.args.get("symbol", "BTC/USDT")
        timeframe = self.args.get("timeframe", cfg["default_timeframe"])
        limit = int(self.args.get("limit", 24))
        try:
            result = await _call_mcp(
                cfg["mcp_server_url"],
                "fetch_ohlcv",
                {"symbol": symbol, "timeframe": timeframe, "limit": limit},
            )
            return Response(message=json.dumps(result, indent=2), break_loop=False)
        except Exception as e:
            return Response(message=f"Error fetching OHLCV: {e}", break_loop=False)


class ValidateTradeRisk(Tool):
    """Check whether a proposed trade passes risk management rules."""

    async def execute(self, **kwargs) -> Response:
        cfg = _cfg(self.agent)
        try:
            result = await _call_mcp(
                cfg["mcp_server_url"],
                "validate_trade_risk",
                {
                    "side": self.args.get("side", "buy"),
                    "symbol": self.args.get("symbol", "BTC/USDT"),
                    "amount_usd": float(self.args.get("amount_usd", 100)),
                    "portfolio_value": float(self.args.get("portfolio_value", 10000)),
                },
            )
            return Response(message=json.dumps(result, indent=2), break_loop=False)
        except Exception as e:
            return Response(message=f"Error validating risk: {e}", break_loop=False)


class RunBacktest(Tool):
    """Run a backtest simulation with a given strategy."""

    async def execute(self, **kwargs) -> Response:
        cfg = _cfg(self.agent)
        try:
            result = await _call_mcp(
                cfg["mcp_server_url"],
                "run_backtest_simulation",
                {
                    "strategy_code": self.args.get("strategy_code", ""),
                    "symbol": self.args.get("symbol", "BTC/USDT"),
                    "timeframe": self.args.get("timeframe", cfg["default_timeframe"]),
                },
            )
            return Response(message=json.dumps(result, indent=2), break_loop=False)
        except Exception as e:
            return Response(message=f"Error running backtest: {e}", break_loop=False)


class GetMarketSentiment(Tool):
    """Get aggregated market sentiment from news and social sources."""

    async def execute(self, **kwargs) -> Response:
        cfg = _cfg(self.agent)
        try:
            result = await _call_mcp(cfg["mcp_server_url"], "get_sentiment", {})
            return Response(message=json.dumps(result, indent=2), break_loop=False)
        except Exception as e:
            return Response(message=f"Error fetching sentiment: {e}", break_loop=False)


class GetMarketRegime(Tool):
    """Detect the current market regime (trending, ranging, volatile)."""

    async def execute(self, **kwargs) -> Response:
        cfg = _cfg(self.agent)
        symbol = self.args.get("symbol", "BTC/USDT")
        timeframe = self.args.get("timeframe", "1d")
        try:
            result = await _call_mcp(
                cfg["mcp_server_url"],
                "get_market_regime",
                {"symbol": symbol, "timeframe": timeframe},
            )
            return Response(message=json.dumps(result, indent=2), break_loop=False)
        except Exception as e:
            return Response(message=f"Error fetching regime: {e}", break_loop=False)
