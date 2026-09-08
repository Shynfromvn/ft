"""Thresholds and the nine silence rules — the values, and what checks them.

Thresholds are **Python constants with types and tests**, not YAML. A string in
a configuration file has nothing checking it still means what it meant; a
constant here is read by the same test that asserts the behaviour it produces.

Every number below traces to a decision. Where a company document fixed it, that
is said; where the project owner settled an open question, the question is named.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

__all__ = [
    "ECO_ACK_TIMEOUT_S",
    "EVENT_CODE",
    "MIN_INFERENCE_CONFIDENCE",
    "NAVIGATION_MAX_AGE_SECONDS",
    "NEARBY_DISTANCE_KM",
    "RESPONSE_WINDOW_SECONDS",
    "SILENCE_REASONS",
    "SOC_MAX_AGE_SECONDS",
    "SOFT_RECOMMENDATION_SOC_PCT",
    "TARGET_DRIVING_MODE",
    "TARGET_STATE_ECO",
    "SilenceReason",
    "Thresholds",
    "watch_thresholds",
]

# ── vocabulary this feature owns on the S5 → S7 wire ──────────────────────
#
# These three strings live here and **only** here. `docs/architecture/contract-s5-s7.md`
# gives the platform the shape of `recommendedActions` and leaves the catalogue
# to whichever feature emits one — invariant 1 forbids the platform knowing that
# `driving_mode` exists, and `docs-check.sh §6` checks it.
#
# Open clauses `RA-01` (the full target catalogue) and `RA-02` (the eventCode
# catalogue) are still under negotiation between the parties. When they settle,
# they settle in files like this one, not in `backend/src/pa`.

#: What this recommendation asks the vehicle to change.
TARGET_DRIVING_MODE: Final = "driving_mode"
#: What it asks it to change to.
TARGET_STATE_ECO: Final = "ECO"
#: Names the kind of recommendation on the wire. Distinct from the internal
#: `ActionKind.SUGGEST_ECO`: one is our enum, the other is a string the other
#: side of a contract reads.
EVENT_CODE: Final = "battery_low_eco_suggestion"


# ── inherited from the company document ───────────────────────────────────

#: Speak when charge falls to this mark or below. `BR-01` reads as a closed
#: bound ("SoC chạm mức 20%"): `service.py` compares with `>`, not `>=`, so
#: exactly 20.0 is still eligible.
SOFT_RECOMMENDATION_SOC_PCT: Final = 20.0
#: Within this distance of Home or a suitable charging station, stay quiet
#: (`BR-09`). Distance alone never suppresses — `service.py` only applies this
#: once `destination_type` says the destination is one of those two.
NEARBY_DISTANCE_KM: Final = 5.0
#: Older than this and the battery reading is not worth speaking on (`NFR-01`).
SOC_MAX_AGE_SECONDS: Final = 10.0
#: `NFR-01`: Navigation context used for the proximity check.
NAVIGATION_MAX_AGE_SECONDS: Final = 120.0
#: Confidence floor. Nobody publishes this number yet (`DEBT-012`); the
#: simulator and the dashboard supply it, and the default of 0 is fail-closed.
MIN_INFERENCE_CONFIDENCE: Final = 0.90
#: `BA-05` in the reference brief, kept as the voice response window (`NFR-*`
#: does not fix this feature's own ack timing, and 6s matches `ba.md`'s
#: 6-second no-response rule, Bước 9).
RESPONSE_WINDOW_SECONDS: Final = 6
#: How long to wait for the vehicle to confirm the mode change before giving up.
ECO_ACK_TIMEOUT_S: Final = 3.0


@dataclass(frozen=True, slots=True)
class Thresholds:
    """The values this evaluation runs on, after any overrides are applied.

    Resolved once and passed down, so every rule in a single evaluation sees the
    same numbers. Reading the constants directly inside each rule would let an
    override apply to some of them and not others.
    """

    soft_soc_pct: float = SOFT_RECOMMENDATION_SOC_PCT
    nearby_distance_km: float = NEARBY_DISTANCE_KM
    soc_max_age_seconds: float = SOC_MAX_AGE_SECONDS
    navigation_max_age_seconds: float = NAVIGATION_MAX_AGE_SECONDS
    min_inference_confidence: float = MIN_INFERENCE_CONFIDENCE
    eco_ack_timeout_s: float = ECO_ACK_TIMEOUT_S


class SilenceReason(StrEnum):
    """Reason codes a dashboard can group silences by — `ba.md` `Bước 5`'s own.

    Codes rather than sentences because `BR-12` needs "every silence for reason
    X this month" to be a query. The Vietnamese wording lives beside them in
    `SILENCE_REASONS`, and the driver only ever sees it when they ask.
    """

    #: `BR-01`/`Bước 5` fail-closed list — already in Eco Mode.
    ALREADY_IN_ECO_MODE = "already_in_eco_mode"
    #: `E04` — Assistant Mode is not Balanced or Proactive.
    ASSISTANT_MODE_NOT_ALLOWED = "assistant_mode_not_allowed"
    #: `Preconditions §2` — the vehicle cannot reach the cloud.
    OFFLINE = "offline"
    #: `Bước 5` Eligibility gates — ViTa is not Available.
    ASSISTANT_UNAVAILABLE = "assistant_unavailable"
    #: `Bước 5` Eligibility gates — System State is not Normal.
    SYSTEM_STATE_NOT_NORMAL = "system_state_not_normal"
    #: `E06`/`BR-06` — a call is active; it blocks Voice and Sound outright.
    CALL_ACTIVE = "call_active"
    #: `E05`/`BR-05` — a Safety/System Alert or ADAS Warning/Intervention is
    #: active; the assistant yields rather than compete with it.
    SAFETY_PREEMPTED = "safety_preempted"
    #: `E01` — a required field is missing.
    DATA_MISSING = "data_missing"
    #: `E01` — SoC/drive-mode data is older than `NFR-01` allows, or confidence
    #: is below the floor.
    DATA_STALE = "data_stale"
    #: `E03` — Navigation context is not available at all.
    NAVIGATION_UNAVAILABLE = "navigation_unavailable"
    #: `E03` — Navigation context is older than `NFR-01` allows.
    NAVIGATION_STALE = "navigation_stale"
    #: `E03` — Navigation is active but the destination could not be classified.
    DESTINATION_TYPE_UNKNOWN = "destination_type_unknown"
    #: `BR-09` — Home or a suitable charging station, within 5 km, and known.
    PROXIMITY_SUPPRESSED = "proximity_suppressed"
    #: Charge is simply above the mark. The ordinary case, and still recorded,
    #: because a QA report needs to distinguish it from a rule that suppressed.
    ABOVE_THRESHOLD = "above_threshold"
    #: `E02`/`BR-11` — S7 Shared Memory did not answer inside the `NFR-02`
    #: budget at all (a timeout on the call itself, not a slow-but-valid one).
    MEMORY_TIMEOUT = "memory_timeout"
    #: `E02`/`BR-11` — S7 Shared Memory raised, or the call to it failed for any
    #: reason other than the budget running out.
    MEMORY_UNAVAILABLE = "memory_unavailable"
    #: `E02`/`BR-11` — S7 Shared Memory answered inside the budget with a
    #: snapshot that does not carry what `NFR-02` requires (no `generation`).
    MEMORY_INCONSISTENT = "memory_inconsistent"
    #: `E02`/`BR-11` — S7 Shared Memory answered inside the budget with a
    #: snapshot older than `ContextAggregator.STALE_AFTER_S` (P22 T12'). That
    #: threshold is a technical placeholder, not a BA-confirmed number —
    #: `DEBT-066`.
    MEMORY_EXPIRED = "memory_expired"
    #: `Bước 5` Memory checks / `BR-11` — an Eco Candidate for this driver is
    #: already outstanding (spoken, not yet answered, still inside its
    #: lifetime). A second one would be two competing offers for one decision.
    DUPLICATE_CANDIDATE = "duplicate_candidate"


#: What the driver hears if they ask why nothing was said (`BR-12`). They see it
#: **only when they ask**; the demo dashboard always shows it. Two audiences,
#: two levels of visibility.
SILENCE_REASONS: Final[dict[SilenceReason, str]] = {
    SilenceReason.ALREADY_IN_ECO_MODE: "Xe đã ở Eco Mode",
    SilenceReason.ASSISTANT_MODE_NOT_ALLOWED: "Chế độ trợ lý không cho phép nói chủ động",
    SilenceReason.OFFLINE: "Xe đang mất kết nối tới cloud",
    SilenceReason.ASSISTANT_UNAVAILABLE: "Trợ lý đang không sẵn sàng",
    SilenceReason.SYSTEM_STATE_NOT_NORMAL: "Trạng thái hệ thống không bình thường",
    SilenceReason.CALL_ACTIVE: "Đang trong cuộc gọi",
    SilenceReason.SAFETY_PREEMPTED: "Đang có cảnh báo an toàn hoặc ADAS hoạt động",
    SilenceReason.DATA_MISSING: "Thiếu dữ liệu bắt buộc",
    SilenceReason.DATA_STALE: "Dữ liệu pin không đủ mới hoặc không đủ tin cậy",
    SilenceReason.NAVIGATION_UNAVAILABLE: "Không có bối cảnh Navigation",
    SilenceReason.NAVIGATION_STALE: "Bối cảnh Navigation quá cũ",
    SilenceReason.DESTINATION_TYPE_UNKNOWN: "Không xác định được loại điểm đến",
    SilenceReason.PROXIMITY_SUPPRESSED: "Đã gần Nhà hoặc trạm sạc đã biết",
    SilenceReason.ABOVE_THRESHOLD: "Mức pin còn trên ngưỡng",
    SilenceReason.MEMORY_TIMEOUT: "S7 Shared Memory không trả lời kịp trong 300 ms",
    SilenceReason.MEMORY_UNAVAILABLE: "S7 Shared Memory không khả dụng",
    SilenceReason.MEMORY_INCONSISTENT: "S7 Shared Memory trả về một snapshot không hợp lệ",
    SilenceReason.MEMORY_EXPIRED: "S7 Shared Memory trả về một snapshot đã hết hạn",
    SilenceReason.DUPLICATE_CANDIDATE: "Đã có một đề cử Eco đang chờ tài xế trả lời",
}


def watch_thresholds() -> dict[str, float]:
    """Entry threshold for each signal the platform watches on this feature.

    The seam of ADR-0013. `feature.yaml` says *which* signal and *which way*;
    this says *how much*, and it says it by handing back the same constant the
    behaviour tests read — so there is no second copy of 20 anywhere, and no
    drift check to write.

    Keys must match `routing.watches[].signal` exactly. A mismatch either way is
    refused at startup, because a feature watching a signal it has no mark for
    never runs, and "never ran" looks exactly like "the threshold was never
    crossed".
    """
    return {"motion.socPct": SOFT_RECOMMENDATION_SOC_PCT}
