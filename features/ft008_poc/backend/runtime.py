"""Projecting the normalised vehicle state into this feature's request.

A **pure projection**: no I/O, and no value invented on the way through. A
domain the vehicle has not reported arrives as `None`, and becomes an explicit
"unreliable" flag rather than a guessed number — `service.py` then refuses to
speak on it, which is the correct outcome. Guessing would mean the assistant
speaking confidently on a number nobody supplied.

Until P12 T6 that was a claim rather than a fact. The projection took a
`dict[str, Any]` and dug through it with `.get(name, default)`, against a
snapshot where every domain is populated by default — so all four `*_reliable`
flags were constants, always `True`, and `service.py`'s data/navigation checks
could never fire
([C022](../../../docs/devlog/sprint-04-goi-tinh-nang-tu-chua/log.md)). The
platform now hands over a typed `StateView`.

The domains this reads are declared in `spec.py`. Declaring them is also a
privacy statement: what this feature did not ask for, it does not receive.
"""

from __future__ import annotations

from features.ft007_battery_status_recommendation.backend.schemas import (
    BatteryState,
    ConnectivityState,
    EvaluateRequest,
    InteractionState,
    NavigationState,
    SafetyState,
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
    from a default. That is what makes "we did not receive navigation data" and
    "the destination is far away" two different situations, which `E03`'s
    fail-closed check depends on.
    """
    motion = view.motion
    navigation = view.navigation
    interaction = view.interaction
    phone = view.phone
    connectivity = view.connectivity
    vehicle_health = view.vehicle_health
    safety = view.safety

    return EvaluateRequest(
        profile_id=profile_id,
        # Chở thẳng, không diễn giải: ý nghĩa của chuỗi này là việc của
        # `service.evaluate`, không của phép chiếu (ADR-0075).
        woken_by=woken_by,
        battery_state=BatteryState(
            soc_pct=motion.soc_pct if motion is not None else _NO_READING_SOC,
            data_age_seconds=motion.soc_data_age_seconds if motion is not None else 0.0,
        ),
        vehicle_state=VehicleState(
            vehicle_in_drive=motion.vehicle_in_drive if motion is not None else False,
            gear_state=motion.gear_state.value if motion is not None else "UNKNOWN",
            drive_mode=motion.drive_mode.value if motion is not None else "UNKNOWN",
            system_state=(
                vehicle_health.system_state if vehicle_health is not None else "UNKNOWN"
            ),
        ),
        navigation_state=NavigationState(
            active=navigation.active if navigation is not None else False,
            distance_to_destination_km=(
                navigation.distance_to_destination_km if navigation is not None else None
            ),
            # Hai trường này về lại `view.navigation` cùng ADR-0061 điều 2. Lập
            # luận cũ — *"xe không biết nơi ấy là nhà ai"* — bị chính team sở
            # hữu S6 bác: bộ Navigation nằm trên xe. Cái đổi ở đây là **một
            # đường đọc thay vì hai**; giá trị và ngữ nghĩa `None` giữ nguyên,
            # nên `E03` vẫn fail-closed đúng như trước.
            nearest_charger_km=(navigation.nearest_charger_km if navigation is not None else None),
            destination_type=(
                navigation.destination_type if navigation is not None else "UNKNOWN"
            ),
            # A day old, when nothing arrived. `E03` reads a stale navigation
            # context as one it may not act on, which is the right answer for a
            # context that does not exist.
            data_age_seconds=(navigation.data_age_seconds if navigation is not None else 86_400.0),
        ),
        interaction_state=InteractionState(
            assistant_available=(
                interaction.assistant_available if interaction is not None else False
            ),
            assistant_mode=(interaction.assistant_mode if interaction is not None else "UNKNOWN"),
            # `phone` declared from P25 T8 (`DEBT-020`/`DEBT-022`). Absent phone
            # reading is fail-closed to `False`, same reasoning as everywhere
            # else here: a call the vehicle never reported cannot be acted on,
            # but it also should not silence the feature — only a call the
            # vehicle actually reports does that (`E06`/`BR-06`).
            call_active=phone.call_active if phone is not None else False,
            inference_confidence=(
                interaction.inference_confidence if interaction is not None else 0.0
            ),
        ),
        # `ba.md` Preconditions §2: "Network = Online". `connectivity` domain
        # declared from P25 T9. A vehicle that never reported it reads as
        # offline, same fail-closed reasoning `ConnectivityState` itself uses
        # at the platform layer.
        connectivity_state=ConnectivityState(
            online=connectivity.online if connectivity is not None else False,
        ),
        # `ba.md` Bước 5 Blocking checks / `E05`/`BR-05`. `safety` domain
        # declared from P27 (ADR-0029).
        safety_state=SafetyState(
            alert_level=safety.alert_level if safety is not None else "UNKNOWN",
            adas_state=safety.adas_state if safety is not None else "UNKNOWN",
        ),
        settings=Settings(
            # Reliability follows from the domain arriving at all — fail-closed.
            battery_state_reliable=motion is not None,
            vehicle_state_reliable=motion is not None,
            navigation_state_reliable=navigation is not None,
            interaction_state_reliable=interaction is not None,
        ),
    )
