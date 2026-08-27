# Agentic marine intelligence platform

A voice-first, multi-agent system that turns INCOIS, IMD, and Copernicus ocean data into spoken answers for fishermen and coastal operators, in their own language, over a phone call, WhatsApp, or an Android app. No dashboards, no IoT hardware, no smartphone required for the base tier.

This document is the system-level spec. Each agent has its own contract in `/agents`. MCP tool definitions live in `MCP_SERVERS.md`.

## Why this exists

INCOIS, IMD, and Copernicus already publish the data that answers "where are the fish" and "is it safe to go out today": sea surface temperature, chlorophyll-a, wave height, cyclone tracks, swell surge advisories. The problem is not data availability. It's that a fisherman with a basic Android phone and patchy signal has no way to ask a GIS portal a question in Tamil or Odia and get a spoken answer back in fifteen seconds.

The platform closes that gap with three things working together: a multi-agent reasoning layer that decomposes a spoken question into API calls, a Bhashini-based speech pipeline for 22 Indian languages, and three access channels (app, WhatsApp, phone call) so the entry cost is zero for anyone who already owns a phone.

## Design principles

**Reliability beats speed.** A wrong wave-height answer during a cyclone can kill someone. Every number that reaches the user comes from an API response, never from the language model's own estimate. If a data source is down or the last reading is stale, the system says so out loud instead of guessing. See [Guardrails](#guardrails-the-part-that-keeps-people-alive) below.

**Voice first, chat as fallback.** The primary interaction is push-to-talk: speak a question, hear an answer. Text chat (WhatsApp, in-app) exists for people who prefer typing or are in a place too loud to talk, but no feature requires reading.

**Three channels, one brain.** App, WhatsApp, and a dial-in phone number all route through the same Router and Bhashini pipeline. A fisherman without a smartphone still gets full functionality by calling a number.

**Offline degrades gracefully, it doesn't fail.** Past the edge of cellular coverage, a quantized on-device model answers geofencing and PFZ-bearing questions from the last cached advisory, with the cache timestamp always stated.

## Access channels

| Channel | Who it's for | Transport | Latency budget |
|---|---|---|---|
| Android app (push-to-talk) | Smartphone owners, works offline past the coastline | Raw audio over WebSocket direct to Bhashini streaming ASR | under 3s round trip |
| WhatsApp | Anyone with WhatsApp, voice notes or text | Meta WhatsApp Business Cloud API webhook | 5-8s acceptable |
| Phone call (IVR) | Feature phones, zero data cost | PSTN via Exotel/Twilio Voice, media streamed to Bhashini | under 4s per turn |

Full channel handling: [`agents/01-channel-gateway-agent.md`](agents/01-channel-gateway-agent.md).

## System flow

```
                         ┌─────────────────────────────────────┐
                         │           ACCESS CHANNELS             │
                         │  Android app │ WhatsApp │ Phone call  │
                         └──────────────────┬────────────────────┘
                                             │ audio / text
                                             ▼
                         ┌─────────────────────────────────────┐
                         │        Channel Gateway Agent          │
                         │  normalizes input, runs Bhashini ASR  │
                         └──────────────────┬────────────────────┘
                                             │ {text, lang, geo, channel}
                                             ▼
                         ┌─────────────────────────────────────┐
                         │       Router & Planning Agent         │
                         │  intent classification, task graph    │
                         └──┬─────────┬──────────┬───────────┬──┘
                            ▼         ▼          ▼           ▼
                     ┌──────────┐┌─────────┐┌──────────┐┌──────────┐
                     │  Marine  ││Weather &││Geospatial││  Ocean   │
                     │   Data   ││  Risk   ││Reasoning ││Analytics │
                     │Discovery ││Assessment││  Agent   ││  Agent   │
                     └────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘
                          │           │            │           │
                          └───────────┴─────┬──────┴───────────┘
                                             ▼
                         ┌─────────────────────────────────────┐
                         │      Guardrail & Confidence Layer     │
                         │  hard-coded thresholds, staleness     │
                         │  checks, source-timestamp binding     │
                         └──────────────────┬────────────────────┘
                                             ▼
                         ┌─────────────────────────────────────┐
                         │         Synthesis & Voice Agent       │
                         │   builds spoken response, Bhashini TTS│
                         └──────────────────┬────────────────────┘
                                             ▼
                                    back to originating channel

              ┌─────────────────────────────────────────────────┐
              │  Alert & Notification Agent (runs continuously,  │
              │  not query-triggered) → WhatsApp broadcast, SMS, │
              │  outbound IVR call for cyclone / swell surge     │
              └─────────────────────────────────────────────────┘
```

## Agent roster

| Agent | Job | Reads from |
|---|---|---|
| [Channel Gateway](agents/01-channel-gateway-agent.md) | Normalizes app, WhatsApp, and phone-call input into one schema; runs ASR/TTS per channel | Bhashini ULCA |
| [Router & Planning](agents/02-router-planning-agent.md) | Classifies intent, builds the task graph, holds LangGraph state | Internal only |
| [Marine Data Discovery](agents/03-marine-data-discovery-agent.md) | Potential Fishing Zone coordinates, bathymetry | INCOIS WebGIS, INCOIS text API |
| [Weather & Risk Assessment](agents/04-weather-risk-agent.md) | Wave height, wind, cyclone proximity, swell surge; the only agent allowed to raise a safety alert | IMD REST API, INCOIS OSF, INCOIS SIVAS |
| [Geospatial Reasoning](agents/05-geospatial-reasoning-agent.md) | Distance, bearing, routing, point-in-polygon geofencing against MPAs and the IMBL | GeoPandas, Shapely, IMBL shapefiles |
| [Ocean Analytics](agents/06-ocean-analytics-agent.md) | Historical trend analysis for "why did productivity drop" style questions | Copernicus Marine Toolbox |
| [Synthesis & Voice](agents/07-synthesis-voice-agent.md) | Turns agent outputs into one spoken, evidence-cited answer | Bhashini TTS |
| [Alert & Notification](agents/08-alert-notification-agent.md) | Proactive push for cyclone cones and swell surge, independent of any user query | INCOIS SIVAS, IMD Cyclone Track |

## Orchestration state

LangGraph holds one shared state object across the whole run. Every agent reads what it needs and writes its own section; nobody overwrites another agent's output.

```python
class PlatformState(TypedDict):
    query_text: str              # transcribed, translated to English
    source_lang: str              # e.g. "kn-IN"
    channel: Literal["app", "whatsapp", "ivr"]
    user_location: tuple[float, float] | None   # lat, lon
    intent: str                   # set by Router
    subtasks: list[str]           # agent names to invoke, set by Router
    marine_data_result: dict | None
    weather_risk_result: dict | None
    geospatial_result: dict | None
    ocean_analytics_result: dict | None
    safety_flags: list[SafetyFlag]  # only Weather & Risk Agent may append
    data_freshness: dict[str, datetime]  # source name -> timestamp of last successful fetch
    final_response_text: str
```

`safety_flags` and `data_freshness` are the two fields the Synthesis Agent is required to check before it's allowed to speak. See [Guardrails](#guardrails-the-part-that-keeps-people-alive).

## MCP tools

INCOIS, IMD, Copernicus, Bhashini, and the outbound channels are each wrapped as MCP tools rather than hard-coded API clients, so the Router discovers what's available from tool schemas instead of from code that has to change every time an endpoint changes. Full tool signatures, request/response shapes, and which agent owns which tool: [`MCP_SERVERS.md`](MCP_SERVERS.md).

## Guardrails: the part that keeps people alive

This is the section that separates a demo that looks good from one a coast guard would actually trust.

1. **No LLM-generated safety thresholds.** "Is 2.8m safe" is answered by a hard-coded Python function in the Weather & Risk Agent (`wave_height_m > 2.5 or wind_speed_kt > 25 → unsafe`), not by the language model. The LLM only formats the verdict into a sentence. It cannot override it.
2. **Every number carries a timestamp.** The `data_freshness` field tracks when each upstream source last answered successfully. If the last IMD cyclone-track fetch is older than 30 minutes, the Synthesis Agent must say "as of [time]" and, for anything in the safety-critical path, must retry before answering.
3. **Retries before guesses.** Each MCP tool call gets 3 attempts with exponential backoff (1s, 2s, 4s). A 429 triggers a queued retry; a 401 triggers a silent token refresh and replay, never a user-facing error mid-conversation.
4. **Explicit failure over confident silence.** If wave height or cyclone data cannot be retrieved after retries, the response is: "I couldn't get current wave and wind data for your area. The last reading I have is from [time] and showed [value]. Don't use that for a decision right now." That sentence is a template, not something the model composes freely.
5. **Circuit breaker per upstream.** If IMD returns 5 consecutive failures, the platform stops hammering it for 5 minutes and serves cached data with a staleness warning instead of retrying on every incoming query.
6. **One quote, cross-checked.** For "why did productivity drop" style questions, the Ocean Analytics Agent's historical read is stated as an observation from the data ("chlorophyll-a in this cell dropped 40% over six months"), never as a causal claim the model invents on its own.

## Example query trace

**Spoken query (Tamil, via phone call):** "இன்று அருகிலுள்ள மீன்பிடி மண்டலம் எங்கே?" ("Where is the nearest fishing zone today?")

1. Channel Gateway receives the call over the Exotel media stream, forwards audio to Bhashini streaming ASR, gets back `"Where is the nearest fishing zone today?"` plus `source_lang: ta-IN`. Caller ID is matched to a saved GPS location from a prior app session (or the caller states a landmark, which the Geospatial Agent geocodes).
2. Router classifies intent as `pfz_nearest`, dispatches to Marine Data Discovery Agent.
3. Marine Data Discovery Agent calls the `incois_get_pfz` MCP tool with today's date and a bounding box around the caller's coast. Gets back a GeoJSON array of active PFZ nodes with lat/lon, bathymetry, and bearing references.
4. Geospatial Reasoning Agent runs a Haversine calculation across the returned nodes against the caller's location, picks the nearest one.
5. Weather & Risk Agent checks that node's coordinates against the current IMD cyclone cone and INCOIS SIVAS alerts. Clear, no flag raised.
6. Guardrail layer confirms `data_freshness["incois_pfz"]` is under 6 hours old (INCOIS refreshes PFZ advisories once daily) and no safety flags are pending.
7. Synthesis Agent composes: "The nearest fishing zone today is about 14 kilometers southwest of [landmark], depth around 45 meters. Conditions are clear, no wave or cyclone warnings for that area as of this morning's advisory."
8. Bhashini TTS renders that in Tamil, streamed back into the live call in overlapping chunks so the caller starts hearing a response before the full sentence finishes generating.

## Growth mechanic: shareable daily card

Every WhatsApp and app answer generates a follow-up share card, a satellite visual plus a one-line verdict, sent as a separate message a few seconds after the voice answer so it never adds latency to a safety-critical response. The mechanic is structural, not promotional: the card is what gets forwarded into fishing-community WhatsApp groups, and each forward is a person who's never used the platform seeing it for the first time. Full behavior and its guardrail constraints: [`agents/07-synthesis-voice-agent.md`](agents/07-synthesis-voice-agent.md#shareable-card-whatsapp-and-app-only).

## MVP demo script

Three queries that show the full stack working end to end, meant to run live in front of judges in under five minutes.

1. **"Where's the nearest fishing zone?"** over an actual phone call to a real number, not a simulator. Proves the IVR channel and Bhashini streaming latency are real.
2. **A cyclone-risk query sent as a WhatsApp voice note** while the Weather & Risk Agent's hard threshold is deliberately tripped (query a coordinate inside a live or simulated cyclone cone). Shows the guardrail forcing a red-alert answer that the LLM cannot soften.
3. **Kill the INCOIS API mid-demo** (block the endpoint) and ask a PFZ question again. Shows the platform saying "I couldn't get current data, here's the last known reading from [time]" instead of inventing coordinates. This is the moment that separates the project from every other hackathon chatbot in the room.

## Repository layout

```
/README.md                              this file
/MCP_SERVERS.md                         MCP tool contracts for every data source and channel
/agents/
  01-channel-gateway-agent.md
  02-router-planning-agent.md
  03-marine-data-discovery-agent.md
  04-weather-risk-agent.md
  05-geospatial-reasoning-agent.md
  06-ocean-analytics-agent.md
  07-synthesis-voice-agent.md
  08-alert-notification-agent.md
```

## What's deferred past MVP

Worth stating outright rather than pretending scope is smaller than it is. Cut for v1, planned for v2: the on-device ExecuTorch offline model (v1 ships app-online-only with a "no signal" message instead of true offline geofencing), multi-turn conversation memory across calls, and the Ocean Analytics Agent's Copernicus integration (v1 answers "where are the fish" and "is it safe," not "why did the fishery decline," since that needs the heaviest data pipeline for the least demo impact).