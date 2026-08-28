#!/usr/bin/env python3
"""Scripted three-moment demo from docs/07-testing-and-demo.md."""

from __future__ import annotations

from orca.graph import run_query
from orca.guardrails.resilience import reset_breaker, reset_last_ok


def _print(title: str, state: dict) -> None:
    print("=" * 72)
    print(title)
    print(f"intent={state.get('intent')}  guardrail={state.get('guardrail_status')}")
    print(state.get("final_response_text"))
    cites = state.get("citations") or []
    if cites:
        print("citations:")
        for cite in cites[:4]:
            print(f"  - {cite}")


def main() -> None:
    """Run the three demo moments on fixture data."""
    reset_breaker()
    reset_last_ok()

    moment1 = run_query("Where is the nearest fishing zone?", cell_id="calm")
    _print("Moment 1 — nearest fishing zone (calm cell)", moment1)

    moment2 = run_query("Is it safe to go out tomorrow morning?", cell_id="cyclone")
    _print("Moment 2 — safety check (cyclone cell, hard no-go)", moment2)

    moment3 = run_query(
        "Is it safe to go out tomorrow morning?",
        cell_id="cyclone",
        force_error_sources=["imd_marine"],
    )
    _print("Moment 3 — weather source killed (explicit failure)", moment3)


if __name__ == "__main__":
    main()
