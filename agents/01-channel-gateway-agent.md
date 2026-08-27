# Agent 01 — Channel Gateway

> File: `src/orca/agents/channel_gateway.py` · Node: `channel_gateway` · **Always runs (entry node).** MVP: build fully.

## Job
The single front door. Normalize any channel's input (web audio, WhatsApp text/audio, IVR telephony audio) into one schema the graph understands, and prepare the reply path. All speech I/O happens here and only here — no other agent touches audio or language.

## State I/O
**Writes:** `query_text` (English), `source_lang`, `channel`, `user_location`, `trace_id`.
**Reads:** the raw inbound payload passed in by the `api/` layer (audio bytes or text + channel + optional geo).

## Tools / dependencies
- `speech` interface (`detect_language`, `asr`, `translate`) via `get_speech()` — default `MockSpeech`. **Never** import Bhashini/vendor directly.
- No data tools.

## Algorithm
1. Assign `trace_id` (uuid4) for logging this run.
2. If input is audio: `lang = speech.detect_language(audio)`; `text_native = speech.asr(audio, lang)`. If input is text (WhatsApp/typed): set `lang` from channel hint or detect from text.
3. `query_text = speech.translate(text_native, src=lang, tgt="en")`; store `source_lang = lang`.
4. Resolve `user_location`: from the client GPS (web), a saved profile, or a landing-centre name if provided. If none, leave `None` (Synthesis will ask via `location_unknown`).
5. Set `channel` from the transport.

## Guardrail interactions
- None directly, but it sets up the return leg: the *reply* language is `source_lang`, and Synthesis's English output is translated back here on the way out. Keep the translate step symmetric so citations/times survive round-trip.
- If ASR/translate fails, do **not** invent a query — surface an empty/again condition the graph can turn into a "didn't catch that" template.

## Acceptance test
`test_agents_channel_gateway.py`: given a fixture audio id for a Tamil query, writes `source_lang="ta-IN"` and an English `query_text`; given typed English, passes it through; missing location leaves `user_location=None` without crashing.
