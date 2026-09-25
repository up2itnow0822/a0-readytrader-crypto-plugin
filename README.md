# a0-readytrader-crypto-plugin

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Zero Plugin](https://img.shields.io/badge/Agent%20Zero-Plugin-blue)](https://github.com/agent0ai/agent-zero)

**Paper BTC trading for [Agent Zero](https://github.com/agent0ai/agent-zero)** through the
[ReadyTrader-Crypto](https://github.com/up2itnow0822/ReadyTrader-Crypto) MCP server.

Installing the plugin installs the ReadyTrader-Crypto server into the plugin's own folder, registers
it with Agent Zero's MCP client, and adds a paper-trading skill. Your agent can then read BTC prices,
candles, sentiment and market regime, run backtests and risk checks, and place **paper** orders
against a simulated wallet. The server always runs the paper profile — paper mode, trading halted,
live execution disabled, no exchange keys — and the plugin has no switch that changes that.

Requires Agent Zero v2.13 or later (plugin system with lifecycle hooks), Git in the Agent Zero
environment, network access to GitHub and PyPI during installation, and a ReadyTrader-Crypto version
that refuses exchange-account tools in paper mode (PR #20, September 2026, or later). Installation
checks that last point and refuses an older server.

## Install

Open **Plugins** in Agent Zero and click **Install** (the Plugin Hub). Either tab works; each runs
the plugin's `install()` hook:

- **Git:** enter `https://github.com/up2itnow0822/a0-readytrader-crypto-plugin`.
- **ZIP:** download this repository as a ZIP and upload it.

Installation takes a few minutes. `install()`:

1. clones ReadyTrader-Crypto into `usr/plugins/readytrader_crypto/server` (branch `main` by default)
   and installs its requirements into `server/.venv` with Agent Zero's own Python (3.12+);
2. starts the server once over MCP stdio, checks that it offers the tools the skill uses, and checks
   that it refuses an exchange-account tool (`list_cex_open_orders`) in paper mode;
3. adds an entry named `readytrader_crypto` under **Settings &rarr; MCP/A2A &rarr; External MCP
   Servers**, pointing at that server with the paper profile. Your other servers are kept as they are
   (the settings JSON is saved back as `{"mcpServers": {...}}`, so comments and formatting in it are
   not kept), and nothing is written if any earlier step fails.

The server checkout gets an empty `.env` so ReadyTrader-Crypto does not read Agent Zero's own
`usr/.env` (your model API keys and UI password).

Copying the folder into `usr/plugins/` by hand does not run `install()`; use the Git URL or ZIP
installer. (If you did copy it, open the plugin's settings and click **Save**: that runs the same
setup.)

**Upgrading from 1.0.0:** uninstall 1.0.0 first, then install this version. 1.0.0 has no install
hook, so an in-place update would not set up the server.

## Use

Open a new chat and ask, for example, *"What is BTC trading at?"* or *"Paper-buy $100 of BTC after a
risk check."* The agent sees the server's 29 tools as `readytrader_crypto.<tool>` and the
`readytrader-crypto-paper` skill, which gives it the procedure: take the price from
`get_crypto_price`, run `validate_trade_risk` and continue only when it allows the trade, then place
a market order without a price (the server fills it at its market price). The paper wallet and
order history are kept in `usr/plugins/readytrader_crypto/data`.

The skill keeps the agent on BTC. The BTC exchange and symbol allowlists in the MCP entry are a
backstop for ReadyTrader-Crypto's live order path, which the plugin never enables; the server does not
apply them to paper orders, so a paper order for another pair (ETH/USDT, say) also fills on paper.

Asking for a live trade gets a refusal. Live trading is an operator process run on ReadyTrader-Crypto
itself (see its `docs/LIVE_TESTING_PROTOCOL.md`), never through this plugin.

## Settings

The plugin's settings screen (Settings &rarr; External, or the plugin's entry under **Plugins**) holds
the server repository and version (branch, tag or full commit SHA), the MCP server name, and the
start-up and tool-call timeouts. The paper profile is not a setting.

**Saving applies the settings at once:** the server is moved to the chosen version, checked, and the
MCP entry is registered again. A version change can take a few minutes. If any step fails, the
settings are not saved, a notification names the step, and the server goes back to the version it
was on (a server folder the setup had to create is moved aside as `server.failed-*` instead of being
left behind the MCP entry). Saving again without changes re-runs the setup, which also repairs it (for
example after an Agent Zero upgrade changed its Python), and makes Agent Zero reload the server's tools.
The MCP settings must be strict JSON for any of this: the plugin will not rewrite settings with
comments or trailing commas, because that could drop what you wrote.

To choose a setting before the first install (for example a server version, or another MCP server
name because yours is taken), give Agent Zero the environment variable
`A0_SET_readytrader_crypto__<setting>`, e.g. `A0_SET_readytrader_crypto__server_ref=v1.2.3` (in
`usr/.env`, or `-e` for the Docker container), and restart Agent Zero. The install uses it while no
settings have been saved; once you save the settings screen, the saved values win. (The screen's
**Reset to default** shows the plugin's own defaults, not the preset.)

The server repository is code the plugin runs: the setup clones it, installs its requirements and
starts its `server.py` with Agent Zero's Python. Leave it at ReadyTrader-Crypto, or point it only at
a fork you trust.

## Update and uninstall

- **A newer plugin version:** installed from the Plugin Index, use **Update** on the plugin's Plugin
  Hub page; it re-runs `install()` and keeps the paper wallet. Installed from a Git URL or ZIP (Agent
  Zero offers no Update button for those), uninstall and install again; that resets the settings and
  the paper wallet.
- **A newer server version:** set it in the settings and save.
- **Uninstall** removes the `readytrader_crypto` MCP entry, then Agent Zero deletes the plugin folder,
  including the server and the paper wallet. If the MCP settings cannot be read, the uninstall still
  goes ahead and the log says which entry to remove by hand.

## Troubleshooting

- **Install or save fails:** the message names the step (cloning, fetching the version, installing
  requirements, starting the server, the paper-mode check). Check that Agent Zero can reach GitHub and
  PyPI, then try again.
- **"does not refuse list_cex_open_orders in paper mode":** the server version predates
  ReadyTrader-Crypto's paper-mode refusals. Set a newer server version.
- **"An MCP server named ... already exists (Agent Zero calls it readytrader_crypto)":** you have your
  own entry with that name, or one Agent Zero treats as the same (it lowercases names and turns other
  characters into `_`). Remove or rename it and install again, or preset another name with
  `A0_SET_readytrader_crypto__mcp_server_name` (see Settings).
- **No tools in the chat:** open Settings &rarr; MCP/A2A &rarr; External MCP Servers and check the
  entry's status and tool count. An Agent Profile with a custom tool policy can block MCP tools. Saving
  the plugin settings re-runs the setup.
- **Market data errors behind a proxy:** Agent Zero starts MCP servers with a minimal environment
  (no proxy variables). Add `HTTPS_PROXY` (and `NO_PROXY`, or a CA bundle variable if your proxy needs
  one) to the `readytrader_crypto` entry's `env` in the MCP settings. The setup keeps only these
  variables there (any letter case): `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, `ALL_PROXY`,
  `SSL_CERT_FILE`, `SSL_CERT_DIR`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`,
  `WEBSOCKET_CLIENT_CA_BUNDLE`, `TZ`, `LANG`, `LC_ALL`. Anything else you add (keys, signer
  endpoints, other ReadyTrader settings) is removed the next time the setup runs, and the paper-profile
  and data-path variables are always reset.
- **Projects:** a project whose own MCP settings define a server Agent Zero also calls
  `readytrader_crypto` uses that server instead of this one inside that project.
- **Slow first call:** Agent Zero starts the server afresh for every call; allow a few seconds.

## Development

```bash
python -m pip install -r requirements-dev.txt
pytest -q
```

`hooks.py` holds the lifecycle hooks, `skills/readytrader-crypto-paper/SKILL.md` the agent-facing
procedure, `webui/config.html` the settings screen. The 1.x HTTP tool client is kept in `_deprecated/`
for reference; Agent Zero never loads it.

## Ecosystem

- [ReadyTrader-Crypto](https://github.com/up2itnow0822/ReadyTrader-Crypto) — the MCP server
- [readytrader-crypto-hermes](https://github.com/up2itnow0822/readytrader-crypto-hermes) — the same paper procedure for Hermes Agent
- [agent-wallet-sdk](https://github.com/up2itnow0822/agent-wallet-sdk) — Non-custodial agent wallets
- [agentpay-mcp](https://github.com/up2itnow0822/agentpay-mcp) — MCP server for agent payments

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE)
