# 00 — Overview

## What ORCA is

ORCA is a **voice-first, multi-agent conversational assistant** that turns India's fragmented ocean and satellite Earth-Observation data into **spoken, evidence-backed answers** for coastal fishermen, in their own language, over channels that cost nothing to adopt.

A fisherman asks, out loud, *"Where's the nearest fishing zone today?"* or *"Is it safe to go out tomorrow morning?"* A set of specialist AI agents, coordinated by a planner, breaks that into data lookups (fishing zones, weather, cyclone tracks, boundaries), reconciles the results, checks them against **deterministic safety rules**, and speaks back one clear answer that **cites its source and time** — or, if data is stale or missing, says so plainly instead of guessing.

The whole point is the **last mile**: the data that answers these questions already exists (ISRO satellites, INCOIS advisories, IMD warnings), but it lives in GIS portals, NetCDF files, and English PDFs a low-literacy fisherman with a basic phone cannot query. ORCA is the reasoning-and-access layer on top of that data.

## Who it's for

- **Primary user:** a marine fisherman with a basic or mid-range phone, limited literacy, patchy signal, speaking a regional Indian language. May be planning a trip from shore or operating near the coast.
- **Secondary:** coastal disaster-management authorities, the Coast Guard, and fisheries field officers who want the same synthesized picture.

Design implications that flow from this user, and that you must honor in the build:
- **Voice is primary, text is fallback.** No feature may *require* reading.
- **Zero adoption cost.** A phone call (IVR) must give full functionality to someone with no smartphone and no data plan.
- **Trust is everything.** The user is betting their safety on the answer. Wrong-but-confident is far worse than "I don't know right now."

## The signature idea (this is what you are really building)

Most hackathon chatbots hallucinate confidently. ORCA's differentiator is a **deterministic guardrail layer** that makes the system *reliable enough to trust with a life*:

- safety verdicts come from hard-coded thresholds, not the language model;
- every number is bound to a source and a timestamp;
- stale or missing data produces an explicit "don't rely on this" instead of a guess.

If you build nothing else well, build **this** well. See `docs/05-guardrails.md`.

## Scope — what to build now vs. later

This project is **MVP-first with a full scaffold**. That means: lay out the structure for the *whole* system, but only *fully implement* the MVP slice. Everything else is created as a clearly-marked stub and left for later.

### ✅ MVP — build these fully (Milestones M0–M6, hardened in M8)

| Area | In the MVP |
|------|------------|
| **Intents** | Exactly two: `pfz_nearest` ("where's the nearest fishing zone?") and `safety_check` ("is it safe to go out?"). |
| **Agents** | Channel Gateway, Router & Planning, Marine Data Discovery, Weather & Risk, Geospatial Reasoning, Synthesis & Voice. |
| **Guardrails** | The full deterministic layer: thresholds, freshness/timestamps, retries+backoff, circuit breaker, explicit-failure templates, "number must exist in retrieved data" check. |
| **Data** | **Mock-first** — every source wrapped as an adapter reading realistic fixtures. |
| **Speech** | ASR + TTS behind an interface, with a **mock implementation** as default and a Bhashini adapter stubbed. Languages: architect for many, demo Tamil + Hindi + English. |
| **Channels** | A **browser push-to-talk web client** (primary, easiest to demo) + WhatsApp Cloud API webhook + Exotel/Twilio IVR handler. |
| **Geospatial** | Haversine nearest-zone; point-in-polygon geofence against the IMBL (International Maritime Boundary Line). |

### 🟡 Scaffold — create the files/interfaces, leave `# TODO(orca):` bodies (do NOT fully build)

- **Ocean Analytics Agent** (historical "why did productivity drop" via Copernicus) — heaviest pipeline, least demo value. Stub only. See `agents/07-ocean-analytics-agent.md`.
- **Alert & Notification Agent** (always-on proactive cyclone/swell push) — stub the background-job structure and the point-in-polygon trigger; wire a single scripted trigger at most. See `agents/08-alert-notification-agent.md`.
- **Real data adapters** for INCOIS/IMD/ISRO/Copernicus/Bhashini — `RealAdapter` classes next to each mock adapter, bodies `# TODO(orca):`.
- **MCP server exposure** of the tools (M7) — optional; the tools work as typed Python functions without it.
- **Shareable daily card**, **IMBL proactive voice-alert**, **multi-turn memory** — mention in `README.md` roadmap; do not build.

### 🔴 Out of scope entirely (do not create, just note as v2 in README)

- Native Android/iOS app (the web client stands in for push-to-talk).
- True on-device offline inference (ExecuTorch).
- Deep-sea connectivity beyond cellular (documented as a NavIC/GEMINI *integration* story, not built).

## What success looks like

A judge (or you) can:
1. Speak/type "where's the nearest fishing zone?" through the web client and hear a sourced, timestamped answer.
2. Ask a safety question against a tripped threshold and watch the guardrail force a red-alert answer the model can't soften.
3. **Kill a data source mid-demo** and re-ask — and the system explicitly says it can't get current data and gives the last known reading with its time, instead of inventing an answer.

That third moment is the project. Everything in `docs/06-build-plan.md` builds toward being able to run it reliably.
