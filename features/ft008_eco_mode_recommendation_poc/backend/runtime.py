"""Projecting the normalised vehicle state into this feature's request.

A **pure projection**: no I/O, and no value invented on the way through. A
domain the vehicle has not reported arrives as `None`, and becomes an explicit
"unreliable" flag rather than a guessed number — `service.py` then refuses to
recommend on it, which is the correct outcome. Guessing would mean the assistant
recommending confidently on a number nobody supplied.

The domains this reads are declared in `feature.yaml`. Declaring them is also a
privacy statement: what this feature did not ask for, it does not receive. Two
domains here where `ft007_battery_status_recommendation` has seven —
`navigation`, `interaction`, `phone`, `safety` and `vehicleHealth` fed gates
this brief's §Phạm vi puts out of scope, so this feature never sees them.
"""

from __future__ import annotations

from features.ft008_eco_mode_recommendation_poc.backend.schemas import (
    BatteryState,
    ConnectivityState,
    EvaluateRequest,
    Settings,
    VehicleState,
)
from pa.kernel.telemetry.contracts import StateView

__all__ = ["project_runtime"]

#: What `socPct` reads as when the vehicle has not reported `motion` at all.
#: Paired with `batteryStateReliable: false`, so nothing acts on it. Zero rather
#: than a full battery on purpose: if some path ever does read it without
#: checking the flag, being wrongly alarmed is recoverable and being wrongly
#: reassured is not.
_NO_READING_SOC = 0.0


def project_runtime(
    view: StateView, *, profile_id: str = "guest", woken_by: str = ""
) -> EvaluateRequest:
    """Build an `EvaluateRequest` from the domains this feature may see.

    Each `*_reliable` flag is set from whether the domain actually arrived, not
    from a default. That is what makes "we did not receive a battery reading"
    and "the battery is full" two different situations, which
    `Preconditions §2`'s freshness check depends on.

    `woken_by` là **nhận rồi bỏ**, và chữ ký giữ nó vì nền tảng gọi mọi phép
    chiếu bằng cùng một bộ tham số — bỏ đi thì chỗ vỡ chuyển từ đây sang bên
    gọi. Gói gốc chở giá trị ấy vào `EvaluateRequest` vì `ba.md` của nó khai
    hai vế Trigger nối bằng *HOẶC*, nên mã lý do phải đọc từ cột mốc đã đánh
    thức thay vì suy lại từ trạng thái. Brief này có đúng một vế — `SoC ≤ 20%`
    — nên chỉ có một cột mốc, và một trường luôn mang cùng một giá trị không
    phân biệt được điều gì. Cùng lối xử lý `clock` trong `service.evaluate`.
    """
    del woken_by

    motion = view.motion
    connectivity = view.connectivity

    return EvaluateRequest(
        profile_id=profile_id,
        battery_state=BatteryState(
            soc_pct=motion.soc_pct if motion is not None else _NO_READING_SOC,
            data_age_seconds=motion.soc_data_age_seconds if motion is not None else 0.0,
        ),
        vehicle_state=VehicleState(
            drive_mode=motion.drive_mode.value if motion is not None else "UNKNOWN",
        ),
        # `ba.md` `Preconditions §2`: "Kết nối mạng: Online". Xe chưa từng báo
        # miền này thì đọc là offline — cùng lối fail-closed với mọi chỗ khác
        # ở đây: một điều kiện chưa được xác lập thì coi như chưa đạt.
        connectivity_state=ConnectivityState(
            online=connectivity.online if connectivity is not None else False,
        ),
        settings=Settings(
            # Độ tin cậy suy từ việc miền có tới hay không — fail-closed.
            # Cả hai cùng đọc `motion`: `socPct` và `driveMode` sống chung một
            # miền, nên chúng vắng mặt cùng nhau hoặc có mặt cùng nhau.
            battery_state_reliable=motion is not None,
            vehicle_state_reliable=motion is not None,
        ),
    )