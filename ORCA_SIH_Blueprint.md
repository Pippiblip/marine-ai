# ORCA — Marine EcOsystem Reasoning with Collaborative Agents
### SIH 2026 Blueprint: Idea Validation · Market Research · Technical Architecture · Roadmap

**Problem Statement:** SIH 2026 · PS ID 26176 · *ORCA – Marine EcOsystem Reasoning with Collaborative Agents*
**Organization:** Indian Space Research Organisation (ISRO), Department of Space · **Category:** Software · **Theme:** Disaster Management
**Prepared as:** a single working document usable (a) as a build brief for Claude Code and (b) as a source for pitch-deck slides.

---

> ## How to read the sourcing in this document
>
> The **analysis** here — positioning, competitive framing, architecture, roadmap, risk assessment — is my own reasoning; treat it as fully usable. The **facts** (statistics, scheme outlays, satellite specs, data-source behavior, paper references) are drawn from established domain knowledge current to roughly mid-2025, and are stated plainly where I'm confident. Two light flags mark the exceptions:
>
> - `[CHECK]` — an exact figure, date, or ID worth a 30-second confirmation before it goes on a slide. The *claim* is sound; the *precise number* is what to double-check.
> - `[POST-2025]` — something that may have changed after my knowledge horizon (a scheme's latest outlay, a portal's current API status, or any competing product launched in 2025–26). Confirm the current state.
>
> Everything untagged is high-confidence — build and pitch from it as-is. Appendix B lists the primary source for each flagged item so a confirmation pass is quick.

---

## Table of contents

1. **Stage 1 — Understand & Position the Idea** — what it is, SIH fit, the pitch angle, and fixing what sounds hand-wavy
2. **Stage 2 — Competitive & Market Research** — what exists, the gaps, how we differentiate, and the adoption path
3. **Stage 3 — Technical Architecture Blueprint** — components, every pipeline explained, tech stack, and the riskiest parts
4. **Stage 4 — Feature & Roadmap Recommendations** — MVP vs pitch vs future scope, and the live demo script
5. **Appendix A** — How SIH is judged and how ORCA maps to it
6. **Appendix B** — Sources & fact-verification checklist
7. **Appendix C** — Ready-to-paste Claude Code kickoff prompt

---

# Stage 1 — Understand & Position the Idea

## 1.1 The idea, in my own words

**ORCA is a voice-first, multi-agent conversational assistant that turns India's fragmented ocean and satellite Earth-Observation data into spoken, evidence-backed answers for coastal communities — primarily marine fishermen — in their own language, over channels that cost nothing to adopt.**

Under the hood, a set of specialized AI agents, coordinated by a central planner (LangGraph), takes a spoken question like *"Where's the nearest fishing zone today?"* or *"Is it safe to go out tomorrow morning?"* and breaks it into a plan of data lookups. Each data source — INCOIS advisories, IMD weather and cyclone warnings, ISRO satellite products (sea-surface temperature, chlorophyll), Copernicus ocean data — is wrapped as a standard "tool" (via the Model Context Protocol) that the planner can call. A **deterministic guardrail layer** then checks the results against hard-coded safety rules and data-freshness timestamps, so that **every number the user hears comes from a real data response, never from the language model's own guess.** Finally, a speech pipeline built on **Bhashini** (India's national language-AI stack) renders the answer as natural speech in the user's language.

Three access channels share one brain:
- **Android app** (push-to-talk) for smartphone owners,
- **WhatsApp** (voice notes or text) for anyone with WhatsApp,
- **a dial-in phone number / IVR** for feature-phone users with zero data cost.

**The core problem it solves.** The data that answers *"where are the fish"* and *"is it safe to go out"* already exists — ISRO and INCOIS generate it daily from satellites. The failure is the **last mile**: that data lives in GIS web-portals, scientific NetCDF files, English PDFs, and one-way broadcasts. A fisherman with a basic phone, limited literacy, patchy signal, and no English cannot *ask a question* of a GIS portal and get a reasoned, spoken answer back in seconds. ORCA closes that last-mile **reasoning + access** gap.

**Who it's for.**
- **Primary:** India's marine fishermen — roughly **4 million people** across 9 coastal states, disproportionately small-boat and traditional operators (CMFRI Marine Fisheries Census; a more recent census may have updated the exact count — `[POST-2025]`).
- **Secondary:** coastal disaster-management authorities, the Indian Coast Guard, port/maritime operators, and fisheries-department field officers who need the same synthesized picture.

## 1.2 Is this a strong fit for SIH? (honest assessment)

SIH judges reward four things above all: **real-world impact, feasibility, innovation, and scalability.** Here is where ORCA genuinely stands on each — including where it's weak.

**Impact — very strong (this is the project's biggest asset).**
The beneficiary population is huge, identifiable, and underserved, and the stakes include human life, not just convenience. Three concrete impact hooks:
- **Life safety / disaster management:** Cyclone Ockhi (Nov–Dec 2017) killed **over 245 people with hundreds of fishermen missing** (`[CHECK]` the exact toll — figures were revised repeatedly), and was widely criticized for warnings failing to reach boats already at sea. This is exactly the "Disaster Management" theme of the PS.
- **Livelihood:** PFZ guidance cuts fuel and search time; safety guidance prevents lost boats and gear.
- **Geopolitical / rights:** accidental crossings of the International Maritime Boundary Line (IMBL) lead to hundreds of Indian fishermen being detained each year, with a notably sharp spike in 2024 (`[CHECK]` the exact count). A spoken "you are approaching the maritime boundary — turn back" alert addresses this directly.

**Alignment with *this* problem statement — strong, but needs recentering.**
This is the single most important strategic point in the document. The PS is issued by **ISRO / Department of Space**, under a **Disaster Management** theme, and its language emphasizes **satellite Earth Observation data** and **autonomous/agentic AI** for **conversational** decision support. Your `README` currently leads with INCOIS/IMD/Copernicus data and a fishing-livelihood narrative. That's not wrong — but to land with *these specific judges*, you must **foreground ISRO's own satellite EO** (Oceansat-3 / EOS-06 Ocean Colour Monitor for chlorophyll, sea-surface temperature products, and ISRO data portals like MOSDAC/Bhuvan) and the **disaster-management safety angle**, with fishing livelihood as the human story that makes it matter. (This is the synthesis positioning you selected — see §1.3.)

**Innovation — real, but must be claimed honestly.**
The individual building blocks are established, not novel: LangGraph multi-agent orchestration, MCP tool-wrapping, retrieval-grounded answers, and Bhashini speech are all proven patterns (see Stage 3 and Appendix B). **The novelty is the integration**: an agentic, multi-source reasoning system with a *deterministic safety-grounding layer* and *22-language voice*, aimed at a population and a data ecosystem (ISRO/INCOIS) that no existing conversational product serves. That is a defensible **"systems novelty"** claim. Judges respond well to a team that says "we didn't invent a new model; we engineered a reliable system out of proven parts for a problem nobody has solved for this user" — and badly to teams that oversell a "new AI."

**Feasibility in a hackathon window — feasible only if scoped hard.**
The full vision is genuinely large (three channels, 22 languages, offline model, historical analytics, deep-sea coverage). The good news: your `README` already **defers** the on-device offline model, cross-call memory, and the Copernicus historical-analytics agent to v2 — that's exactly the right instinct. To be demo-ready you should narrow further (see Stage 4): two query types (PFZ + safety), 2–3 languages live, one or two channels shown end-to-end, and the guardrail demonstration. The architecture can *describe* the full system while the demo *proves* a sharp slice.

**Scalability — strong, and easy to argue.**
ORCA rides on rails that already exist and already scale: INCOIS data feeds, Bhashini language models, NavIC/GEMINI hardware, and the new National Fisheries Digital Platform registry. Marginal cost per additional user is low; IVR and WhatsApp scale to millions; the cloud backend is horizontally scalable. The scaling story is "plug into government infrastructure that's already funded," which is far more credible than "we'll build our own."

**Bottom line.** This is one of the stronger possible responses to PS 26176 — *if* you (1) recenter the narrative on ISRO satellite EO + disaster management, (2) scope the demo ruthlessly, (3) lead with the safety/guardrail behavior as your technical signature, and (4) are honest about novelty and about deep-sea connectivity limits. Done that way, it reads as feasible **and** as something with a real future, not a toy.

## 1.3 The angle to pitch from

**Recommended positioning (synthesis): "The data to protect a fisherman's life and livelihood already exists. ORCA is the voice that finally delivers it — in his language, in seconds — and refuses to guess when lives are on the line."**

Build the pitch on three pillars, in this order:

1. **Satellite Earth Observation as the hero data (for ISRO judges).** Lead with ISRO's own eyes in the sky: Oceansat-3 / EOS-06's Ocean Colour Monitor (chlorophyll) and SST products are the raw signal behind Potential Fishing Zones. Show the pipeline from *satellite → fish location → spoken answer*. This directly honors "satellite Earth Observation data" in the PS and uses ISRO assets, which ISRO judges reward.
2. **Disaster management as the stakes (for the theme).** The safety path — cyclone cones, high-wave and swell-surge alerts → *"is it safe to go out?"* → a red-alert answer the model cannot soften — is the emotional and thematic core. Anchor it to Ockhi and to the last-mile dissemination failure that killed people.
3. **Agentic reliability as the technical signature (for the "how").** The differentiator isn't "a chatbot for fishermen" — it's a system that **cites its sources, timestamps every number, and says 'I don't know, don't rely on this' instead of hallucinating** when data is stale or missing. That is the line that separates you from every other LLM demo in the room.

**Frame ORCA as an intelligence layer on top of government rails, not a competitor to them.** INCOIS already owns dissemination (Sagar Vani); ISRO owns the satellites and NavIC; Bhashini owns the language stack. Position ORCA as the *conversational reasoning layer* that sits on those rails. This does three things at once: it de-risks data access (you're a partner, not a rival), it gives you a credible deployment owner (INCOIS / Department of Fisheries), and it makes the scaling story free.

**Impact framing to put on the title slide:** ~4M marine fishermen; ~58% literacy in fishing communities (why *voice*, not text — `[CHECK]` the exact CMFRI figure); Ockhi's toll (why *fast, reachable* warnings); IMBL detentions (why *boundary alerts*). Numbers + a face.

## 1.4 What currently sounds hand-wavy — and how to reframe it

Judges (and mentors) will poke exactly these spots. Pre-empt each one.

**"22 Indian languages."** As stated, it invites the question "show me all 22 working." **Reframe:** "Architected for all 22 scheduled languages via Bhashini; demonstrated live in Tamil, Hindi, and one more." Bhashini's *translation* covers the 22 scheduled languages, but *speech recognition and text-to-speech* cover fewer and vary in quality, and coverage keeps expanding — check the current per-service language list before you name a number. Claim the architecture, demo a credible subset, and name the constraint before they do.

**"Under 3-second voice round trip."** A full loop of speech-recognition → translation → multi-agent reasoning → several live API calls → text-to-speech in 3 seconds is very hard, especially over a noisy 8 kHz phone line. **Reframe:** state a *realistic, tiered* latency budget (e.g., near-instant acknowledgement + streamed/overlapping TTS so the user hears the answer forming; cached daily advisories for the common PFZ query), and *show* the number you actually hit rather than promising 3s. Honesty about latency reads as engineering maturity.

**On-device offline model (ExecuTorch).** Already deferred to v2 in your `README` — good. Keep it strictly as *future scope*; do not attempt to demo true offline inference. Over-promising offline AI on a feature phone is a credibility risk.

**"Works over a phone call at sea."** App/WhatsApp/phone-call all need cellular, which typically ends ~10–20 km offshore, while boats routinely go 50–300+ km out. **Reframe honestly:** ORCA's strength is **pre-departure planning + near-shore operation + relaying**; for the deep-sea leg it **integrates with / hands off to** ISRO's NavIC messaging transponders and INCOIS's GEMINI device (which use satellite, not cellular). Owning this limit — and turning it into an integration story — is far stronger than letting a judge expose it.

**"Agentic AI" as a buzzword.** Don't just say "agentic." Show *why* multiple agents earn their keep: (a) **separation for safety** — only one agent can raise a safety flag, and it uses hard-coded thresholds; (b) **source attribution** — each agent owns one data domain, so every claim is traceable; (c) **parallelism** — weather, fishing-zone, and geospatial lookups run at once. If a single prompt could do it, judges will ask why the complexity; have the answer ready.

**Safety liability.** Spoken go/no-go advice can get someone killed if it's wrong. **Reframe the risk as the feature:** a deterministic rule layer (not the LLM) issues the safety verdict; INCOIS/IMD advisories are the source of truth; stale data triggers an explicit "don't rely on this" template; and every answer carries a timestamp and a disclaimer. This is precisely the guardrail story from your `README` — make it central, not a footnote.

**"Reasoning about the marine ecosystem" / "why did productivity drop."** This (the Ocean Analytics / Copernicus historical path) is the heaviest data pipeline for the least demo impact, and is already deferred in your `README`. Keep it as a **future-scope** storytelling item; don't build it for the demo.

---

# Stage 2 — Competitive & Market Research

## 2.1 The landscape

The important insight is that **India's marine-data ecosystem is authoritative on content but structurally unusable for a fisherman as-is.** The data is world-class; the delivery is portals, PDFs, NetCDF files, and one-way broadcasts. Competition therefore falls into four buckets: government dissemination systems, fisher-facing apps, satellite hardware devices, and global comparators. Crucially, **no deployed product today offers conversational, voice-first, multilingual, safety-gated ocean reasoning for Indian fishers** — that is the whitespace.

> **The one thing worth confirming:** whether INCOIS / MoES / Bhashini launched any *conversational or voice AI assistant for fishers* in 2025–26. That is the only thing that could be a direct competitor, and it's the one item squarely after my knowledge horizon. `[POST-2025]`

## 2.2 Comparison table

| Solution | What it does | Strengths | Weaknesses / the gap ORCA exploits |
|---|---|---|---|
| **INCOIS Sagar Vani** (launched 2017, MoES) — *closest incumbent* | Multi-modal dissemination of PFZ, ocean-state, high-wave, swell-surge, tsunami alerts via SMS, app, IVR/audio, social media, harbour display boards, in ~9–10 languages | Official, authoritative, free, multi-channel, real government reach | **One-way broadcast, not Q&A.** Its "voice" is pre-recorded/IVR, not conversational. No free-form questions, no personalization, no multi-source synthesis, no reasoning |
| **Fisher Friend Mobile App (FFMA)** — MSSRF + Qualcomm + TCS | Android app bundling PFZ, weather, disaster alerts, IMBL crossing alerts, market prices, SOS numbers; icon-driven for low literacy | Purpose-built for low-literacy fishers; multi-feature; deployed across coastal states | Menu/screen app, **not conversational**; smartphone + install + literacy required; only a handful of languages; no live AI IVR; no multi-source reasoning or citations |
| **mKRISHI Fisheries** — TCS | Fuses INCOIS PFZ + IMD wind/wave into a "best-zone / go–no-go" advisory, often with a rugged onboard GPS device | Smart fusion of PFZ + weather; fuel-saving value proposition | Pilot-scale, not a public rollout; hardware dependency; one-way advisory; few languages; no phone/WhatsApp channel; no conversational reasoning |
| **GEMINI + NavIC / GAGAN devices** — INCOIS/ISRO | Onboard hardware that receives INCOIS advisories (PFZ, ocean-state, cyclone, tsunami, high-wave) via satellite up to ~300 km offshore, relayed to a phone app | **Solves deep-sea connectivity** cellular can't reach; official; regional languages | Extra hardware to buy/charge/carry; **one-way broadcast**, no interactivity or reasoning; few languages. *Complement, not a rival — integrate with it* |
| **Kadal Osai 90.4 FM** | Community radio for the Rameswaram fishing community — sea conditions, safety, prices, IMBL awareness, in Tamil | Deep community trust; genuinely reaches low-literacy users | Broadcast radio (one-way), single locality, Tamil only, no interactivity or personalization |
| **ABALOBI** (South Africa) | App suite for small-scale fishers: catch logbook, "Fish with a Story" traceability marketplace, co-management data | Strong livelihoods + traceability model; award-winning | Not weather/safety/PFZ; not voice/conversational; smartphone-required; few languages. Different problem |
| **Global Fishing Watch** | Global map/API of commercial fishing activity from AIS + satellite + ML, for transparency & enforcement | Excellent open data/API; global scale | A monitoring/transparency tool for governments & NGOs, **not an advisory for individual fishers**; English; dashboard/API only |
| **Windy / Windguru / PredictWind** | Marine weather visualization (wind, waves, swell) from global models | Polished, localized UI; trusted by sailors | Generic weather maps, not India-tailored PFZ/safety; not INCOIS-integrated; not voice; require literacy + data + map-reading; English/technical |
| **mFisheries** (Univ. of West Indies) | Academic toolkit for small-scale fishers incl. research on voice/TTS for low-literacy users | Proves voice-for-fishers is a valid direction | Research/prototype scale; not LLM-based; not multilingual-at-scale. *Validates the direction and the whitespace* |
| **Conversational AI for ocean data** (global, e.g. NOAA/Copernicus experiments; EU Digital Twin of the Ocean) | Experimental AI/chat over ocean datasets, aimed at scientists | Signals the direction of travel | Aimed at researchers, not artisanal fishers; not Indian languages; not safety advisories; not voice-first |

## 2.3 How we differentiate (concrete, not "better UI")

Seven differentiators, each a functional or strategic capability no incumbent combines:

1. **Conversation, not broadcast.** Every incumbent *pushes* fixed advisories. ORCA answers *free-form* questions — "is it worth going 20 km southwest tomorrow morning, and is it safe?" — by synthesizing multiple sources into one reasoned answer. This is the categorical difference.
2. **Voice-first, over the phone too.** Not just an app: a **dial-in IVR number** means a feature-phone owner with no data and no literacy gets the full service. That erases the two biggest adoption barriers (smartphones and reading) that every app-based competitor is stuck behind.
3. **Multi-source fusion into a single answer.** Today PFZ (INCOIS), weather (IMD), boundary (Coast Guard), and satellite EO (ISRO) live in separate silos and separate apps. ORCA's agents fuse them: one question, one answer that already reconciles fishing opportunity *and* safety *and* boundary.
4. **Deterministic safety guardrails + evidence citation + staleness handling.** This is the signature. The safety verdict comes from hard-coded rules, not the LLM; every number is timestamped and sourced; stale/missing data produces an explicit "don't rely on this" instead of a confident guess. **No fisher-facing chatbot does this** — and for safety-critical advice it's the difference between trustworthy and dangerous.
5. **22-language *spoken conversation*, not static translation.** Incumbents offer a few languages as fixed translations of fixed advisories. ORCA does spoken dialogue via Bhashini, including handling of dialects and code-mixing (a hard problem, honestly scoped).
6. **Rides government rails + integrates with deep-sea hardware.** Built as a layer on INCOIS/ISRO/Bhashini, and designed to hand off to NavIC/GEMINI for the offshore leg — so it covers the whole journey rather than competing on one segment.
7. **The IMBL boundary voice-alert.** A spoken, proactive "you are nearing the international maritime boundary — turn back" ties a sharp, quantifiable impact story (detentions) to a feature the conversational/geospatial stack already makes possible.

## 2.4 Market, impact & the real-world adoption path

**Scale of the opportunity** (sources in Appendix B):
- **~4 million marine fisherfolk**, roughly 864,550 fishing families across ~3,288 fishing villages and ~1,511 landing centres (CMFRI Marine Fisheries Census — `[CHECK]` the exact counts; the census is 15+ years old and a newer round may have revised them, `[POST-2025]`).
- **9 coastal states + 4 UTs**; official coastline **7,516.6 km** (a 2023–24 remapping revised the national coastline length upward — `[CHECK]` the current official figure before quoting it).
- India is the **world's 2nd-largest fish producer** (~8% of global output); seafood exports on the order of **₹60,000 cr / ~US$7+ bn** in a recent year (`[CHECK]` the exact FY figure — MPEDA).
- **Just under 60% literacy** among marine fisherfolk (CMFRI) — the core argument for a voice-first, regional-language interface (`[CHECK]` the exact percentage).
- Cellular typically ends **~10–20 km offshore**; boats operate **50–300+ km** out — the argument for the NavIC/GEMINI integration.

**Who would actually adopt it, and how.** Frame ORCA not as a standalone app hoping for downloads, but as the **spoken, regional-language decision-support layer on existing government rails**, with a clear owner and a funded distribution channel:

- **Deployment owner / data authority:** **INCOIS** (under MoES) — issues PFZ and Ocean State Forecast, runs Sagar Vani, provides open data; the most natural host. Co-owner: **Department of Fisheries** (owns the fisher relationship, the schemes, and the NFDP registry).
- **Satellite EO + hardware rail:** **ISRO / NRSC / SAC** (Oceansat-3 OCM & SST; NavIC; GAGAN). **IMD** for cyclone/marine weather. **NDMA** (SACHET/CAP alerting) and **Indian Coast Guard** for disaster and safety.
- **Funding & onboarding hooks (policy alignment):**
  - **PMMSY** (Pradhan Mantri Matsya Sampada Yojana) — a **₹20,050 cr** flagship launched in 2020 that explicitly funds fisher safety, communications, and technology.
  - **PM-MKSSY** (2024) — a sub-scheme (on the order of ₹6,000 cr — `[CHECK]` the exact outlay) building the **National Fisheries Digital Platform (NFDP)** and issuing digital IDs to millions of fishers (~40 lakh target — `[CHECK]`). **A voice assistant is a natural front-end for NFDP onboarding and benefit delivery to low-literacy users.**
  - **NavIC messaging transponder programme** (ISRO + DoF, under PMMSY) — rolling out two-way satellite messaging including IMBL alerts to fishing boats (~1 lakh-boat target — `[CHECK]`). **This is the hardware rail ORCA's voice layer can ride offshore.**
  - **Blue Economy policy** and the **Deep Ocean Mission** (a **₹4,077 cr**, 2021–26 programme) — the national "ocean-tech priority" framing.
- **Precedent that this adoption path is real:** INCOIS already acts as a data provider to third-party front-ends (FFMA, mKRISHI); Digital India / Startup India / IN-SPACe signal government openness to external tools built on public data.

**One-line market thesis for the deck:** *"There are ~4 million marine fishermen, a mature national ocean-data and language-AI stack, and tens of thousands of crores in active fisheries schemes (PMMSY + PM-MKSSY ≈ ₹26,000 cr) looking for a last-mile channel — ORCA is that channel."*

---

# Stage 3 — Technical Architecture Blueprint

This stage is written to two audiences at once: a non-specialist teammate should be able to follow *what each piece does and why*, and an implementer (human or Claude Code) should be able to build from it. Where your `README` already specifies a design, this refines and de-risks it rather than reinventing it.

## 3.0 The one thing that will make or break the build: data access reality

Before any architecture, internalize this, because it silently kills marine-data hackathon projects: **the Indian ocean-data sources mostly do NOT expose clean, documented, public REST APIs.** Plan for it now.

- **INCOIS** publishes advisories via web portals and Sagar Vani; some machine-readable endpoints exist, but there is no guaranteed stable, documented public REST API — confirm what's actually live before designing against it (`[POST-2025]`).
- **IMD** output is largely HTML/PDF/GIF charts. The cleanest *machine-readable* warning feed is **CAP (Common Alerting Protocol) XML via NDMA's SACHET**, not a documented IMD REST API.
- **ISRO portals:** **Bhuvan** exposes OGC services (WMS/WFS/WCS) and some APIs — the best programmatic access of the three; **MOSDAC** and **VEDAS** are largely download / registration / visualization with no prominent public bulk API. Ocean data arrives as **NetCDF/HDF5/GeoTIFF**, not JSON. (The current API surface can change — confirm it, `[POST-2025]`.)
- **Copernicus Marine** has the cleanest programmatic access: the `copernicusmarine` Python toolbox (subset/get) over NetCDF, free account required.
- **Bhashini** exposes ASR / TTS / translation via a pipeline API, and the underlying **AI4Bharat models** (IndicTrans2, IndicConformer/IndicWhisper, Indic-TTS) are open, so you can **self-host** to avoid uptime and rate-limit risk. (Confirm the current hosted-API details, `[POST-2025]`.)

**Design consequence:** ORCA's data layer is an **ingestion + normalization tier**, not a set of thin API proxies. For each source you will do one of: (a) call a real endpoint if one exists, (b) parse CAP-XML / scrape-and-parse a portal, or (c) pre-download and cache NetCDF and serve point-queries from your own store. **Wrapping each of these behind a uniform MCP tool interface is exactly why the MCP layer is valuable** — the agents don't care whether the data came from a REST call or a parsed PDF. Build the ingestion adapters first; they are the critical path.

## 3.1 High-level architecture

```
        ┌───────────────────────── ACCESS CHANNELS ─────────────────────────┐
        │   Android app (push-to-talk) │ WhatsApp (voice/text) │ Phone/IVR   │
        └───────────────────────────────┬────────────────────────────────────┘
                                         │  audio / text  + caller geo
                                         ▼
        ┌────────────────────────────────────────────────────────────────────┐
        │  CHANNEL GATEWAY AGENT   — normalizes all channels to one schema;    │
        │  runs Bhashini ASR (speech→text) + language ID; queues TTS on reply  │
        └───────────────────────────────┬────────────────────────────────────┘
                                         │ {text(EN), source_lang, geo, channel}
                                         ▼
        ┌────────────────────────────────────────────────────────────────────┐
        │  ROUTER & PLANNING AGENT — intent classification → task graph;       │
        │  owns shared LangGraph state; decides which specialist agents run    │
        └──┬───────────────┬────────────────┬────────────────┬────────────────┘
           ▼               ▼                ▼                ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │ MARINE DATA  │ │  WEATHER &   │ │ GEOSPATIAL   │ │   OCEAN      │
   │  DISCOVERY   │ │    RISK      │ │  REASONING   │ │  ANALYTICS   │  (v2)
   │ PFZ, SST,    │ │ waves, wind, │ │ distance,    │ │ historical   │
   │ chlorophyll  │ │ cyclone,     │ │ bearing,     │ │ trends       │
   │ (ISRO/INCOIS)│ │ swell (IMD/  │ │ geofence,    │ │ (Copernicus) │
   │              │ │  INCOIS)     │ │ IMBL/MPA     │ │              │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │                │
          │   each reads via MCP TOOLS ─────┴────────────────┘
          │   (INCOIS · IMD/CAP · ISRO/Bhuvan · Copernicus adapters)
          └────────────────────────────┬───────────────────────────────
                                        ▼
        ┌────────────────────────────────────────────────────────────────────┐
        │  GUARDRAIL & CONFIDENCE LAYER — deterministic Python, NOT the LLM:   │
        │  hard-coded safety thresholds · staleness/timestamp checks ·         │
        │  source binding · explicit-failure templates                        │
        └───────────────────────────────┬────────────────────────────────────┘
                                         ▼
        ┌────────────────────────────────────────────────────────────────────┐
        │  SYNTHESIS & VOICE AGENT — composes ONE evidence-cited answer;       │
        │  Bhashini TTS (text→speech) streamed back to the origin channel      │
        └───────────────────────────────┬────────────────────────────────────┘
                                         ▼
                          back to the originating channel

        ┌────────────────────────────────────────────────────────────────────┐
        │  ALERT & NOTIFICATION AGENT (always-on, not query-triggered):        │
        │  watches cyclone cones + swell-surge → WhatsApp/SMS/outbound IVR     │
        └────────────────────────────────────────────────────────────────────┘
```

## 3.2 Component-by-component — what each does and how it works under the hood

### A. Access channels (the three front doors)
- **Android app:** captures push-to-talk audio and streams it over a WebSocket to the backend; also holds the user's GPS. *Under the hood:* raw audio frames → backend → ASR. Simplest to demo reliably.
- **WhatsApp:** via the **Meta WhatsApp Business Cloud API**. Inbound voice notes/text arrive as webhook events; you download the media, run ASR, and reply with a voice/text message. *Under the hood:* webhook → media fetch → ASR → pipeline → TTS audio message back.
- **Phone / IVR:** a real phone number via **Exotel or Twilio Voice** (Exotel is India-focused and a strong choice for the "real Indian number" demo). The telephony provider streams call audio to your backend (media streams), you run ASR, and stream TTS back into the live call. *Under the hood:* PSTN → provider media stream (8 kHz) → ASR → pipeline → TTS → back into call. **This channel has the hardest audio quality (narrowband, noisy) — see risk §3.4.**

### B. Channel Gateway Agent (normalize + speech)
**Job:** turn any channel's input into one uniform object `{text_en, source_lang, geo, channel}` and run speech both ways.
**How it works:** (1) detect language and run **ASR** (speech→text) via Bhashini/AI4Bharat; (2) run **translation** to English so the reasoning core is language-agnostic; (3) resolve location — from app GPS, saved caller-ID profile, or a spoken landmark that the Geospatial agent geocodes. On the way back it invokes **TTS** in the source language. Keeping the reasoning core in English while I/O is multilingual is a deliberate simplification that makes the agents far easier to build and debug.

### C. Router & Planning Agent (the orchestrator)
**Job:** classify the user's intent and build the plan of which specialist agents to run, in what order, with what dependencies.
**How it works:** an LLM call (with a tightly constrained prompt) maps the query to an intent (`pfz_nearest`, `safety_check`, `boundary_check`, `conditions_summary`, …) and emits a **task graph**. This is the documented **"routing" + "orchestrator-workers"** agent pattern — a classifier dispatches to specialists, and a coordinator later synthesizes their outputs. It writes `intent` and `subtasks` into the shared **LangGraph state**; it never calls data tools itself. *Why LangGraph:* it holds one **shared, checkpointed state object** across the whole run, supports **loops** (retry/reflection) not just straight pipelines, and lets you pause/resume and trace every step — which matters enormously for a safety system you must debug.

### D. The four specialist agents (each owns one data domain)
Each agent reads what it needs from state, calls its **MCP tools**, and writes only its own section of state (no agent overwrites another's output). Owning one domain each is what makes every downstream claim **traceable to a source**.

1. **Marine Data Discovery Agent** — *"where are the fish."* Calls the INCOIS PFZ tool (and, for the ISRO-forward pitch, the satellite chlorophyll/SST products behind PFZ) for a bounding box around the user. Returns candidate fishing-zone nodes with lat/lon, depth, and bearing. *Under the hood:* the satellite chain is **SST + ocean-colour/chlorophyll → thermal fronts & productivity gradients → fish aggregation zones**; INCOIS already computes this into PFZ advisories, so you consume the advisory and, for the demo's "ISRO story," visualize the underlying Oceansat-3 chlorophyll layer that produced it.
2. **Weather & Risk Assessment Agent** — *"is it safe."* The **only** agent allowed to raise a safety flag. Pulls significant wave height, wind, cyclone proximity, and swell-surge from IMD (via CAP-XML) and INCOIS Ocean State Forecast / swell advisories. *Under the hood:* it fetches numbers, then hands them to the deterministic guardrail (it does **not** decide "safe" itself with the LLM).
3. **Geospatial Reasoning Agent** — the math. Distance and bearing (Haversine) to the nearest PFZ node; **point-in-polygon geofencing** of the user's position/track against the **IMBL** and Marine Protected Areas, using GeoPandas/Shapely over shapefiles. *Under the hood:* pure deterministic computation — LLMs are unreliable at geospatial math, so this is done in code, not the model. This agent also powers the IMBL boundary alert.
4. **Ocean Analytics Agent (v2 / future scope)** — historical trend questions ("why did productivity drop") from Copernicus reanalysis. Heaviest pipeline, least demo value — deferred, and stated as an *observation from data*, never an invented causal claim.

### E. MCP tool layer (the uniform data interface)
**Job:** expose every data source and every outbound channel as a standard **tool** the agents can call, so the reasoning code never hard-codes an endpoint.
**How it works:** MCP (Model Context Protocol) is an open standard (client–server over JSON-RPC) for exposing **tools/resources** to LLM apps. You write one small **MCP server per source** — `incois_get_pfz`, `imd_get_marine_warnings`, `isro_get_chlorophyll`, `copernicus_subset`, `bhashini_asr`, `bhashini_tts`, `whatsapp_send`, `ivr_speak` — each hiding whatever ugliness (REST call, CAP-XML parse, NetCDF point-query) lives behind it. Benefit: you can add/swap a data source without touching the agents, and each tool has a typed schema the router can discover. *(If MCP overhead is too much for the hackathon window, the fallback is plain typed Python "tool" functions with the same interface — the architecture is identical; MCP just makes it a clean, demoable standard. Decide based on time.)*

### F. Guardrail & Confidence Layer (the part that keeps people alive)
This is your technical signature. It is **deterministic Python, deliberately not the LLM.** Straight from your `README`, and worth keeping verbatim as design law:
1. **No LLM-generated safety thresholds** — e.g. `wave_height_m > 2.5 or wind_speed_kt > 25 → unsafe` is a hard-coded function; the LLM only phrases the verdict, it cannot override it.
2. **Every number carries a timestamp** — a `data_freshness` map records when each source last answered; stale safety data forces an "as of [time]" and a retry.
3. **Retries before guesses** — each tool call: 3 attempts, exponential backoff (1s/2s/4s); 429 → queued retry; 401 → silent token refresh + replay.
4. **Explicit failure over confident silence** — if wave/cyclone data can't be fetched, the reply is a fixed template ("I couldn't get current data; last reading was [time], [value]; don't use it for a decision now"), not free-composed text.
5. **Circuit breaker per upstream** — 5 consecutive failures → stop hammering for 5 min, serve cached data with a staleness warning.
6. **One quote, cross-checked** — historical reads are stated as observations, never invented causation.

*Why this design is correct, in one line for judges:* the LLM is used only to **translate language and narrate retrieved facts**; **retrieval + comparison against thresholds happen in code** — which is the established way to keep safety-critical LLM outputs reliable (retrieval-grounding + deterministic rule layer).

### G. Synthesis & Voice Agent
**Job:** turn the agents' structured outputs into **one** spoken, evidence-cited answer — but only after checking `safety_flags` and `data_freshness`.
**How it works:** it composes a short, plain answer ("nearest zone ~14 km southwest of [landmark], depth ~45 m; conditions clear, no warnings as of this morning's advisory"), then Bhashini **TTS** renders it in the source language, streamed back in overlapping chunks so the user hears speech forming before the full sentence is generated (the main perceived-latency win). The optional **shareable card** (satellite visual + one-line verdict) is sent *after* the voice answer so it never delays a safety-critical response.

### H. Alert & Notification Agent (always-on)
**Job:** proactive push, independent of any user query. A background job watches cyclone cones and swell-surge advisories; when a user's saved location falls inside a threat polygon, it pushes a WhatsApp/SMS/outbound-IVR warning. *Under the hood:* scheduled polling of the alert sources → point-in-polygon against registered user locations → templated multilingual alert out. This is the clearest embodiment of the "Disaster Management" theme.

## 3.3 Recommended tech stack (hackathon-fast, demo-worthy, defensible)

| Layer | Recommendation | Why |
|---|---|---|
| **Orchestration** | **Python + LangGraph** | Stateful multi-agent graph with checkpointing, loops, human-in-loop, tracing (LangSmith). Matches your design exactly. |
| **LLM** | A strong hosted model for the router/synthesis (e.g. GPT-4-class or Claude); keep prompts small and constrained | Reasoning quality for intent + narration; the *numbers* never come from it |
| **Tool interface** | **MCP servers** (Python SDK) per source/channel; fallback = typed Python tool functions | Clean, swappable, demoable; the "agentic" story judges want |
| **Speech & language** | **Bhashini API**, with **self-hosted AI4Bharat models** (IndicTrans2, IndicConformer/IndicWhisper, Indic-TTS) as fallback | 22-language coverage + government alignment; self-host de-risks uptime/rate limits and enables domain fine-tuning |
| **Geospatial** | **GeoPandas + Shapely** (point-in-polygon, IMBL/MPA); **Haversine** for distance/bearing | Deterministic, well-understood, no LLM in the math |
| **Ocean data** | **`copernicusmarine` toolbox** (NetCDF via `xarray`); INCOIS/IMD adapters (REST where available, else CAP-XML parse / cached NetCDF point-query) | Real, free, programmatic; matches the data-access reality of §3.0 |
| **Telephony / channels** | **Exotel** (India) or Twilio for IVR; **Meta WhatsApp Business Cloud API**; a lightweight Android app (Kotlin/Flutter) with push-to-talk over WebSocket | Real Indian dial-in number for the demo; broad reach |
| **Backend / API** | **FastAPI** (async, WebSocket-friendly) | Fast to build, handles streaming audio, Python-native with the rest of the stack |
| **Storage / cache** | **PostgreSQL + PostGIS** (users, saved locations, geofences) + **Redis** (cache advisories, circuit-breaker state, freshness map) | PostGIS for spatial queries; Redis for the staleness/cache/breaker logic |
| **Deploy** | One cloud VM or a managed container; ngrok/Cloudflare tunnel for webhooks during the demo | Keep it trivially reproducible for the 36-hour finale |

## 3.4 The riskiest technical parts — and how to de-risk each *early*

Ranked by "most likely to sink the demo," with a concrete mitigation to do in the **first 24 hours**, not the last.

1. **Data access / ingestion (highest risk).** If you assume clean APIs exist and they don't, you lose days. **De-risk day 1:** for each of the 2 demo query types, get *one* real data path working end-to-end — even if it's a parsed CAP-XML file or a pre-downloaded NetCDF served from your own cache. Freeze a **known-good cached dataset** for the demo so a live outage can't break you (and so you can *deliberately* break it for the guardrail demo).
2. **Numeric / spatiotemporal grounding correctness.** The single biggest *credibility* risk: the LLM must never emit a wave height or coordinate it made up. **De-risk:** enforce it structurally — agents return typed numeric fields; the synthesis prompt is given only those fields and is instructed to narrate, not compute; add a check that every number in the final text exists in the retrieved data. This *is* the guardrail layer — build it early and demo it.
3. **ASR in the field — noise + narrowband phone audio + dialects.** Clean read-speech models degrade badly on wind/engine noise and 8 kHz phone lines, and on coastal dialects/code-mixing. **De-risk:** for the demo, prefer the app/WhatsApp channels (16 kHz, cleaner) for the "wow" queries and use the phone-call channel to *prove the channel works* with a clear speaker; add denoising/VAD + a confirmation prompt ("did you mean…?"); build a small marine-vocabulary lexicon; consider **constrained/keyword-spotting intents** rather than fully open dialogue for v1 (this is also why IVR historically works for rural users).
4. **End-to-end latency.** Many chained steps + live APIs blow past a snappy feel. **De-risk:** cache the daily PFZ/advisory data (the common query becomes a cache hit), run independent agents in parallel, stream TTS in overlapping chunks, and send an instant "let me check…" acknowledgement. Measure and state the real number.
5. **Multi-agent reliability.** Multi-agent systems fail in characteristic ways (miscommunication, premature termination, weak verification) — more agents is not automatically more reliable. **De-risk:** keep roles tightly specified, keep the graph as simple as the two demo intents require, and lean on the *deterministic* guardrail as the backstop rather than trusting agent coordination to be perfect.
6. **Safety liability.** **De-risk:** INCOIS/IMD advisories are the stated source of truth; the LLM is an explainer; every safety answer carries a timestamp + a spoken disclaimer; and you never contradict an official advisory. Say all of this out loud in the pitch.

---

# Stage 4 — Feature & Roadmap Recommendations

The organizing principle: **the MVP must prove the hard, differentiating thing (reliable multi-source reasoning + voice), not the easy, broad thing (many features).** Judges remember one demo that clearly worked over ten features that half-worked.

## 4.1 Must-have (MVP / demo) — build these, nothing else, first

- **Two query intents, done well:** `pfz_nearest` ("where's the nearest fishing zone?") and `safety_check` ("is it safe to go out tomorrow?"). These map to your two hero data paths and cover the "where are the fish / is it safe" core.
- **One reasoning core** (Router + Marine Data + Weather & Risk + Geospatial agents) over **MCP/tool-wrapped data** — with at least one *real* data path per intent, plus a frozen cached dataset as the demo safety net.
- **The deterministic guardrail layer**, fully working and *visible*: hard-coded safety verdict + timestamped numbers + the explicit-failure template. This is the demo's centerpiece.
- **Voice in/out via Bhashini** in **2–3 languages** (e.g., Tamil + Hindi + English), through **one or two channels shown live** — the phone-call/IVR channel is the highest-impact "this is real" moment; WhatsApp is the easiest reliable backup.
- **Location handling** (GPS from app, or a spoken landmark geocoded) sufficient for the demo queries.
- **Evidence-cited answers** — every spoken answer names its source and time ("as of this morning's INCOIS advisory").

## 4.2 Nice-to-have (pitch / roadmap slide) — describe, partially build if time

- **The IMBL boundary alert** (geofence + proactive "turn back" voice) — very strong story; the geospatial machinery is already there. Build a scripted version if you can.
- **Proactive Alert & Notification Agent** for cyclone/swell (the always-on disaster-management path) — at least a scripted trigger.
- **The shareable daily card** (satellite chlorophyll visual + one-line verdict) as the organic-growth mechanic for WhatsApp groups.
- **The satellite EO visual** — show the Oceansat-3 chlorophyll/SST layer behind a PFZ answer, to make the "ISRO data" story tangible on screen.
- **Third channel** and **more languages** wired through the same brain, to prove the "three channels, one brain / scales to 22" claim.

## 4.3 Stretch (future-scope storytelling) — say, don't build

- **True offline mode** (on-device quantized model for geofencing past cellular range).
- **Deep-sea coverage via NavIC/GEMINI integration** (the honest answer to "what about at sea").
- **Multi-turn memory across calls** (personal history, boat profile).
- **Ocean Analytics** (Copernicus historical "why did the fishery decline") — the ecosystem-reasoning frontier.
- **NFDP onboarding front-end** (voice-driven scheme registration for low-literacy users) — the government-adoption vision.

## 4.4 What the live demo must visibly show (≤5 minutes)

Keep your `README`'s three-query script — it is genuinely excellent because each query proves a different hard thing. Refined for maximum judge impact:

1. **"Where's the nearest fishing zone?" over a real phone call to a real number** (not a simulator). Proves the IVR channel, Bhashini speech, and end-to-end latency are real. *Optionally* flash the underlying **ISRO Oceansat-3 chlorophyll layer** on screen as the voice answers — that's the "satellite EO → spoken answer" money shot for ISRO judges.
2. **A cyclone/high-wave safety query (WhatsApp voice note) with the hard threshold deliberately tripped** (query a coordinate inside a live or simulated cyclone cone). Shows the guardrail forcing a red-alert answer the LLM *cannot* soften. This is the disaster-management theme, live.
3. **Kill the data source mid-demo** (block the endpoint) and re-ask the PFZ question. The system says *"I couldn't get current data — here's the last reading from [time] — don't rely on it for a decision now"* instead of inventing coordinates. **This is the single moment that separates ORCA from every other chatbot in the room** — rehearse it, and call out explicitly to the judges what just happened and why it matters for a tool that can get someone killed.

**Demo staging tips:** pre-warm caches; have the frozen dataset ready; script the exact spoken phrases in a clean voice for the noisy channels; keep a recorded video fallback in case the venue network fails; and end on the impact slide (Ockhi + ~4M fishermen + the deployment path) so the last thing judges hear is *why it matters and that it has a future*.

---

# Appendix A — How SIH is judged, and how ORCA maps to it

> **Note:** the dimensions below are the long-standing SIH evaluation criteria and are safe to build a pitch around. The *exact* current-year rubric and finale format can shift year to year — confirm them on **sih.gov.in** (`[POST-2025]`). For precedent, search `sih.gov.in` and news for "INCOIS", "MoES", "ISRO", "ocean", "fishermen", "PFZ" across past SIH editions to find and cite specific ocean/marine problem statements and winning teams.

**Typical SIH evaluation dimensions** (and where ORCA is strong / needs care):

| Dimension | ORCA's standing | What to emphasize |
|---|---|---|
| **Novelty / innovation** | Medium-high (systems novelty, not new model) | The integration + deterministic safety grounding; be honest, don't oversell |
| **Technical feasibility / complexity** | High if scoped | Show the working guardrail + one real data path; multi-agent + MCP demonstrates depth |
| **Practicality / implementability** | High | Rides on existing government rails; real dial-in number in the demo |
| **Potential impact / usefulness** | Very high | ~4M fishers, life-safety (Ockhi), IMBL detentions, livelihood |
| **Scalability / sustainability** | High | Bhashini + INCOIS + NavIC + NFDP; low marginal cost; clear owner |
| **User experience** | High (voice-first, no literacy needed) | Demo in regional language over a phone call |
| **Presentation / clarity** | Your job on the day | Lead with the story, prove the hard thing, end on impact |

**What ISRO / space-tech judges tend to reward** (a general pattern, not a published rule): genuine use of **ISRO data** (Bhuvan/MOSDAC/Oceansat), indigenous tech, and a realistic path to deployment with a government partner. All three are natural strengths here if you foreground them.

---

# Appendix B — Sources & the short list to confirm

> **How to use this appendix:** these are the primary sources behind the facts in the document, grouped by topic. Most are well-established and are stated plainly in the body; a quick pass on the flagged items — `[CHECK]` (confirm an exact figure/date/ID) and `[POST-2025]` (may have moved since my knowledge horizon) — makes every number slide-ready. Each item names the source to open.

### B.1 Impact & market figures (the ones that land on slides)
1. **Marine fisherfolk ≈ 4 million; ~864,550 families; ~3,288 villages; ~1,511 landing centres** — CMFRI Marine Fisheries Census (`[CHECK]` exact counts; the census is 15+ yrs old and a newer round may exist — `[POST-2025]`). — http://www.cmfri.org.in/marine-fisheries-census
2. **Literacy in fishing communities ≈ 58%** — CMFRI (`[CHECK]` the exact percentage). The core "why voice" stat.
3. **Coastline 7,516.6 km** (standard figure); a **2023–24 remapping revised the national coastline upward (~11,098 km reported)** — `[CHECK]` the current official number. — Department of Fisheries / Survey of India.
4. **India = 2nd-largest fish producer (~8% global); seafood exports on the order of ₹60,000 cr / ~US$7+ bn in a recent year** — `[CHECK]` the exact FY figure. — MPEDA / DoF Handbook on Fisheries Statistics — https://mpeda.gov.in , https://dof.gov.in
5. **Cyclone Ockhi (2017): 245+ deaths, hundreds of fishermen missing; warning-dissemination criticism** — `[CHECK]` the exact toll. — NDMA/IMD reports + press archives.
6. **India–Sri Lanka IMBL detentions, with a sharp 2024 spike** — `[CHECK]` the exact count for the year. — MEA / Parliament Q&A (sansad.in) / The Hindu.
7. **PMMSY: ₹20,050 cr, launched 2020** — https://pmmsy.dof.gov.in ; **PM-MKSSY (2024): ~₹6,000 cr, NFDP, ~40 lakh digital IDs** (`[CHECK]` exact outlay & target) — PIB/DoF.
8. **NavIC messaging transponder programme (~1 lakh-boat target)** and **GEMINI (~300 km offshore)** — `[CHECK]` the target number and unit cost. — ISRO / INCOIS / PIB.
9. **Deep Ocean Mission: ₹4,077 cr, 2021–26** — MoES. **Blue economy ≈ 4% of GDP** (`[CHECK]`) — NITI Aayog.

### B.2 Data-source & satellite facts (established; confirm the flagged specifics)
10. **Oceansat-3 / EOS-06 launched 26 Nov 2022 on PSLV-C54; carries the Ocean Colour Monitor (chlorophyll), a sea-surface-temperature monitor, and a Ku-band scatterometer** (`[CHECK]` the exact payload spec list). — https://www.isro.gov.in , https://www.eoportal.org/satellite-missions/oceansat-3
11. **PFZ generation = satellite SST + chlorophyll → thermal fronts / productivity gradients** (established mechanism); confirm current dissemination channels/languages/cadence (`[POST-2025]`). — https://incois.gov.in
12. **INCOIS Sagar Vani (2017), Ocean State Forecast, SIVAS/swell advisories, tsunami warning; GEMINI device** — confirm current feature/channel details (`[POST-2025]`). — https://incois.gov.in , https://sagarvani.incois.gov.in
13. **ISRO portals: Bhuvan (OGC WMS/WFS/WCS + APIs, best programmatic access); MOSDAC & VEDAS largely download/visualization** — confirm current API availability, since it drives your ingestion design (`[POST-2025]`). — https://bhuvan.nrsc.gov.in , https://www.mosdac.gov.in , https://vedas.sac.gov.in
14. **IMD: limited public REST API; cleanest machine-readable warnings = CAP-XML via NDMA SACHET** — confirm current endpoints (`[POST-2025]`). — https://mausam.imd.gov.in , https://sachet.ndma.gov.in
15. **Copernicus Marine: `copernicusmarine` toolbox, NetCDF, free account; global grids cover Indian seas, with no dedicated Indian-Ocean regional model** (`[CHECK]` exact product resolutions). — https://marine.copernicus.eu , https://pypi.org/project/copernicusmarine/
16. **Bhashini/ULCA: translation covers the 22 scheduled languages (IndicTrans2); ASR/TTS cover fewer and vary; access via pipeline API; AI4Bharat models open for self-hosting** (`[CHECK]` current per-service language counts). — https://bhashini.gov.in , https://ai4bharat.iitm.ac.in , https://github.com/AI4Bharat

### B.3 Technical / method references (established; `[CHECK]` the exact arXiv IDs before citing in a paper)
17. **LangGraph** (stateful multi-agent orchestration) — https://langchain-ai.github.io/langgraph/
18. **Anthropic, "Building Effective Agents" (Dec 2024)** — routing + orchestrator-workers patterns — https://www.anthropic.com/engineering/building-effective-agents
19. **Model Context Protocol** (open tool/data standard, JSON-RPC) — https://modelcontextprotocol.io/introduction , https://www.anthropic.com/news/model-context-protocol
20. **ReAct** (reason+act tool use), Yao et al., ICLR 2023 — https://arxiv.org/abs/2210.03629
21. **RAG** (retrieval-grounded generation), Lewis et al., NeurIPS 2020 — https://arxiv.org/abs/2005.11401
22. **Chain-of-Verification** (Dhuliawala et al. 2023) — arXiv 2309.11495 ; **Self-RAG** (Asai et al. 2024) — arXiv 2310.11511 (`[CHECK]` IDs).
23. **NeMo Guardrails** (programmable rule rails over LLMs) — arXiv 2310.10501 (`[CHECK]` ID) — https://github.com/NVIDIA/NeMo-Guardrails
24. **"Why Do Multi-Agent LLM Systems Fail?" (MAST taxonomy, 2025)** — the failure modes cited in your risk section — arXiv 2503.13657 (`[CHECK]` ID).
25. **EO/geospatial LLM prior art** (position your novelty against these): GeoChat (CVPR 2024, arXiv 2311.15826), "Remote Sensing ChatGPT" (arXiv 2401.09083), Autonomous GIS (arXiv 2305.06453), NASA/IBM Prithvi, Clay, EU Digital Twin of the Ocean, Google Flood Hub (Nature 2024) — `[CHECK]` IDs/dates.
26. **Voice-for-low-literacy evidence:** Medhi et al., "Text-Free UIs" (ICTD 2006); Patel et al., "Avaaj Otalo" (CHI 2010); Gram Vaani / Mobile Vaani (deployed IVR at scale) — `[CHECK]` exact URLs/DOIs.

### B.4 Competitors (profiles per Stage 2)
27. **FFMA** — MSSRF + Qualcomm Wireless Reach + TCS — https://www.mssrf.org
28. **mKRISHI Fisheries** — TCS — https://www.tcs.com
29. **INCOIS Sagar Vani** — https://sagarvani.incois.gov.in
30. **GEMINI / NavIC / Nabhmitra** — ISRO/INCOIS — https://www.isro.gov.in
31. **Kadal Osai 90.4 FM** (Rameswaram community radio); **ABALOBI** — https://abalobi.org ; **Global Fishing Watch** — https://globalfishingwatch.org ; **Windy** — https://www.windy.com ; **mFisheries (UWI)** — search "mFisheries UWI".
32. **Confirm before citing (`[POST-2025]` / unverified):** any 2025–26 INCOIS/MoES/Bhashini conversational or voice fisher assistant (the only plausible direct competitor); the reported "Numa Fisheries" and a "Wesee" fisher wearable, which I can't confirm exist; and exact FFMA/Sagar Vani download & language counts (`[CHECK]`).

---

# Appendix C — Ready-to-paste Claude Code kickoff prompt

Paste this (with the full blueprint attached) into Claude Code to start building the MVP:

```
You are building the MVP for "ORCA — Marine EcOsystem Reasoning with Collaborative Agents"
(SIH 2026, ISRO PS 26176). Read the attached blueprint (ORCA_SIH_Blueprint.md) in full first.

Build scope for THIS iteration (MVP only — see Stage 4.1):
- Python + FastAPI backend, LangGraph orchestration.
- Two intents: pfz_nearest and safety_check.
- Agents: Router/Planning, Marine Data Discovery, Weather & Risk, Geospatial Reasoning,
  Guardrail/Confidence (deterministic Python), Synthesis.
- Wrap data sources and channels as MCP tools (or typed Python tool functions if faster):
  incois_get_pfz, imd_get_marine_warnings (CAP-XML parse), isro_get_chlorophyll,
  bhashini_asr, bhashini_tts. Include a FROZEN cached dataset per intent as a demo fallback.
- Guardrail layer FIRST and VISIBLE: hard-coded safety thresholds (wave_height_m > 2.5 or
  wind_speed_kt > 25 -> unsafe), per-source data_freshness timestamps, 3-retry+backoff,
  circuit breaker, and the explicit-failure template. The LLM never emits a number it didn't
  receive; add a check that every number in the final text exists in retrieved data.
- Geospatial: Haversine for nearest-PFZ; GeoPandas/Shapely point-in-polygon for IMBL geofence.
- Voice: Bhashini ASR->EN reasoning core->Bhashini TTS, in Tamil + Hindi + English.
- One channel end-to-end first (WhatsApp Cloud API OR Exotel/Twilio IVR), app optional.
- Storage: PostgreSQL+PostGIS (users, saved locations, geofences) + Redis (cache, freshness,
  breaker state).

Priorities & constraints:
1. Get ONE real data path per intent working end-to-end before adding breadth.
2. Build and demo the guardrail behavior (including the "data source killed -> explicit
   failure, no hallucinated coordinates" path) — this is the project's signature.
3. Keep the LLM to intent-classification and narration only; all numbers/geo-math in code.
4. Stream TTS in overlapping chunks; cache daily advisories; send an instant acknowledgement.
Start by scaffolding the repo (per the blueprint's repository layout), the LangGraph state
object, and the guardrail module, then wire one intent through to voice.
```

---

*End of blueprint. Everything here is ready to build and pitch from; the only pre-presentation homework is a quick pass over the `[CHECK]` figures/IDs and `[POST-2025]` items in Appendix B against the listed primary sources.*



