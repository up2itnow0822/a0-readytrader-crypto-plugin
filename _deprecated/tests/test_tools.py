"""Tests for the ReadyTrader Crypto tool classes."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

import tools.crypto_tools as cx


def _mock_httpx_success(payload: dict):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=payload)
    client = MagicMock()
    client.post = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return MagicMock(return_value=client), client


def _mock_httpx_connect_error():
    client = MagicMock()
    client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return MagicMock(return_value=client), client


def _mock_httpx_timeout():
    client = MagicMock()
    client.post = AsyncMock(side_effect=httpx.TimeoutException("slow"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return MagicMock(return_value=client), client


def _make(tool_cls, agent, **args):
    return tool_cls(agent=agent, args=args)


class TestConfig:
    def test_defaults_applied(self, set_plugin_config, mock_agent):
        set_plugin_config()
        cfg = cx._cfg(mock_agent)
        assert cfg["mcp_server_url"] == "http://localhost:8000"
        assert cfg["default_exchange"] == "binance"
        assert cfg["mcp_request_timeout"] == 30

    def test_url_override(self, set_plugin_config, mock_agent):
        set_plugin_config(mcp_server_url="http://crypto.example.com:9000")
        cfg = cx._cfg(mock_agent)
        assert cfg["mcp_server_url"] == "http://crypto.example.com:9000"

    @pytest.mark.parametrize("blocked", [
        "http://169.254.169.254/",
        "http://metadata.google.internal/",
        "http://metadata.azure.com/",
    ])
    def test_ssrf_blocked(self, set_plugin_config, mock_agent, blocked):
        set_plugin_config(mcp_server_url=blocked)
        cfg = cx._cfg(mock_agent)
        assert cfg["mcp_server_url"] == "http://localhost:8000"
        assert "_ssrf_warning" in cfg

    def test_ssrf_bad_scheme(self, set_plugin_config, mock_agent):
        set_plugin_config(mcp_server_url="javascript:alert(1)")
        cfg = cx._cfg(mock_agent)
        assert cfg["mcp_server_url"] == "http://localhost:8000"
        assert "_ssrf_warning" in cfg


TOOL_CASES = [
    (cx.GetCryptoPrice,       {"symbol": "BTC/USDT"},                        "get_crypto_price"),
    (cx.FetchOHLCV,           {"symbol": "BTC/USDT"},                        "fetch_ohlcv"),
    (cx.ValidateTradeRisk,    {"symbol": "BTC/USDT", "amount_usd": 100},     "validate_trade_risk"),
    (cx.RunBacktest,          {"strategy_code": "pass"},                     "run_backtest_simulation"),
    (cx.GetMarketSentiment,   {},                                            "get_sentiment"),
    (cx.GetMarketRegime,      {"symbol": "BTC/USDT"},                        "get_market_regime"),
]


class TestToolsSuccess:
    @pytest.mark.parametrize("tool_cls,args,expected_mcp_name", TOOL_CASES)
    async def test_success(self, set_plugin_config, mock_agent,
                            tool_cls, args, expected_mcp_name):
        set_plugin_config()
        payload = {"ok": True, "tool": expected_mcp_name}
        factory, client = _mock_httpx_success(payload)
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(tool_cls, mock_agent, **args)
            response = await tool.execute()
        assert response.break_loop is False
        parsed = json.loads(response.message)
        assert parsed == payload
        call = client.post.await_args
        assert call.kwargs["json"]["name"] == expected_mcp_name


class TestToolsOffline:
    @pytest.mark.parametrize("tool_cls,args,expected_mcp_name", TOOL_CASES)
    async def test_connect_error(self, set_plugin_config, mock_agent,
                                  tool_cls, args, expected_mcp_name):
        set_plugin_config()
        factory, _ = _mock_httpx_connect_error()
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(tool_cls, mock_agent, **args)
            response = await tool.execute()
        parsed = json.loads(response.message)
        assert parsed["error"] == "mcp_unreachable"
        assert "ReadyTrader-Crypto" in parsed["message"]

    async def test_timeout(self, set_plugin_config, mock_agent):
        set_plugin_config()
        factory, _ = _mock_httpx_timeout()
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.GetCryptoPrice, mock_agent, symbol="BTC/USDT")
            response = await tool.execute()
        parsed = json.loads(response.message)
        assert parsed["error"] == "mcp_unreachable"


class TestConfigOverrideRespected:
    async def test_url_override_used(self, set_plugin_config, mock_agent):
        set_plugin_config(mcp_server_url="http://cx.example.com:1234")
        factory, client = _mock_httpx_success({"ok": True})
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.GetCryptoPrice, mock_agent, symbol="BTC/USDT")
            await tool.execute()
        call = client.post.await_args
        assert call.args[0].startswith("http://cx.example.com:1234")

    async def test_trading_mode_forwarded_price(self, set_plugin_config, mock_agent):
        set_plugin_config(trading_mode="live")
        factory, client = _mock_httpx_success({"ok": True})
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.GetCryptoPrice, mock_agent, symbol="BTC/USDT")
            await tool.execute()
        payload = client.post.await_args.kwargs["json"]
        assert payload["arguments"]["mode"] == "live"

    async def test_trading_mode_forwarded_backtest(self, set_plugin_config, mock_agent):
        set_plugin_config(trading_mode="live")
        factory, client = _mock_httpx_success({"ok": True})
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.RunBacktest, mock_agent, strategy_code="pass")
            await tool.execute()
        payload = client.post.await_args.kwargs["json"]
        assert payload["arguments"]["mode"] == "live"

    async def test_ssrf_warning_prepended(self, set_plugin_config, mock_agent):
        set_plugin_config(mcp_server_url="http://metadata.azure.com/")
        factory, _ = _mock_httpx_success({"ok": True})
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.GetCryptoPrice, mock_agent, symbol="BTC/USDT")
            response = await tool.execute()
        assert response.message.startswith("[WARNING]")
        assert "SSRF" in response.message


class TestExchangeAllowList:
    @pytest.mark.parametrize("valid", ["binance", "coinbase", "kraken", "okx", "bybit"])
    async def test_allowed_exchanges_accepted(self, set_plugin_config, mock_agent, valid):
        set_plugin_config()
        factory, client = _mock_httpx_success({"ok": True})
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.GetCryptoPrice, mock_agent, symbol="BTC/USDT", exchange=valid)
            response = await tool.execute()
        assert json.loads(response.message) == {"ok": True}
        args = client.post.await_args.kwargs["json"]["arguments"]
        assert args["exchange"] == valid

    async def test_mixed_case_normalized(self, set_plugin_config, mock_agent):
        set_plugin_config()
        factory, client = _mock_httpx_success({"ok": True})
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.GetCryptoPrice, mock_agent, symbol="BTC/USDT", exchange="Binance")
            response = await tool.execute()
        assert json.loads(response.message) == {"ok": True}
        args = client.post.await_args.kwargs["json"]["arguments"]
        assert args["exchange"] == "binance"

    @pytest.mark.parametrize("bad", [
        "mexc",           # not on allow-list
        "ftx",            # not on allow-list
        "bitmex",         # not on allow-list
        "file://etc",     # garbage
        "",               # empty
    ])
    async def test_disallowed_exchanges_rejected(self, set_plugin_config, mock_agent, bad):
        set_plugin_config()
        factory, client = _mock_httpx_success({"ok": True})
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.GetCryptoPrice, mock_agent, symbol="BTC/USDT", exchange=bad)
            response = await tool.execute()
        assert "Invalid exchange" in response.message
        # Confirm allow-list was printed to user
        for ex in ("binance", "coinbase", "kraken", "okx", "bybit"):
            assert ex in response.message
        client.post.assert_not_awaited()


class TestStrategyCodeLimit:
    async def test_oversize_rejected(self, set_plugin_config, mock_agent):
        set_plugin_config()
        big = "x" * (cx._STRATEGY_CODE_LIMIT + 1)
        tool = _make(cx.RunBacktest, mock_agent, strategy_code=big)
        response = await tool.execute()
        assert "too large" in response.message

    async def test_under_limit_accepted(self, set_plugin_config, mock_agent):
        set_plugin_config()
        factory, client = _mock_httpx_success({"ok": True})
        with patch.object(cx.httpx, "AsyncClient", factory):
            tool = _make(cx.RunBacktest, mock_agent, strategy_code="pass")
            response = await tool.execute()
        assert json.loads(response.message) == {"ok": True}
