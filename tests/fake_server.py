"""A stand-in MCP stdio server for smoke_test(): FAKE_MODE picks how it behaves.

pr20     offers the tools the skill uses and refuses exchange-account tools in paper mode (current server)
old      same tools, but answers list_cex_open_orders like revisions before PR #20 (no paper refusal)
missing  starts, but offers only one tool
crash    writes an error to stderr and exits before speaking MCP
crashbytes  the same, with bytes that are not UTF-8
hang     never answers
"""

import json
import os
import sys
import time

mode = os.environ.get("FAKE_MODE", "pr20")
if mode == "crash":
    print("Traceback: ModuleNotFoundError: No module named 'ccxt'", file=sys.stderr, flush=True)
    sys.exit(1)
if mode == "crashbytes":
    sys.stderr.buffer.write(b"fatal: \xff\xfe not utf-8, then ModuleNotFoundError: No module named 'ccxt'\n")
    sys.stderr.flush()
    sys.exit(1)
if mode == "hang":
    time.sleep(3600)

from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("fake-readytrader")


@mcp.tool()
def get_crypto_price(symbol: str) -> str:
    return json.dumps({"ok": True, "data": {"price": 1.0}})


if mode != "missing":
    for name in ("deposit_paper_funds", "get_cex_balance", "validate_trade_risk", "place_cex_order"):
        mcp.tool(name=name)(lambda: json.dumps({"ok": True, "data": {}}))

    @mcp.tool()
    def list_cex_open_orders() -> str:
        if mode == "old":
            return json.dumps({"ok": True, "data": {"orders": []}})
        return json.dumps({"ok": False, "error": {"code": "paper_mode_not_supported", "message": "paper", "data": {}}})


mcp.run()
