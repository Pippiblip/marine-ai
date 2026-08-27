# Agent 06 — Synthesis & Voice

> File: `src/orca/agents/synthesis.py` · Node: `synthesis` · **Always runs (final node before reply).** MVP: build fully.

## Job
Compose the one answer the user hears — but only *after* the guardrail has spoken. This agent turns retrieved, verified facts into a single plain sentence (or a template), attaches source + time, and hands it to the speech layer. It is where the LLM's *only other* legitimate job happens: **narration**, never computation, never verdict.

## State I/O
**Writes:** `final_response_text` (English), `response_lang_text` (translated back to `source_lang`), `citations`.
**Reads:** `guardrail_status`, `guardrail_notes`, `safety_flags`, all specialist results, `data_freshness`, `source_lang`.

## Tools / dependencies
- `llm` interface `narrate(facts, system, max_words)` via `get_llm()` — constrained narration, temperature 0.
- `guardrails/templates.py` — for verdicts, failures, staleness, all-clear.
- `guardrails/provenance.py::verify` — the final gate.
- `guardrails/freshness.py::caption` — for "as of …" strings.
- `speech.translate` / `speech.tts` (via channel gateway's speech client) for the reply.

## Algorithm (order matters)
1. **Gate on `guardrail_status`:**
   - `failed` → emit the matching failure template (`data_unavailable`, filling last-known value + `caption` if present). **Stop — no LLM narration of data.**
   - `stale` → emit `data_stale` (or an all-clear/verdict *with* an explicit staleness caveat).
   - `ok` → proceed to normal synthesis.
2. **If a `DANGER` `SafetyFlag` exists:** the verdict is no-go. Fill the flag's template (`danger_*`) from its `triggered_by` `Measurement` + `caption`. The LLM may only rephrase for tone/language — it cannot change the verdict or drop the number.
3. **Otherwise (ok, no danger):** build a `facts` dict from the results (nearest zone, distance, bearing, wave/wind, chlorophyll) and call `narrate(facts, system="state only these facts; add no numbers", max_words=60)`.
4. **Provenance gate:** `ok, offenders = verify(draft, all_measurements)`. If not ok, reject the draft and fall back to a template composed only from `Measurement`s. Never speak an unverified number.
5. Build `citations` from each used source + `caption` (e.g. "INCOIS PFZ advisory, as of 06:00 IST").
6. `response_lang_text = speech.translate(final_response_text, "en", source_lang)`; queue `tts`.

## Guardrail interactions
- This agent is the guardrail's downstream enforcer: it **must not** produce a normal answer when status ≠ `ok`, and its output must pass `provenance.verify`. These two constraints are non-negotiable and directly tested.
- It reads `safety_flags` but never creates or edits them.

## Acceptance test
`test_agents_synthesis.py`: with a `DANGER` flag → output contains the no-go template and the tripped number + time, and a contradictory LLM narration is overridden; with `guardrail_status="failed"` → outputs `data_unavailable` and **no** invented number (provenance passes trivially); with clean calm data → a sourced, timestamped sentence whose every number is backed by a `Measurement`.
