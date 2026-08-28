"""Fixed, deterministic response templates used for safety and explicit failure."""

TEMPLATES = {
    "danger_high_wave": (
        "Do not go out. Wave height is {value} m ({caption}), " "above the safe limit of {limit} m."
    ),
    "danger_high_wind": (
        "Do not go out. Wind is {value} kt ({caption}), " "above the safe limit of {limit} kt."
    ),
    "danger_cyclone": (
        "Do not go out. A cyclone is {value} km away ({caption}). "
        "Stay ashore and follow local warnings."
    ),
    "warn_swell": (
        "Caution: swell surge is {value} m ({caption}). " "Small boats should avoid going out."
    ),
    "all_clear": (
        "Conditions look safe right now: waves {wave} m, "
        "wind {wind} kt ({caption}). Always stay alert."
    ),
    "data_unavailable": (
        "I can't get current {what} data right now. "
        "I won't guess about your safety. "
        "{last_known}"
        "Please try again shortly or follow local warnings."
    ),
    "last_known_clause": (
        "My last reading was {value} {unit} ({caption}), which may be out of date — "
    ),
    "data_stale": (
        "Warning: my most recent {what} reading is from {caption}, "
        "which may be out of date. Do not rely on it — check local "
        "sources before going out."
    ),
    "partial_data": (
        "I could get {have} but not {missing}. Based only on what I have: "
        "{summary}. Treat this as incomplete."
    ),
    "location_unknown": (
        "I need your location to answer that. Please share it or tell me your " "landing centre."
    ),
}
