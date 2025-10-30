# README_prompts — Prompt Specs for This Agent

> **High-contrast reminder:** Any UI that renders content from these prompts must maintain strong contrast. This file describes how **ASK**, **DO WORK**, and **TRY HARDER** cooperate, how they evolve with styles, and how the Agent/Codex/LLM should interpret and improve them over time.

## What Lives Here
- **ask.md** — read‑only reasoning and context building; no side‑effects.  
- **do_work.md** — action mode with approvals, audit trail, and “trifecta” updates.  
- **try_harder.md** — recovery & escalation path with alternative plans.  

These files are **contracts** the Agent follows. They are versioned documents: the Agent may propose edits through the normal change process, but must never mutate them silently.

## Relationship to the Trifecta
- **Required‑Updates.md** (desired future) → parsed in Do Work to generate plans and Spec Verification blocks.  
- **README.md** (current truth) → must always reflect the system after successful changes.  
- **Implemented‑/Quarantined‑/Missing‑Updates.md** (status) → maintained each loop; serve as the source of truth for what has been done, blocked, or still absent.

The prompts instruct the Agent to **keep these in sync** and to declare “All implemented, 2025-10-30 01:24:48” when appropriate.

## Styles & Personas
Prompts may vary by **agent style**. If a style is active (e.g., `agent_styles/math/`), the Agent may extend these prompts with style‑specific addenda (e.g., stricter verification, different planning cadence). Style overrides must be explicit and documented in the style’s README.

## Self‑Reflection & Improvement
- The Agent periodically proposes prompt refinements (better checklists, clearer gating, tighter logging) as normal PRs.  
- Use dataset evidence (failures, latency, macro reuse rates) to justify changes.  
- Never reduce contrast or remove guardrails.  
- Any accepted prompt change increments a `prompts/CHANGELOG.md` entry with rationale.

## Integration & Expansion
- Prompts can call into **system tools** (e.g., macro store, OCR pipeline) via documented functions; they do **not** embed executable code.  
- Future tools (e.g., upload manager, plugin manager) should expose minimal, testable interfaces; prompts reference them by name and capability, not by internal implementation.  

## Editing Workflow
1. Propose edits in ASK (no side‑effects).  
2. Stage a Do Work plan that modifies prompt docs.  
3. On approval, write changes and update **README.md** and **Implemented‑Updates.md**.  
4. Re-run Spec Verification on **Required‑Updates.md**.

---

### Quick Glossary
- **Pending Command** — the currently proposed action awaiting approval.  
- **Macro (with beans/TTL)** — a reusable snippet saved in `system_tools/system_macros/` with automatic expiry unless reused.  
- **Rant Feed** — freeform notes promoted into Required‑Updates buckets during Do Work loops.

