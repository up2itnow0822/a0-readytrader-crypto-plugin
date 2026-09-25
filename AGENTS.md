# a0-readytrader-crypto-plugin

Root AGENTS.md (DOX rail).

## Purpose

Agent Zero community plugin `readytrader_crypto`: paper BTC trading through the ReadyTrader-Crypto MCP
server. The repository root is the plugin folder Agent Zero installs into `usr/plugins/readytrader_crypto/`.

## Ownership

- Owner: Agent Economy, LLC / Bill Wilson (@up2itnow0822)
- Companion server: https://github.com/up2itnow0822/ReadyTrader-Crypto (source of truth for tools and env vars)
- Host contract: Agent Zero v2.13+ `plugins/AGENTS.md`, `helpers/plugins.py`, `helpers/mcp_handler.py`,
  `helpers/skills.py`, `skills/a0-create-plugin/references/implementation.md`

## Local Contracts

- `plugin.yaml` — Agent Zero manifest fields only; `name` == `readytrader_crypto`; `settings_sections` from
  Agent Zero's set (`agent`, `external`, `mcp`, `developer`, `backup`); `version` matches CHANGELOG and the skill
- `hooks.py` — the only lifecycle code: `install()` and `save_plugin_config()` both run `apply(cfg)` under a
  file lock (read + clash-check the MCP settings, clone/fetch the server at `server_ref` into `server/`,
  venv with Agent Zero's Python, requirements, an empty `server/.env` so the server never reads Agent
  Zero's `usr/.env`, the smoke test, then register the MCP entry last, or ask Agent Zero to reload it when
  the entry text is unchanged); any failure before registration completes rolls the checkout back (or
  moves an unverified fresh checkout aside as `server.failed-*`) and writes nothing. `save_plugin_config()` validates and applies before Agent Zero writes
  `config.json`, so saved settings are always applied settings. `pre_update()` is a no-op;
  `uninstall()` removes only our entry and never raises. Setup never lives in `execute.py`
- `mcp_smoke.py` — the smoke test, run by `hooks.smoke_test()` in its own Python process (never inside Agent
  Zero's patched event loop); the server is registered only on its positive proof (tool count, required
  tools present, gate passed); a timeout kills the process group
- `PAPER_GATE` — the server must refuse `list_cex_open_orders` with `paper_mode_not_supported` in paper
  mode (ReadyTrader-Crypto PR #20+); older servers sent exchange-account tools to the exchange in paper
  mode and are never registered
- The MCP entry always carries `PAPER_ENV` (paper, halted, live disabled, approve-each, BTC allowlists — the
  server enforces allowlists on its live path only, so they are a backstop, not a paper-order filter) and
  every data path under `data/`, under both names the server reads (`<X>_DB_PATH`, `READYTRADER_<X>_DB_PATH`);
  no setting may change the paper profile; no credentials are ever written
- Registration never overwrites or removes a server the plugin did not add, including one whose name Agent
  Zero normalises to ours; it reads every `mcp_servers` shape Agent Zero accepts and writes back
  `{"mcpServers": {...}}` with every server and other top-level key kept; non-strict JSON is never
  rewritten. Our entry is recognised by `MARKER`, or by its `server.py` path only under our configured
  name (another name pointing at our server is the user's). A refresh keeps `disabled` / `disabled_tools`
  and only the proxy/CA variables in `USER_ENV_ALLOWED`; everything else the user added is removed
- Settings are validated in `normalize_config`: https repo or absolute directory, `server_ref` a
  branch/tag/full SHA that can never be read as a git option, name `[a-z0-9_]+`, timeouts 5-3600 s
- `skills/readytrader-crypto-paper/SKILL.md` — Agent Zero skill rules (name `^[a-z0-9-]+$`, description
  <= 1024); names only real ReadyTrader-Crypto tools; market orders never carry a `price`
- `webui/config.html` binds only `config.<key>` for exactly the keys in `default_config.yaml`
- No `tools/` directory: the agent uses the server's tools through Agent Zero's MCP client. The 1.x tool
  client and its tests stay in `_deprecated/` (never loaded)
- `server/`, `data/`, `config.json` are created at install time and are never committed
- No UAT records in the tree: the repository root ships to every user's Agent Zero

## Work Guidance

- When ReadyTrader-Crypto adds or renames a tool, update `SERVER_TOOLS` in `tests/test_contract.py` and the skill
- Verify behaviour in a real Agent Zero framework process (hooks + MCP client), not only with the unit fakes
- Paper-first only; never add a live-trading path or a setting that could enable one

## Verification

- `pytest -q` (hooks with framework fakes, real git checkouts and venvs, the smoke test and paper gate
  against `tests/fake_server.py` over real MCP stdio, manifest / settings-screen / skill contract);
  needs `requirements-dev.txt` (pytest, PyYAML, mcp, nest_asyncio for the "inside Agent Zero's loop" test)
- Agent Zero integration: install into a throwaway Agent Zero v2.13 tree through its installer (Git URL and
  ZIP), initialise `MCPConfig` from the saved settings, call the paper procedure's tools, save settings
  through the real settings screen, update, uninstall

## Child DOX Index

(none)
