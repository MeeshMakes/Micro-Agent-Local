# TRY HARDER — Recovery & Alternatives

> **High-contrast rule:** Status chips (e.g., “RETRYING”, “ALTERNATIVE PLAN”) must be readable, never low‑contrast.

**Purpose**  
Invoked when an operation failed, produced incomplete results, or when the user presses **Try Harder**. Escalate effort **without** hand‑waving: capture precise failure signals, propose concrete alternatives, and re‑stage a new pending command.

## Escalation Playbook
1. **Capture failure** — exact error text, paths, and diff context.  
2. **Diagnose** — is this authority, dependency, environment, or logic?  
3. **Offer 2–3 alternatives** with specific file-by-file steps.  
4. **If authority issue** — add a clear entry to `Quarantined-Updates.md` including the approval sentence needed and scope to unlock.  
5. **If dependency missing** — create a stub fetch/generate task and requeue; do not silently proceed.  
6. **Macro repair** — if a macro failed, mark a **failure bean**, suggest a repaired variant, and re-test quickly.  
7. **Restage** a new pending command using a stronger prompt and updated plan.  
8. **Log** the outcome in `logs/session_<DATE>.md` and update status docs accordingly.

## Stronger Prompt Template (used to regenerate the plan)
```
You failed on: <one-line summary>.

Re-think the plan with sharper constraints:
- Work within repo root: <path> (safe_write_outside_repo = <bool>).
- Target files: <paths>.
- Provide a step list with exact edits and command lines.
- Offer at least 2 viable alternatives; prefer minimal-diff solutions first.
- Verify results and produce an updated Spec Verification block.
```
