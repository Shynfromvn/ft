"""The adapter: turns a platform snapshot into this feature's own request shape.

This is where that one lookup lives, and that placement is the reason
`service.py` can be pure. `feature.yaml`'s `agent.adapter` names this class —
the platform checks the symbol resolves (`test_contract.py`) — so the class
stays even though nothing in this feature's own runtime path constructs it
today; `handlers.py` calls `project_runtime` directly for the REST path, and
this remains the shape a future caller (a scenario runner, the bus path) would
build a request through.

`DEBT-020`/plan P28: this used to also carry a `MemoryReader` and
`resolve_facts()`, the one place `service.py`'s `MemoryFacts` were resolved
from the database. That lookup never had a real caller — `handlers.evaluate()`
always ran it against `_NoMemory()` — and P28 moved the real lookup to
`handlers.py`, where the platform's S7 Shared Memory snapshot actually arrives
from the route. Removed with the dead code, not kept red.
"""

from __future__ import annotations

from typing import Any

from features.ft007_battery_status_recommendation.backend.runtime import project_runtime
from features.ft007_battery_status_recommendation.backend.schemas import EvaluateRequest
from pa.kernel.telemetry.contracts import StateView

__all__ = ["BatteryStatusRecommendationAdapter"]


class BatteryStatusRecommendationAdapter:
    """Builds the evaluation request from a platform snapshot.

    Deterministic by construction: the same snapshot produces the same
    request, every time.
    """

    def build_request(
        self,
        *,
        snapshot: StateView,
        profile_id: str,
        overrides: dict[str, Any] | None = None,
    ) -> EvaluateRequest:
        request = project_runtime(snapshot, profile_id=profile_id)
        if overrides:
            # An explicit override wins over what the platform would supply.
            # That is what lets a scenario set up "already in cooldown" without
            # replaying five minutes of it.
            request = request.model_copy(
                update={"rule_overrides": request.rule_overrides.model_copy(update=overrides)}
            )
        return request
