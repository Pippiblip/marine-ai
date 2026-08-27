# ORCA — build kickoff prompt

> Paste this as your first message to the coding agent with this repo open, **or** attach this file. `AGENTS.md`, `.cursor/rules/`, `docs/`, and `agents/` are your complete specification — you generate everything else.

---

You are going to build **ORCA — Marine EcOsystem Reasoning with Collaborative Agents**: a voice-first, multi-agent system that turns India's ocean and satellite data into spoken, evidence-backed answers for coastal fishermen, over a web push-to-talk client, WhatsApp, and phone/IVR. It is a Smart India Hackathon 2026 project for ISRO problem statement 26176 (Disaster Management). You are building it **from scratch** in this repository.

This is **safety-critical software**: it gives go/no-go advice to people whose lives depend on it. A wrong wave-height number during a cyclone can kill someone. Build accordingly.

## Read first (do not skip)

1. Read `AGENTS.md` in full.
2. Read `docs/00-overview.md` → `docs/07-testing-and-demo.md` in order.
3. Keep the relevant `agents/0X-*.md` open while implementing each agent.

When instructions conflict, precedence is: **`AGENTS.md` → `docs/` → your own judgment.** If the spec is ambiguous or seems internally inconsistent, **ask me before proceeding — do not guess.**

## Pre-flight check (before writing ANY code)

Reply to me first with a short confirmation proving you've absorbed the spec:

1. The 7 golden rules, in your own words.
2. The MVP scope: which intents and agents are fully built vs. scaffolded, and why.
3. The M0–M8 build order, and the exact acceptance test for M0.

Do not start coding until you've sent this and I've said go.

## How to build

- Follow `docs/06-build-plan.md` **one milestone at a time.** Do not begin milestone N+1 until milestone N's acceptance test passes. Show me the passing `pytest` output at each milestone boundary.
- The whole system must build, test, and run the demo **fully offline with no API keys** — mock LLM, mock speech, fixture data are the defaults. Never introduce a step that requires a network call or a secret to run tests or the demo.
- **Never break a golden rule to make progress.** If a rule blocks you, stop, leave a `# TODO(orca):` comment stating the assumption, and tell me. The golden rules are the entire technical differentiation — they are not negotiable for convenience.
- The LLM only (a) classifies intent and (b) narrates already-retrieved facts. It never invents a number, never decides a safety verdict, never softens one. Safety verdicts and all math are deterministic, unit-tested Python.
- Everything is mock-first: read fixtures behind uniform adapters; leave `RealAdapter` stubs marked `# TODO(orca): wire live endpoint`. Do not call live INCOIS/IMD/ISRO/Copernicus/Bhashini APIs.
- Provider-agnostic AI: all LLM access via `src/orca/llm/base.py`, all speech via `src/orca/speech/base.py`. Agents never import a vendor SDK.
- Conventions: full type hints; typed Pydantic models across every module boundary (no bare dicts); one agent per file, one tool per file; keep `graph.py` thin (composition only). Mark safety-path code `# SAFETY:` and every deferred/scaffold piece `# TODO(orca):` so both are greppable.
- Commit once per milestone minimum, message prefixed with the milestone id (e.g. `M2: deterministic guardrail layer + tests`).

## The bar for "done"

The guardrail layer (`docs/05-guardrails.md`) is the heart of this project — build and test it to a higher standard than anything else. The three demo moments in `docs/07-testing-and-demo.md` must work reliably:

1. A fishing-zone query returns a sourced, timestamped answer.
2. A safety query against a tripped threshold forces a no-go verdict the model cannot soften.
3. **Kill a data source and re-ask** → the system says it can't get current data, refuses to guess, and returns the last-known reading with its timestamp — never an invented number.

That third moment is the project. If it works and is honest, everything else is supporting cast.

## Start

Send the pre-flight confirmation (golden rules, scope, M0 acceptance test). Once I approve, begin M0.
