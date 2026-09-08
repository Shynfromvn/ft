"""Request and result models — the inherited data contract, field for field.

Every field name, every bound and every default here comes from `ba.md`. That
axis is **inherited intact**: fields may be added, never removed, and a field
that stops being the source of truth changes its *meaning* to an explicit
override while keeping its name.

**What this package removed, and why it is a removal rather than a loss.** The
wider feature `ft007_battery_status_recommendation` carries `NavigationState`,
`SafetyState` and `InteractionState`, plus `systemState`, `gearState`,
`vehicleInDrive` and `inferenceConfidence`. This POC's `ba.md` puts every gate
that read them out of scope — §Phạm vi names Navigation, Safety/ADAS, calls and
Assistant Mode explicitly — so they are gone rather than kept unread. A field a
caller can set that changes nothing is worse than no field: it reads as a
control.

`Preconditions §2` of this brief lists exactly two conditions, network and data
freshness, and `BR-01` adds one state check (not already in Eco Mode). Three
conditions, three pieces of state: battery, drive mode, connectivity. That is
the whole input surface.
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
    #: How old the reading is. A value with no age attached cannot be refused
    #: for being stale, and `Preconditions §2` requires that it can be.
    data_age_seconds: float = Field(default=0.0, ge=0, le=86_400)


class VehicleState(FeatureModel):
    """One field, because `BR-01` asks one question of the vehicle.

    `gearState`, `vehicleInDrive` and `systemState` are not here. The first two
    fed the wider feature's Parked/Driving output rules (`AC-06`, `AC-07`,
    `AC-13`), which this brief does not have — `Bước 4` describes one display
    and does not vary it by vehicle state. `systemState` fed a `Bước 5`
    eligibility gate that this brief's `Preconditions §2` does not list.
    """

    drive_mode: Literal["NORMAL", "ECO", "SPORT", "TURTLE", "UNKNOWN"] = "UNKNOWN"


class ConnectivityState(FeatureModel):
    """`ba.md` `Preconditions §2` — "Kết nối mạng: Online"."""

    online: bool = False


class Settings(FeatureModel):
    """Per-request switches.

    Two flags, one per domain whose absence must be distinguishable from its
    contents. `runtime.py` sets each from whether the domain actually arrived,
    which is what makes "we received no battery reading" and "the battery is
    full" two different situations.

    Defaults are `False` — fail-closed. A caller that says nothing has
    established nothing, and the correct response to establishing nothing is
    silence.
    """

    battery_state_reliable: bool = False
    vehicle_state_reliable: bool = False


class RuleOverrides(FeatureModel):
    """Business values tunable at runtime, each bounded in one direction.

    The direction of every bound is inherited and is not arbitrary: **each one
    is open in the direction that makes the feature quieter and closed in the
    direction that would make it interrupt more readily than the brief
    allows.** The threshold may only fall; the freshness ceiling may only
    tighten.

    Values outside a bound are **rejected**, never silently clamped. A clamp
    means the system ran on a number nobody chose and nothing said so.

    Four overrides went out with the constants they tuned: `nearbyDistanceKm`,
    `navigationMaxAgeSeconds`, `minInferenceConfidence` and `ecoAckTimeoutS`.
    """

    soft_recommendation_soc_pct: float | None = Field(default=None, ge=5, le=20)
    soc_max_age_seconds: float | None = Field(default=None, gt=0, le=10)


class EvaluateRequest(FeatureModel):
    profile_id: str = Field(default="guest", min_length=1, max_length=160)
    battery_state: BatteryState
    vehicle_state: VehicleState
    connectivity_state: ConnectivityState = Field(default_factory=ConnectivityState)
    settings: Settings = Field(default_factory=Settings)
    rule_overrides: RuleOverrides = Field(default_factory=lambda: RuleOverrides())
    #: KIỂM TRA TRƯỚC KHI XOÁ. Không luật nào trong `service.py` đọc trường
    #: này — nó thuộc về đường REST/demo, không về `ba.md`. Nhưng
    #: `extra="forbid"` nghĩa là nếu route vẫn gửi nó lên mà model không khai,
    #: mọi request đều bị từ chối ở biên schema.
    #:
    #: Giữ tạm cho tới khi xác nhận được route có gửi hay không. Nếu không,
    #: xoá — repo này gỡ trường không ai đọc chứ không giữ lại.
    preview_recommendation: bool = False

    #: `wokenBy` KHÔNG có ở đây, và đó là một lược bỏ có chủ ý.
    #:
    #: Gói gốc mang trường ấy vì `ba.md` của nó khai hai vế Trigger nối bằng
    #: *HOẶC*, nên mã lý do phải đọc từ cột mốc đã đánh thức thay vì suy lại từ
    #: trạng thái. Brief này có đúng một vế — SoC ≤ 20% — nên chỉ có một cột
    #: mốc, và một trường luôn mang cùng một giá trị không phân biệt được điều
    #: gì.
    #:
    #: `runtime.project_runtime` vẫn nhận tham số `woken_by` vì nền tảng gọi nó
    #: với tham số ấy; nó bị bỏ qua ở đó, và lý do được ghi tại chỗ.


class RespondRequest(FeatureModel):
    """Tồn tại để `handlers.*` đủ bốn trường, không để phục vụ một luồng nào.

    `ba.md` §Phạm vi loại bỏ phản hồi Voice/Touch, timeout phản hồi, thực thi
    lệnh ECU, xác nhận ECU, và toàn bộ lifecycle sau khi Candidate được hiển
    thị. `Bước 4` nói thẳng hai nút xác nhận **không ấn được**. Không màn hình
    nào phát ra một câu trả lời, `routing.triggers` rỗng, và
    `agent.operations` không có `RESPOND` — nên không đường nào dẫn tới model
    này.

    Nó ở đây vì `schemaVersion: 2` đòi cả bốn trường `handlers.*` và cả hai
    model. **Nếu `make feature-check` chấp nhận `null` cho `respondModel` và
    `respond`, xoá cả lớp này lẫn `handlers.respond`.** Một model không ai
    validate được là code chết, và code chết trong gói này bị gỡ chứ không
    comment lại — xem docstring của `copy.py` và `rules.py` cho hai lần gỡ
    trước.

    Một trường, không phải sáu. `outcome`, `channel`, `respondedAfterSeconds`
    và `modeChanged` mô tả những chuyện brief này không có: tài xế trả lời gì,
    qua kênh nào, sau bao lâu, và xe có đổi chế độ thật không.
    """

    candidate_id: str = Field(min_length=1, max_length=160)
