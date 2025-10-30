# agents/authority — Authority & Approvals (Ledger + Policy)

> **Purpose**: This folder defines how the agent requests, records, reuses, and revokes _permission_ to act. It is the auditable source of truth for **Allow / Always Allow / Read‑Only**, and for **Independent Agent Mode**. High‑contrast UI rule applies: all UI that surfaces authority must use readable text on a clear background (no low‑contrast).

## What lives here
- `ledger.json` — durable approvals + policy + history (machine‑readable).
- `README_authority.md` (this file) — human contract for how authority works and how to operate it.
- (optional) `exports/` — CSV/JSON snapshots created by the UI “Export authority log” action.

## Authority model at a glance
- **Ask First (default)** — every non‑trivial command shows a pending prompt; you click **Allow** (once) or **Always Allow** for future recurrences.
- **Full Auto** — agent executes allowed classes of commands without prompting (still audited in `ledger.json`).
- **Read‑Only** — agent plans, analyzes, and drafts but does not write to disk or call tools with side effects.
- **Independent Agent Mode** — approvals are sandboxed _per repo_; when off, approvals may be reused globally across repos for repeat workflows.

> The agent never invents authority. All side‑effects are either approved now, covered by a prior Always‑Allow that matches the command _pattern_, or refused and routed to Quarantined‑Updates.

## Independent Agent Mode
| Mode | Ledger scope | Approval reuse | Typical use |
|---|---|---|---|
| **ON** | Per‑repo file at `agents/authority/ledger.json` in that repo | **No** (isolated) | Experiments; sensitive projects |
| **OFF** | Global cache + this repo | **Yes** (shared) | Speed for repetitive, trusted flows |

Toggle lives in **Agent Manager → Authority**. The UI also exposes **Wipe approvals (repo)**, **Wipe approvals (global)**, and **Export authority log**.

## `ledger.json` format (v1.2)
The file is forward‑extensible and remains backward compatible with your earlier minimal shape (`version`, `independent_agent_mode`, `approvals`, `history`). New fields add policy and timestamps so the agent can reason about safety at runtime.

```json
{
  "version": "1.2",
  "independent_agent_mode": false,
  "policy": {
    "authority_mode": "ask-first",        // one of: "ask-first" | "full-auto" | "read-only"
    "always_allow_default": false,        // UI default for the Always-Allow toggle
    "remember_always_allow": true,        // if true, store Always-Allow grants durably
    "require_command_allow": true         // if true, prompt unless a matching grant exists
  },
  "approvals": [
    {
      "id": "appr_2025-10-29T00:00:00Z_001",
      "pattern": "write:file:*.md",       // canonicalized pattern the grant covers
      "scope": {
        "repo_root": "C:/path/to/repo",
        "paths": ["README.md"],
        "independent": true
      },
      "granted_at": "2025-10-29T00:00:00Z",
      "granted_by": "operator",
      "reason": "Allow updating docs",
      "always_allow": true,
      "ttl_hours": null,                  // optional time limit for auto-expiry
      "expires_at": null,
      "tags": ["docs"],
      "risk": "low"                       // low | medium | high (for UI highlighting)
    }
  ],
  "history": [
    {
      "timestamp": "2025-10-29T00:00:00Z",
      "action": "mode_changed",
      "from": "ask-first",
      "to": "read-only",
      "by": "operator",
      "note": "Temporarily locked to read-only during review"
    }
  ],
  "created_at": "2025-10-29T00:00:00Z",
  "updated_at": "2025-10-29T00:00:00Z",
  "last_reviewed_at": null
}
```

### Notes for implementers
- Matching uses _patterns_ (e.g., `write:file:*.py`, `shell:git commit`, `net:http:api.github.com`). The agent must canonicalize a command into a stable pattern before look‑up.
- A grant matches when **pattern** aligns and **scope.repo_root** matches the active repo. When **Independent Agent Mode** is OFF, grants may be considered across repos.
- All writes to `ledger.json` append to `history` as an audit trail. Never mutate old `history` entries.

## Typical operations
- **Allow once** → Append ephemeral approval (no `always_allow`) + execute.
- **Always Allow** → Append durable approval (`always_allow: true`).
- **Revoke** → Remove a specific approval by `id` (history records the revoke).
- **Wipe (repo)** → Clear `approvals` for this repo; add history entry.
- **Wipe (global)** → Clear global cache; keep this repo’s file unless you also wipe locally.

## Maintenance (UI + scripts)
- From the UI: **Agent Manager → Authority** exposes the allow list, revoke controls, wipes, and export.
- From scripts: add small helpers under `system_tools/authority/` (or agent‑local `agent_tools/authority/`) to list/revoke/export. Keep outputs high‑contrast when rendered in the console.

## Security & audit guarantees
- No silent actions: any command with side‑effects must be _covered_ by an existing approval or explicitly approved now.
- Everything is logged: `history` records grants, revocations, wipes, and mode changes with timestamps.
- Backwards‑compatible structure: Old minimal files load; new policy fields adopt defaults when absent.

## Migration
- **v1.0 → v1.2**: You can simply add the `policy`, timestamp fields, and optional metadata. Older tools that only read `approvals`/`history` continue to work.

## FAQ
**Can different agents share approvals?** Yes, when Independent Agent Mode is OFF.  
**How do I reset a noisy grant?** Revoke the specific `id` or run **Wipe (repo)**.  
**What if I hit Read‑Only by mistake?** Switch back to **Ask First** or **Full Auto** in the Agent Manager.

---

_This README replaces the “explain me and write something here!” placeholder and formalizes the authority contract for your micro‑agent stack._
