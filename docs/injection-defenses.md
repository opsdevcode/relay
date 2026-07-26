# Injection defenses (Phase 2D.3)

Relay limits tool execution, moderates assistant output, and supports an operator **kill switch** for chat and confirm paths.

## Tool allow-list

Chat routing only dispatches handlers in `REGISTERED_TOOL_IDS` ([`registry.py`](../apps/relay-assistant/src/portal_assistant/registry.py)). Unknown tools fall back to a safe error; registry validation in CI (`tests/test_registry.py`) keeps routing aligned with handlers.

## Prompt-injection guard

When **`INJECTION_DEFENSE_ENABLED=true`** (default), messages matching high-risk patterns (e.g. “ignore previous instructions”) **cannot route to write tools** (`scaffold_service`, `request_sandbox`). Routing is downgraded to **`docs_search`** (read-only).

Disable locally only for targeted testing:

```bash
INJECTION_DEFENSE_ENABLED=false
```

## Output moderation

When **`OUTPUT_MODERATION_ENABLED=true`** (default), assistant answers containing blocked patterns (e.g. `<script`, `javascript:`, instruction-override text) are replaced with a safe withheld message before returning to the client.

## Kill switch

Set **`CHAT_KILL_SWITCH=true`** to return **503** on `POST /chat` and `POST /actions/confirm`. Use during incidents without redeploying routing rules.

`/health` reports `chat_enabled`, `injection_defense_enabled`, and `output_moderation_enabled`.

## Related

- [audit-log.md](audit-log.md)
- [roadmap.md](roadmap.md) — Phase 2D.4 citation-required mode
