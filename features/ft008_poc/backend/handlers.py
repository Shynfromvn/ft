"""Entry points the platform calls. Thin, `async`, and free of FastAPI.

A handler resolves what it needs, calls the rules, and returns a dict. No
business rule lives here — that is `service.py` — and no HTTP type appears,
which is what lets the same logic be driven from a scenario runner, a test
harness or a queue consumer without change.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from features.ft007_battery_status_recommendation.backend import service
from features.ft007_battery_status_recommendation.backend.rules import SilenceReason
from features.ft007_battery_status_recommendation.backend.schemas import (
    EvaluateRequest,
    RespondRequest,
)
from pa.kernel.core.clock import Clock, SystemClock
from pa.kernel.core.errors import ValidationFailed

__all__ = ["evaluate", "respond"]

#: The platform's three `assemble()` failure reasons (ADR-0030, P28), mapped to
#: this feature's own `E02` vocabulary. `handlers.py` does this translation —
#: not the route — because the route stays feature-agnostic (it only forwards
#: a `Mapping`) and only a feature may name its own reason codes.
_MEMORY_FAILURE_REASON: dict[str, SilenceReason] = {
    "timeout": SilenceReason.MEMORY_TIMEOUT,
    "absent": SilenceReason.MEMORY_INCONSISTENT,
    "error": SilenceReason.MEMORY_UNAVAILABLE,
    "expired": SilenceReason.MEMORY_EXPIRED,
}


def _facts_from(memory: Mapping[str, Any]) -> service.MemoryFacts:
    failure = memory.get("error")
    if failure is not None:
        return service.MemoryFacts(
            available=False,
            error_reason=_MEMORY_FAILURE_REASON.get(
                str(failure), SilenceReason.MEMORY_UNAVAILABLE
            ),
        )
    return service.MemoryFacts(duplicate_candidate=bool(memory.get("duplicateCandidate")))


async def evaluate(
    request: EvaluateRequest,
    memory: Mapping[str, Any] | None = None,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Decide whether to say anything, and what.

    `memory` is the platform's S7 Shared Memory snapshot for this driver
    (`ba.md` Bước 3, ADR-0030) — or `{"error": "timeout" | "absent" | "error"}`
    when the platform could not assemble one. The REST route
    (`pa.entrypoints.recommendation_app`) always passes a real one. `None`
    reads as "available, nothing duplicate" (`_facts_from`'s default) — the
    trigger/bus path (`pa.recommendation.judgement.JudgementStage`) calls every
    feature's handler with one argument and does not know this feature's Shared
    Memory vocabulary; wiring that path through S7 is out of scope here (plan
    P28's "Not in scope" — it is the S6/bus distribution path QC does not test
    directly).

    `clock` is an argument with a default rather than a module global, so a
    test drives a scenario without waiting and without patching.
    """
    resolved_clock = clock or SystemClock()
    facts = _facts_from(memory or {})
    decision = service.evaluate(request, clock=resolved_clock, facts=facts)
    result = service.public_result(decision)
    # `AC-16`'s audit trail — not in `feature.yaml`'s `publicResult.allowedFields`,
    # so it never reaches the driver-facing response, only the Candidate's own
    # `evidence` (the route reads it from here, see `evaluate/__init__.py`).
    result["context"] = service.audit_context(request)
    return result


async def respond(
    request: RespondRequest,
    *,
    clock: Clock | None = None,
    mode_changed: bool | None = None,
) -> dict[str, Any]:
    """Record the driver's answer and say the matching thing.

    `mode_changed` carries `BA-09`: the caller has read the drive mode back from
    the vehicle. Without it this function cannot claim success, which is the
    point — claiming a change that did not happen costs trust in the whole
    assistant rather than in this feature.

    Reads `request.mode_changed` when the caller does not pass one explicitly —
    that field is what lets the REST route (which only ever calls this with the
    request it received) carry a real ECU confirmation at all. The keyword stays
    for a caller that determines it out of band (a scenario runner simulating
    hardware separately from the request body).
    """
    if not request.candidate_id:
        raise ValidationFailed("candidateId is required to record a response")
    resolved_mode_changed = request.mode_changed if mode_changed is None else mode_changed
    decision = service.respond(
        request, clock=clock or SystemClock(), mode_changed=resolved_mode_changed
    )
    return service.public_result(decision)
