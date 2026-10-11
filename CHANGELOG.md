# Changelog

## [2.0.0] - 2026-09-25

Rebuilt for the Agent Zero v2.13 plugin system. Version 1.0.0 could not work in current Agent Zero
(public-release UAT, run 2026-09-25-01): its tool file failed to import (`python.helpers` no longer
exists), Agent Zero loads one tool class per file by file name, no tool prompts told the model the
tools existed, the settings screen bound to a store Agent Zero does not have, and the tools posted
to an HTTP path (`/mcp/call_tool`) that ReadyTrader-Crypto does not serve (its MCP server speaks
stdio), with arguments the server rejects.

### Changed (breaking)
- The plugin now connects ReadyTrader-Crypto through Agent Zero's own MCP client. `hooks.py`
  `install()` clones the server into the plugin folder, installs its requirements with Agent Zero's
  Python, checks that it starts, and registers it under Settings -> MCP/A2A -> External MCP Servers
  as `readytrader_crypto` (a fixed name: the skill calls the tools by it); `uninstall()` removes that
  entry. The agent gets all 29 server tools
  with their real schemas instead of six hand-written wrappers.
- The server always runs the paper profile (paper mode, trading halted, live execution disabled,
  approve-each, BTC allowlists, no keys); there is no live setting. The paper wallet lives in the
  plugin folder.
- New skill `readytrader-crypto-paper`: the paper procedure (price, risk verdict, market order
  without a price, refusal codes) and the rule to refuse live trading.
- Settings are now the server repository and version and the timeouts;
  the old keys (`mcp_server_url`, `trading_mode`, risk limits, key env names) did nothing.
- The 1.x tools and tests moved to `_deprecated/` (Agent Zero does not load them).
- Saving the settings screen applies the settings at once (`save_plugin_config` hook): the server is
  moved to the chosen version, checked and registered again; on failure nothing is saved and the
  checkout is rolled back. Saving again repairs the setup.
- Install and every save check that the server refuses exchange-account tools in paper mode
  (ReadyTrader-Crypto PR #20 or later) and refuse to register an older server.
- Upgrading from 1.0.0: uninstall it, then install 2.0.0 (1.0.0 has no install hook).

### Security
- The server checkout gets an empty `.env`, so ReadyTrader-Crypto no longer reads Agent Zero's
  `usr/.env` (model API keys, UI password) when it walks up for a `.env` file.
- The MCP entry keeps only proxy and CA-bundle variables a user adds (any other variable, including
  keys and signer endpoints, is removed on every setup); the paper profile and every data path (both
  `<X>_DB_PATH` and `READYTRADER_<X>_DB_PATH`) are reset in any letter case.
- The smoke test runs in its own process (`mcp_smoke.py`) and registers the server only on positive
  proof that the tools are there and the paper gate passed; inside Agent Zero's patched event loop a
  timeout could otherwise look like a pass.
- Setups are serialised with a file lock, check the MCP settings before the server moves, roll back a
  failed registration, move an unverified fresh checkout aside, and ask Agent Zero to reload its MCP
  servers when the entry text did not change. Notifications are HTML-escaped. MCP settings are
  rewritten only when they are strict JSON, keeping other top-level keys and non-ASCII text.
- `server_ref` must be a branch, tag or full commit SHA; a value git could read as an option is refused.
- The MCP entry's name is fixed (`readytrader_crypto`), not a setting: the skill calls the tools by that
  name, so an entry under another name would leave its calls to whatever server holds this one. A
  server name Agent Zero would treat as the plugin's own (it lowercases names and maps other
  characters to `_`) is refused instead of shadowing the paper server.

### Fixed
- README: the install steps (the old `pip install -r requirements.txt` had no file to install)
  and the broker key variables nothing read.
- The URL guard of 1.x no longer matters: the plugin makes no HTTP calls.

## [1.0.0] - 2026-03-23

### Added
- Initial release
- Agent Zero plugin for automated crypto trading via the ReadyTrader strategy engine
- Tools for market data, order execution, and portfolio management via ReadyTrader-Crypto MCP server
