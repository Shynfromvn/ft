"""Request and result models — the inherited data contract, field for field.

Every field name, every bound and every default here comes from `ba.md`. That
axis is **inherited intact**: fields may be added, never removed, and a field
that stops being the source of truth changes its *meaning* to an explicit
override while keeping its name (`docs/architecture/feature-contract.md`,
*Luật hai trục*).

`DEBT-020`: a number of fields here (`demandingDriving`, `doNotDisturb`,
`emergencyActionAccuracy`, `proactiveEnabled`, `cooldownActive`,
`sameContextRejected`, `recommendationHistory`, and the emergency/re-arm/sport/
cooldown bounds in `RuleOverrides`) belonged to a superseded `ba.md` — a
broader document with an emergency flow, a re-arm hysteresis and a two-tier
cooldown that the current, company-approved `ba.md` does not have (and whose
`BR-10` forbids the cooldown outright). Removed rather than kept unread, so a
caller cannot set a flag that changes nothing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class FeatureModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class BatteryState(FeatureModel):
    soc_pct: float = Field(ge=0, le=100)
    #: How old the reading is (`NFR-01`). A value with no age attached cannot
    #: be refused for being stale.
    data_age_seconds: float = Field(default=0.0, ge=0, le=86_400)


class VehicleState(FeatureModel):
    vehicle_in_drive: bool = False
    gear_state: Literal["P", "D", "N", "R", "UNKNOWN"] = "UNKNOWN"
    drive_mode: Literal["NORMAL", "ECO", "SPORT", "TURTLE", "UNKNOWN"] = "UNKNOWN"
    #: `Bước 5` Eligibility gates — "System State = Normal".
    system_state: Literal["NORMAL", "DEGRADED", "UNKNOWN"] = "UNKNOWN"


class NavigationState(FeatureModel):
    active: bool = False
    #: Distance **remaining**, measured now — not the route's total length.
    #: `BR-09` reads it the other way, a 3 km trip is silent from start to
    #: finish and a 200 km trip with 2 km left is not.
    distance_to_destination_km: float | None = Field(default=None, ge=0)
    #: `None` means *we do not know where a charger is*.
    nearest_charger_km: float | None = Field(default=None, ge=0)
    #: `BR-09` only suppresses for Home or a suitable charging station — an
    #: "Other" destination within 5 km must still speak (`AC-04`).
    destination_type: Literal["HOME", "CHARGING_STATION", "OTHER", "UNKNOWN"] = "UNKNOWN"
    data_age_seconds: float = Field(default=86_400, ge=0, le=86_400)


class ConnectivityState(FeatureModel):
    """`ba.md` Preconditions §2 / Bước 5 — "Network = Online"."""

    online: bool = False


class SafetyState(FeatureModel):
    """`ba.md` Bước 5 Blocking checks / `E05`/`BR-05` — Safety và ADAS alert."""

    alert_level: Literal["NONE", "WARNING", "INTERVENTION", "UNKNOWN"] = "UNKNOWN"
    adas_state: Literal["NORMAL", "WARNING", "INTERVENTION", "UNKNOWN"] = "UNKNOWN"


class InteractionState(FeatureModel):
    assistant_available: bool = False
    assistant_mode: Literal["BALANCED", "PROACTIVE", "QUIET", "UNKNOWN"] = "UNKNOWN"
    call_active: bool = False
    #: Default 0 — fail-closed. Nobody publishes this number yet (`DEBT-012`),
    #: and defaulting to 1.0 would make "we never said" read as "confident
    #: enough to intervene".
    inference_confidence: float = Field(default=0, ge=0, le=1)


class Settings(FeatureModel):
    """Per-request switches."""

    battery_state_reliable: bool = False
    vehicle_state_reliable: bool = False
    navigation_state_reliable: bool = False
    interaction_state_reliable: bool = False
    response_timeout_seconds: Literal[6] = 6


class RuleOverrides(FeatureModel):
    """Business values tunable at runtime, each bounded in one direction.

    The direction of every bound is inherited and is not arbitrary: **each one
    is open in the direction that makes the feature quieter and closed in the
    direction that would make it interrupt more readily than the brief
    allows.** The soft threshold may only fall, the suppression radius may only
    widen, the confidence floor may only tighten.

    Values outside a bound are **rejected**, never silently clamped. A clamp
    means the system ran on a number nobody chose and nothing said so.
    """

    soft_recommendation_soc_pct: float | None = Field(default=None, ge=5, le=20)
    nearby_distance_km: float | None = Field(default=None, ge=5, le=20)
    min_inference_confidence: float | None = Field(default=None, ge=0.90, le=1)
    soc_max_age_seconds: float | None = Field(default=None, gt=0, le=10)
    navigation_max_age_seconds: float | None = Field(default=None, gt=0, le=120)
    #: How long to wait for the vehicle to confirm. May only shorten: waiting
    #: longer means longer spent believing something that did not happen.
    eco_ack_timeout_s: float | None = Field(default=None, gt=0, le=3)


class EvaluateRequest(FeatureModel):
    profile_id: str = Field(default="guest", min_length=1, max_length=160)
    battery_state: BatteryState
    vehicle_state: VehicleState
    navigation_state: NavigationState
    interaction_state: InteractionState
    connectivity_state: ConnectivityState = Field(default_factory=ConnectivityState)
    safety_state: SafetyState = Field(default_factory=SafetyState)
    settings: Settings = Field(default_factory=Settings)
    rule_overrides: RuleOverrides = Field(default_factory=lambda: RuleOverrides())
    preview_recommendation: bool = False
    #: Điều kiện nào đánh thức lần đánh giá này — `conditions[].id` của chính
    #: tính năng này (ADR-0075). Rỗng khi lời gọi không đến từ một trigger:
    #: đường REST, hay một bài test gọi thẳng.
    #:
    #: Nó ở đây chứ không suy lại từ trạng thái, và đó là điểm: `ba.md` §3 khai
    #: hai vế nối bằng *HOẶC*, `feature.yaml` dựng hai điều kiện cho chúng, và
    #: viết `if soc <= 20 and trip_just_started` trong service là chép lại luật
    #: ấy ở chỗ thứ hai. Hai chỗ cho một luật là hai chỗ sẽ trôi khỏi nhau.
    woken_by: str = ""


class RespondRequest(FeatureModel):
    """What the driver answered, and when.

    `outcome` has four values because `AC-14` names four things a driver can
    do, and three of them are different: **refusing** is a decision;
    **postponing** is *"not now"*; **not answering** within the 6-second window
    is only *"not yet"*. Collapsing any pair loses what actually happened, and
    `BR-10` forbids treating any of them as grounds to speak less often later.

    `snooze` arrived at P39. Before it, *"để sau"* was sent as `reject` — so a
    driver asking to be reminded later was recorded as having said no, and
    `BR-10` attaches the full cooldown to one and not the other.
    """

    candidate_id: str = Field(min_length=1, max_length=160)
    outcome: Literal["accept", "reject", "snooze", "timeout"]
    #: Which channel answered. `BR-04` allows touch only when Parked.
    channel: Literal["voice", "touch", "none"] = "none"
    responded_after_seconds: float = Field(default=0.0, ge=0, le=3_600)
    #: Only meaningful when `outcome == "accept"` — the caller (today: QC
    #: calling the API directly; eventually the edge, once it reads the mode
    #: back from the ECU) reports whether the vehicle actually confirmed the
    #: change. Defaults `False`, fail-closed: `BR-08`/`AC-09`/`AC-10` forbid
    #: claiming success on anything less than an observed confirmation, and a
    #: caller that says nothing has observed nothing.
    mode_changed: bool = False
