"""Memory hooks: what is remembered, and what the platform does with it.

The platform owns storage, scoping, idempotency and the outbox (invariant I7).
This file declares a category and turns rows into the handful of facts the rules
need. It writes no scoping logic of its own — scoping is where a mistake means
one driver reading another's history.

`BA-24` is why memory is anchored to the **profile** and not the vehicle: two
people sharing a car have opposite habits, and applying one person's habits to
the other is the least forgivable kind of wrong.

`DEBT-020`: this file used to compute `armed`/`cooldown_active`/
`consecutive_rejections` from remembered rows — a re-arm hysteresis and a
cooldown that `BR-10`/`QC-28.1` forbid. Plan P28 wires the real S7 Shared
Memory gate (duplicate Candidate) through `handlers.py`'s `_facts_from`
instead — the row-shaped seam this file used to keep for that (`MemoryRow`,
`facts_from_rows`) is gone with it, not kept red.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pa.kernel.candidates.outcomes import FinalState

__all__ = [
    "CATEGORY",
    "RecordKind",
    "final_state_of_record",
    "recommendation_state_read_projection",
    "transitions",
]

#: Declared in `spec.py`; the platform stores under it and recalls by it.
CATEGORY = "battery_status"


class RecordKind:
    """The five things worth remembering, kept distinct on purpose.

    `AC-14` rests on the difference between `REJECTED` and `NO_ANSWER`: a
    driver watching the road who said nothing has not refused anything.

    `SNOOZED` is the fifth, added at P39. `AC-14` lists it beside the other two
    — *"ghi nhận rejected/snoozed/ignored tuỳ trường hợp"* — and `BR-10` gives
    the two different consequences: a refusal carries the full cooldown, a
    postponement does not. Collapsing them means a driver who says *"để sau"* is
    treated as having said *"không"*.
    """

    SPOKE = "spoke"
    REJECTED = "rejected"
    SNOOZED = "snoozed"
    NO_ANSWER = "no_answer"
    ACCEPTED = "accepted"


#: This feature's four words, in the platform's eight (ADR-0020, quyết định 4).
#:
#: The mapping lives here rather than in `pa.kernel` because only this feature
#: knows what its own words mean. What the platform requires is that the
#: mapping be **total**; a test in this package asserts it, and that test goes
#: red when somebody adds a fifth `RecordKind` without deciding how it ends.
_ENDING_OF: dict[str, FinalState] = {
    RecordKind.SPOKE: FinalState.IGNORED,
    RecordKind.REJECTED: FinalState.REJECTED,
    #: **Không gộp vào `REJECTED`.** `FinalState.SNOOZED` đã có tên trong nền
    #: tảng từ đầu và cho tới P39 không đường nào sinh ra nó — nên *"để sau"* đi
    #: vào hệ thống dưới dạng một lời từ chối.
    RecordKind.SNOOZED: FinalState.SNOOZED,
    RecordKind.NO_ANSWER: FinalState.IGNORED,
    RecordKind.ACCEPTED: FinalState.ACTED,
}


def final_state_of_record(kind: str) -> FinalState:
    """One remembered row, as one of the platform's eight endings.

    `SPOKE` and `NO_ANSWER` both land on `IGNORED`, and that is not a collapse:
    `SPOKE` is what this feature writes the instant it speaks, before anyone has
    answered, so the ending it implies *so far* is the one where nobody did.
    A later row overwrites it.
    """
    try:
        return _ENDING_OF[kind]
    except KeyError:
        raise ValueError(f"RecordKind chưa có kết cục tương ứng: {kind!r}") from None


def transitions(payload: dict[str, Any]) -> dict[str, Any]:
    """Hook the platform calls when a recommendation changes state.

    Returns what to remember. The platform owns *how* it is stored, *where* it
    is scoped and *whether* it is a duplicate — this only says what happened.

    `AC-16`'s audit fields (SoC, drive-mode, Vehicle/Assistant/Audio State)
    never arrive in `payload` from the driver's own answer — a "yes" carries no
    battery reading. `priorContext` is how the route hands them over: it is
    `service.audit_context()`'s output, stamped into the Candidate's `evidence`
    back at `/evaluate` time and read back by the route just before this call.
    """
    outcome = str(payload.get("outcome", ""))
    kind = {
        "accept": RecordKind.ACCEPTED,
        "reject": RecordKind.REJECTED,
        "snooze": RecordKind.SNOOZED,
        "timeout": RecordKind.NO_ANSWER,
    }.get(outcome, RecordKind.SPOKE)
    context = payload.get("priorContext") or {}
    return {
        "category": CATEGORY,
        "kind": kind,
        "candidateId": payload.get("contextKey", ""),
        "socPct": context.get("socPct"),
        "driveMode": context.get("driveMode"),
        "vehicleState": context.get("vehicleState"),
        "assistantMode": context.get("assistantMode"),
        "audioState": context.get("audioState"),
        "channel": payload.get("channel", "none"),
        "finalState": final_state_of_record(kind).value,
        "reasonCode": payload.get("reasonCode") or "",
        "stage": "action",
    }


def recommendation_state_read_projection(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Hook the platform calls to read this feature's remembered state back."""
    return {
        "category": CATEGORY,
        "count": len(rows),
        "lastKind": rows[-1].get("kind") if rows else None,
    }
