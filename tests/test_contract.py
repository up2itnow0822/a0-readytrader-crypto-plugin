"""The Agent Zero v2.13 plugin contract (plugin.yaml, settings screen, skill) and the tool names the skill uses.

Sources mirrored here: agent-zero helpers/plugins.py (manifest fields), skills/a0-create-plugin/references/
implementation.md (settings_sections), plugins/AGENTS.md (config.html binds to config.* through
$store.pluginSettingsPrototype), helpers/skills.py validate_skill (name and description rules).
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "readytrader-crypto-paper" / "SKILL.md"

A0_SETTINGS_SECTIONS = {"agent", "external", "mcp", "developer", "backup"}
A0_MANIFEST_FIELDS = {"name", "title", "description", "version", "settings_sections", "per_project_config",
                      "per_agent_config", "always_enabled"}

# The 29 tools ReadyTrader-Crypto's server.py registers (docs/TOOLS.md). A tool the skill names that is
# not here would be a tool the agent cannot call.
SERVER_TOOLS = {
    "cancel_all_cex_orders", "cancel_cex_order", "deposit_paper_funds", "fetch_ohlcv", "get_cex_balance",
    "get_cex_capabilities", "get_cex_my_trades", "get_cex_order", "get_crypto_price", "get_financial_news",
    "get_free_news", "get_latest_insights", "get_market_regime", "get_news", "get_sentiment",
    "get_social_sentiment", "list_cex_open_orders", "list_cex_orders", "list_cex_private_updates",
    "place_cex_order", "post_market_insight", "replace_cex_order", "run_backtest_simulation",
    "start_cex_private_ws", "stop_cex_private_ws", "swap_tokens", "transfer_eth", "validate_trade_risk",
    "wait_for_cex_order",
}
# snake_case words in the skill's code spans that are answer codes or fields, not tools
NOT_TOOLS = {"risk_blocked", "paper_price_required", "limit_not_marketable", "insufficient_funds",
             "not_configured", "paper_mode_not_supported", "tool_name", "tool_args", "order_type",
             "amount_usd", "portfolio_value", "readytrader_crypto"}


def manifest():
    return yaml.safe_load((ROOT / "plugin.yaml").read_text(encoding="utf-8"))


def test_manifest_fields_name_and_sections():
    m = manifest()
    assert set(m) <= A0_MANIFEST_FIELDS
    assert re.fullmatch(r"[a-z0-9_]+", m["name"]) and not m["name"].startswith("_")
    assert m["name"] == "readytrader_crypto"
    assert set(m.get("settings_sections") or []) <= A0_SETTINGS_SECTIONS
    for key in ("title", "description", "version"):
        assert m[key]


def test_manifest_version_matches_changelog_and_skill():
    version = manifest()["version"]
    assert f"## [{version}]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"version: {version}" in SKILL.read_text(encoding="utf-8")


def test_settings_screen_binds_to_config_only():
    html = (ROOT / "webui" / "config.html").read_text(encoding="utf-8")
    assert "$store.pluginSettings" not in html  # not a store Agent Zero v2.13 provides
    bound = set(re.findall(r"config\.([a-z_]+)", html))
    defaults = set(yaml.safe_load((ROOT / "default_config.yaml").read_text(encoding="utf-8")))
    assert bound == defaults, f"screen fields {bound} != default_config.yaml keys {defaults}"


def test_no_tool_files_left_for_agent_zero_to_misload():
    # v1 shipped tools/crypto_tools.py, which failed to import in Agent Zero and fell back to Unknown.
    assert not (ROOT / "tools").exists()


def frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md must open with a closed --- frontmatter fence"
    return yaml.safe_load(m.group(1)), text[m.end():]


def test_skill_frontmatter_meets_agent_zero_rules():
    fm, _ = frontmatter()
    name = fm["name"]
    assert re.fullmatch(r"[a-z0-9-]+", name) and 1 <= len(name) <= 64
    assert not name.startswith("-") and not name.endswith("-") and "--" not in name
    assert 0 < len(fm["description"]) <= 1024
    assert fm.get("trigger_patterns")


def test_skill_names_only_real_server_tools():
    _, body = frontmatter()
    qualified = set(re.findall(r"readytrader_crypto\.([a-z_]+)", body))
    spans = set(re.findall(r"`([a-z][a-z0-9_]*_[a-z0-9_]+)`", body))
    unknown = (qualified | (spans - NOT_TOOLS)) - SERVER_TOOLS
    assert qualified and not unknown, f"not ReadyTrader-Crypto tools: {sorted(unknown)}"


def test_skill_never_sends_a_price_on_market_orders():
    _, body = frontmatter()
    order = re.search(r"place_cex_order` with `(\{.*?\})`", body, re.S)
    assert order and '"price"' not in order.group(1)
