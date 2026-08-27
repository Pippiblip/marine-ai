# Agent 08 — Alert & Notification *(SCAFFOLD / v2 — do NOT fully build)*

> File: `src/orca/agents/alert.py` · **Not** a node in the request/response graph — a separate always-on background loop. **Scaffold only.**

## Why this is scaffold
The request/response graph answers when *asked*. A proactive alerter ("a cyclone just entered your area — do not go out") is a different shape: an always-on watcher that pushes to users unprompted. Valuable, but it needs a scheduler, a user/geo registry, and push infra — out of MVP scope. Build the *structure* and one scripted trigger at most; leave the loop body `# TODO(orca):`.

## Intended job (for the TODO author)
Periodically pull active cyclone/swell warning polygons (IMD/SACHET CAP), check which registered users' locations fall inside (point-in-polygon via `geo/geofence.py`), and push a templated warning to each affected user over their channel. Reuses the **same** deterministic pieces — thresholds, templates, geofence — so alerts are as trustworthy as answers.

## Inputs / outputs
- **Input:** active warning polygons + a registry of `{user_id, location, channel}` (registry is a `# TODO(orca):` — in-memory list for the scripted demo).
- **Output:** outbound messages via `whatsapp_send` / `ivr_speak`, using `guardrails/templates.py` (`danger_cyclone`, etc.). No free-form LLM text in a safety push.

## Scaffold body (what to actually write)
```python
def run_alert_cycle(now=None):
    # TODO(orca): v2 — proactive alerting.
    # 1) fetch active warning polygons (IMD/SACHET CAP)
    # 2) for each registered user: if geofence.point_in_polygon(user.loc, poly): enqueue push
    # 3) push via channel tool using a fixed template (never invented text)
    # For the demo, a single scripted trigger over a fixture polygon is enough.
    return []  # list of (user_id, message_key) that would be sent
```
Provide a `scripts/`-invocable single-shot trigger (not a real scheduler) so the demo can show one proactive alert if time allows.

## Guardrail interactions
- Alerts go through the **same** thresholds and templates as answers — a proactive warning must be as deterministic and sourced as a reactive one. Same rule: no LLM-invented numbers or verdicts.

## Acceptance test (scaffold-level only)
`test_agents_alert.py`: `run_alert_cycle()` runs without error and, given a fixture warning polygon plus one registered user inside it, returns exactly that user in its would-send list (point-in-polygon reused from `geo/geofence.py`). No real network/push in tests.
