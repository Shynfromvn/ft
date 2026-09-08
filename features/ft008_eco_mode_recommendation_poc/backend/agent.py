"""The adapter: turns a platform snapshot into this feature's own request shape.

`feature.yaml`'s `agent.adapter` names this class — the platform checks the
symbol resolves (`test_contract.py`) — so the class stays even though nothing in
this feature's own runtime path constructs it today; `handlers.py` calls
`project_runtime` directly for the REST path, and this remains the shape a
future caller (a scenario runner, the bus path) would build a request through.
"""

from __future__ import annotations

from typing import Any

from features.ft008_eco_mode_recommendation_poc.backend.runtime import project_runtime
from features.ft008_eco_mode_recommendation_poc.backend.schemas import (
    EvaluateRequest,
    RuleOverrides,
)
from pa.kernel.telemetry.contracts import StateView

__all__ = ["EcoModeRecommendationPocAdapter"]


class EcoModeRecommendationPocAdapter:
    """Builds the evaluation request from a platform snapshot.

    Deterministic by construction: the same snapshot produces the same request,
    every time.
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
            # That is what lets a scenario run against a lower threshold or a
            # tighter freshness ceiling without editing the constants.
            #
            # Đi qua `model_validate`, KHÔNG qua `model_copy(update=...)`.
            # `model_copy` không chạy validator, nên biên khai trong
            # `RuleOverrides` bị bỏ qua và một override ngoài dải đi thẳng vào
            # request. Đó khác hẳn điều docstring của `RuleOverrides` hứa —
            # *"Values outside a bound are rejected, never silently clamped"* —
            # và cái nó bỏ lọt đúng là hướng nguy hiểm: biên ở đó chỉ mở về
            # phía yên lặng hơn, nên thứ lọt qua là một override khiến tính
            # năng nói dễ dãi hơn mức brief cho phép.
            #
            # `ft007_battery_status_recommendation` dùng `model_copy` ở chỗ
            # này. Lỗ ấy hiện chưa ai chạm tới vì không đường nào dựng adapter,
            # nhưng nó là một lỗ — đáng báo lại cho gói kia.
            merged = request.rule_overrides.model_dump() | overrides
            request = request.model_copy(
                update={"rule_overrides": RuleOverrides.model_validate(merged)}
            )
        return request