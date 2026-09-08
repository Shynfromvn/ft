"""The business rules. **Pure** — in, out, nothing else.

No HTTP, no database, no clock read from the ambient. The `Clock` arrives as a
parameter, and every flag the rules need is already resolved by the time they
run. That is what lets a unit test drive the six-second response window and the
three-second acknowledgement ceiling without Postgres and without waiting.

| file | holds |
|---|---|
| `rules.py` | the numbers, and the `Bước 5` reason codes |
| `copy.py` | every sentence the driver hears or reads |
| `service.py` | the decisions — this file |
| `agent.py` | looking things up, so this file does not have to |

The reason is not tidiness. `service.py` staying pure is what makes it testable
without a database, and looking up memory is the one thing that would break
that — so that lookup lives in `agent.py`, one layer out.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from features.ft007_battery_status_recommendation.backend import copy
from features.ft007_battery_status_recommendation.backend.rules import (
    EVENT_CODE,
    RESPONSE_WINDOW_SECONDS,
    SILENCE_REASONS,
    TARGET_DRIVING_MODE,
    TARGET_STATE_ECO,
    SilenceReason,
    Thresholds,
)
from features.ft007_battery_status_recommendation.backend.schemas import (
    EvaluateRequest,
    RespondRequest,
    RuleOverrides,
)
from pa.kernel.core.clock import Clock

__all__ = [
    "Action",
    "ActionKind",
    "Decision",
    "MemoryFacts",
    "audit_context",
    "evaluate",
    "public_result",
    "resolve_thresholds",
    "respond",
]

#: `conditions[].id` của vế thứ hai trong `ba.md` §3 — *"một chuyến đi mới bắt
#: đầu / lộ trình thay đổi trong khi SoC đã ở mức ≤20%"*. Hằng này phải khớp
#: từng ký tự với `feature.yaml`, và trình kiểm hợp đồng canh chuyện đó: một id
#: không tồn tại là một điều kiện nền tảng từ chối nạp.
_NEW_ROUTE_CONDITION = "battery_low_on_new_route"

#: Mã lý do cho vế ấy. **Không** dùng lại `soft_threshold_crossed`: kịch bản của
#: vế này khởi động dưới ngưỡng và không bao giờ đi qua nó, nên mã kia sẽ ghi
#: vào bản ghi một sự kiện chưa từng có (`DEBT-178` nửa (b)).
_NEW_ROUTE_REASON = "low_on_new_route"


class ActionKind(StrEnum):
    """What the assistant decided to do, if anything."""

    NONE = "NONE"
    #: Ask about eco mode. Waits for an answer.
    SUGGEST_ECO = "SUGGEST_ECO"
    #: The vehicle would not, or did not, comply (`AC-10`, `BR-08`) — the
    #: assistant reports STATUS Error rather than claim a change that did not
    #: happen.
    EXECUTION_FAILED = "EXECUTION_FAILED"


@dataclass(frozen=True, slots=True)
class Action:
    kind: ActionKind
    voice_line: str = ""
    message: str = ""
    #: Present only when the assistant is asking the vehicle for something.
    command: str | None = None
    command_argument: str | None = None
    #: How long to wait for the vehicle to confirm the mode change.
    ack_timeout_s: float | None = None
    #: How long the driver has to answer (`BA-05`). The 30-second card is the
    #: screen's business and lives in the frontend.
    response_window_s: int | None = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Decision:
    """One evaluation's outcome — what was decided, and why.

    A silence carries a reason and a stage just as an action does. `BR-12` needs
    that, and so does anyone debugging: without it, "considered and chose not to
    speak" and "broke, so nothing happened" produce the same observable.
    """

    action: Action
    reason_code: str
    reason_vi: str
    stage: str = "judgement"

    @property
    def acted(self) -> bool:
        return self.action.kind is not ActionKind.NONE


@dataclass(frozen=True, slots=True)
class MemoryFacts:
    """What the platform remembers, resolved **before** the rules run.

    Passed in rather than looked up, which is the whole reason `service.py` can
    be tested without a database. `handlers.py` fills this in from the S7
    Shared Memory snapshot the platform assembled (plan P28, ADR-0030).

    `DEBT-020`/`BR-10`: `ba.md` explicitly forbids an automatic cooldown or
    repeat-suppression after refusals (`QC-28.1` — the sixth consecutive low-SoC
    crossing must still speak normally). There is deliberately nothing here for
    that — `duplicate_candidate` is a **live**, still-outstanding Candidate, not
    a history of past ones.
    """

    #: `False` when S7 Shared Memory did not answer validly (`E02`/`BR-11`) —
    #: the evaluation must fail closed on `error_reason` rather than proceed.
    available: bool = True
    #: Set only when `available` is `False`. Which of `E02`'s reason codes this
    #: particular failure was.
    error_reason: SilenceReason | None = None
    #: An Eco Candidate for this driver is already outstanding — spoken, not
    #: yet answered, still inside its lifetime (`Bước 5` Memory checks).
    duplicate_candidate: bool = False


def resolve_thresholds(overrides: RuleOverrides) -> Thresholds:
    """Apply overrides once, so every rule in this evaluation sees one set.

    Reading the module constants inside each rule instead would let an override
    apply to some checks and not others — and the resulting behaviour would be a
    mixture nobody specified.

    Written out field by field rather than splatting a dict: a threshold renamed
    on one side and not the other is then a type error here, not a silently
    ignored override at the first evaluation.
    """
    base = Thresholds()

    def pick[T](supplied: T | None, fallback: T) -> T:
        return fallback if supplied is None else supplied

    return Thresholds(
        soft_soc_pct=pick(overrides.soft_recommendation_soc_pct, base.soft_soc_pct),
        nearby_distance_km=pick(overrides.nearby_distance_km, base.nearby_distance_km),
        soc_max_age_seconds=pick(overrides.soc_max_age_seconds, base.soc_max_age_seconds),
        navigation_max_age_seconds=pick(
            overrides.navigation_max_age_seconds, base.navigation_max_age_seconds
        ),
        min_inference_confidence=pick(
            overrides.min_inference_confidence, base.min_inference_confidence
        ),
        eco_ack_timeout_s=pick(overrides.eco_ack_timeout_s, base.eco_ack_timeout_s),
    )


def _silent(reason: SilenceReason, *, stage: str = "judgement") -> Decision:
    return Decision(
        action=Action(kind=ActionKind.NONE),
        reason_code=reason.value,
        reason_vi=SILENCE_REASONS[reason],
        stage=stage,
    )


def _battery_data_problem(request: EvaluateRequest, thresholds: Thresholds) -> SilenceReason | None:
    """`E01` — missing, stale, or low-confidence battery data.

    `invalid_payload` is not reachable here: `extra="forbid"` and typed,
    bounded fields already refuse a malformed request at the schema boundary,
    before this function ever runs.
    """
    if not request.settings.battery_state_reliable:
        return SilenceReason.DATA_MISSING
    if request.battery_state.data_age_seconds > thresholds.soc_max_age_seconds:
        return SilenceReason.DATA_STALE
    if request.interaction_state.inference_confidence < thresholds.min_inference_confidence:
        return SilenceReason.DATA_STALE
    return None


def _navigation_problem(request: EvaluateRequest, thresholds: Thresholds) -> SilenceReason | None:
    """`E03` — Navigation context must fail closed.

    `ba.md` requires the opposite of what an earlier version of this file did:
    Navigation being unavailable or stale blocks the Candidate. It is not read
    as "we are not sure, so speak" — that inversion belonged to a superseded
    `ba.md` (`DEBT-020`).
    """
    if not request.settings.navigation_state_reliable:
        return SilenceReason.NAVIGATION_UNAVAILABLE
    if request.navigation_state.data_age_seconds > thresholds.navigation_max_age_seconds:
        return SilenceReason.NAVIGATION_STALE
    # `E03`: an active destination whose type could not be classified fails
    # closed. Navigation being simply inactive (no destination at all) is not
    # this case — there is nothing to classify, so `_near_a_known_destination`
    # correctly finds nothing to suppress on.
    if request.navigation_state.active and request.navigation_state.destination_type == "UNKNOWN":
        return SilenceReason.DESTINATION_TYPE_UNKNOWN
    return None


def _near_a_known_destination(request: EvaluateRequest, thresholds: Thresholds) -> bool:
    """`BR-09` — call only once `_navigation_problem` has returned `None`.

    Suppresses only for Home or a suitable charging station within 5 km
    (`AC-03`) — an "Other" destination within the same radius must still
    speak (`AC-04`), and distance alone is never sufficient.
    """
    if request.navigation_state.destination_type not in ("HOME", "CHARGING_STATION"):
        return False
    charger = request.navigation_state.nearest_charger_km
    destination = request.navigation_state.distance_to_destination_km
    known = [value for value in (charger, destination) if value is not None]
    if not known:
        return False
    return min(known) < thresholds.nearby_distance_km


# ── the soft flow ─────────────────────────────────────────────────────────


def _evaluate_soft(
    request: EvaluateRequest,
    thresholds: Thresholds,
    facts: MemoryFacts,
) -> Decision:
    """`Bước 5` của `ba.md`, đúng thứ tự: cổng điều kiện đủ trước, dữ liệu sau.

    Thứ tự không phải ngẫu nhiên: mỗi cổng trả lời "có nên xét tiếp không"
    trước khi cổng sau chạy, để mã lý do ghi lại là điều **đầu tiên** chặn lại,
    chứ không phải điều chặn cuối cùng tình cờ chạy tới.

    `DEBT-020`: hàm này từng mang tên `_evaluate_soft` để phân biệt với một
    nhánh khẩn cấp không còn tồn tại (`ba.md` hiện hành không có luồng 5%).
    Giữ tên vì nó vẫn đúng — đây vẫn là nhánh "mềm" duy nhất còn lại.
    """
    # `BR-01`: "SoC chạm mức 20%" đọc theo hướng đóng (inclusive) — đúng 20.0%
    # vẫn đủ điều kiện, chỉ *trên* 20.0% mới im lặng.
    if request.battery_state.soc_pct > thresholds.soft_soc_pct:
        return _silent(SilenceReason.ABOVE_THRESHOLD, stage="event")

    # `BR-01`/`Bước 5`: xe chưa ở Eco Mode. Đề xuất lại thứ tài xế đã làm là
    # bằng chứng rõ nhất rằng trợ lý không theo dõi họ.
    if request.vehicle_state.drive_mode == "ECO":
        return _silent(SilenceReason.ALREADY_IN_ECO_MODE)

    # `Bước 5` Eligibility gates / `E04`: Assistant Mode phải Balanced hoặc
    # Proactive. `Preconditions §2` không giới hạn "Vehicle State" thành riêng
    # Driving — Parked và Driving đều hợp lệ, nên không có cổng nào chặn theo
    # `vehicle_in_drive` ở đây (khác bản trước — `DEBT-020` ghi rõ đó là một
    # cổng sai chiều).
    if request.interaction_state.assistant_mode not in ("BALANCED", "PROACTIVE"):
        return _silent(SilenceReason.ASSISTANT_MODE_NOT_ALLOWED)

    # `Preconditions §2`/`Bước 5` Eligibility gates: xe phải Online.
    if not request.connectivity_state.online:
        return _silent(SilenceReason.OFFLINE)

    # `Bước 5` Eligibility gates: System State phải Normal.
    if request.vehicle_state.system_state != "NORMAL":
        return _silent(SilenceReason.SYSTEM_STATE_NOT_NORMAL)

    # `Bước 5` Eligibility gates: ViTa đang ở trạng thái Available.
    if not request.interaction_state.assistant_available:
        return _silent(SilenceReason.ASSISTANT_UNAVAILABLE)

    # `Bước 5` Blocking checks / `E06`/`BR-06`: cuộc gọi đang diễn ra chặn
    # Voice và Sound vô điều kiện — S5 không tạo Candidate.
    if request.interaction_state.call_active:
        return _silent(SilenceReason.CALL_ACTIVE)

    # `Bước 5` Blocking checks / `E05`/`BR-05`: không cạnh tranh với Safety/
    # System Alert hay ADAS. `UNKNOWN` không tự chặn (ADR-0029) — chỉ giá trị
    # tường minh Warning/Intervention mới chặn.
    #
    # Đây, cộng `call_active` ở trên, **là** "không có tương tác ưu tiên cao
    # hơn" mà `ba.md` Bước 5 liệt kê như một gạch đầu dòng riêng — xác nhận từ
    # BA (2026-08-28): chỉ đúng ba thứ được coi là ưu tiên cao hơn, Safety/
    # System Alert, ADAS Warning/Intervention, và cuộc gọi đang diễn ra. Không
    # có cổng thứ tư nào còn thiếu.
    if request.safety_state.alert_level in ("WARNING", "INTERVENTION") or (
        request.safety_state.adas_state in ("WARNING", "INTERVENTION")
    ):
        return _silent(SilenceReason.SAFETY_PREEMPTED)

    # `E01`/`NFR-01`: dữ liệu SoC phải tươi và đủ tin cậy.
    battery_problem = _battery_data_problem(request, thresholds)
    if battery_problem is not None:
        return _silent(battery_problem, stage="vehicle_state")

    # `E03`/`NFR-01`: bối cảnh Navigation phải khả dụng và đủ tươi, fail-closed
    # nếu không — xem docstring của `_navigation_problem`.
    navigation_problem = _navigation_problem(request, thresholds)
    if navigation_problem is not None:
        return _silent(navigation_problem, stage="vehicle_state")

    # `BR-09`: chặn theo khoảng cách gần, chỉ khi điểm đến là Home hoặc trạm
    # sạc phù hợp (`AC-03`/`AC-04`).
    if _near_a_known_destination(request, thresholds):
        return _silent(SilenceReason.PROXIMITY_SUPPRESSED)

    # `Bước 3`/`E02`/`BR-11`: chạm S7 Shared Memory là việc có I/O duy nhất
    # trong nhánh này — đặt sau mọi cổng rẻ khác để không trả giá cho một lần
    # đọc DB khi một cổng khác đã đủ để im lặng. Không hợp lệ thì fail-closed
    # với đúng mã lý do S7 đã báo.
    if not facts.available:
        reason = facts.error_reason or SilenceReason.MEMORY_UNAVAILABLE
        return _silent(reason)

    # `Bước 5` Memory checks: một Candidate Eco cho tài xế này đang chờ trả
    # lời — một Candidate thứ hai là hai lời mời cạnh tranh cho cùng một
    # quyết định.
    if facts.duplicate_candidate:
        return _silent(SilenceReason.DUPLICATE_CANDIDATE)

    # **Mã lý do đọc từ cột mốc đã đánh thức, không suy lại từ trạng thái**
    # (ADR-0075). `ba.md` §3 khai hai vế nối bằng *HOẶC*, và một bản ghi nói
    # *"đi qua ngưỡng"* cho vế thứ hai là một bản ghi khẳng định một chuyện
    # không xảy ra — `doi-lo-trinh` khởi động ở 18% và không bao giờ chạm 20%.
    #
    # Rỗng thì giữ mã cũ: đường REST không có cột mốc nào, và đổi câu nó nói
    # hôm nay là đổi một thứ plan này không đụng tới.
    acted_code, acted_vi = (
        (_NEW_ROUTE_REASON, "Chuyến mới bắt đầu khi pin đã dưới ngưỡng")
        if request.woken_by == _NEW_ROUTE_CONDITION
        else ("soft_threshold_crossed", "Pin đi qua ngưỡng thấp")
    )
    spoken = copy.eco_suggestion(request.battery_state.soc_pct)
    return Decision(
        action=Action(
            kind=ActionKind.SUGGEST_ECO,
            voice_line=spoken.voice_line,
            message=spoken.message,
            command="SET_DRIVE_MODE",
            command_argument="ECO",
            ack_timeout_s=thresholds.eco_ack_timeout_s,
            response_window_s=RESPONSE_WINDOW_SECONDS,
            choices=("Đồng ý", "Bỏ qua"),
        ),
        reason_code=acted_code,
        reason_vi=acted_vi,
        stage="action",
    )


# ── entry points ──────────────────────────────────────────────────────────


def evaluate(
    request: EvaluateRequest,
    *,
    clock: Clock,
    facts: MemoryFacts | None = None,
) -> Decision:
    """Decide what, if anything, to say. Pure: same inputs, same answer.

    `facts` defaults to `MemoryFacts()` (memory available, nothing duplicate)
    rather than being required — a caller that never touches S7 Shared Memory
    (every existing test that predates plan P28) keeps its old behaviour
    unchanged. `handlers.evaluate()`, the real path, always passes a value it
    actually resolved.
    """
    del clock  # unused now that the demanding-driving defer is gone (DEBT-020)
    thresholds = resolve_thresholds(request.rule_overrides)
    return _evaluate_soft(request, thresholds, facts or MemoryFacts())


def respond(
    request: RespondRequest,
    *,
    clock: Clock,
    thresholds: Thresholds | None = None,
    mode_changed: bool = False,
) -> Decision:
    """Record what the driver answered, and say the matching thing.

    `mode_changed` is the whole of `BR-08`/`AC-09`: the caller has read the
    drive mode back from the vehicle, and success is only claimed when it
    actually changed. Saying "switched successfully" and then showing the old
    mode costs trust in the entire assistant, permanently — so this function
    cannot say it on its own.
    """
    del clock  # unused now that the two-tier cooldown is gone (DEBT-020/BR-10)
    del thresholds  # no more cooldown to read a duration from

    if request.outcome == "accept":
        if not mode_changed:
            # `AC-10`/`BR-08`: accepted, but the vehicle did not comply. Report
            # STATUS Error and hand the decision back rather than claim a
            # change that did not happen.
            spoken = copy.eco_mode_change_failed()
            return Decision(
                action=Action(
                    kind=ActionKind.EXECUTION_FAILED,
                    voice_line=spoken.voice_line,
                    message=spoken.message,
                ),
                reason_code="execution_failed",
                reason_vi="Tài xế đồng ý nhưng xe không đổi chế độ",
                stage="action",
            )
        spoken = copy.eco_confirmed()
        return Decision(
            action=Action(
                kind=ActionKind.SUGGEST_ECO,
                voice_line=spoken.voice_line,
                message=spoken.message,
            ),
            reason_code="accepted_and_mode_changed",
            reason_vi="Tài xế đồng ý và chế độ đã đổi thật",
            stage="action",
        )

    if request.outcome == "reject":
        spoken = copy.eco_refused()
        return Decision(
            action=Action(
                kind=ActionKind.NONE,
                voice_line=spoken.voice_line,
                message=spoken.message,
            ),
            reason_code="rejected",
            reason_vi="Tài xế từ chối",
            stage="action",
        )

    if request.outcome == "snooze":
        # `AC-14` liệt ba kết cục và `BR-10` gắn hệ quả khác nhau: từ chối mang
        # khoảng nghỉ đầy đủ, hoãn thì không. Trước P39 nút *"Để sau"* gửi
        # `reject`, nên một lời hoãn đi vào hệ thống dưới dạng một lời từ chối.
        spoken = copy.eco_snoozed()
        return Decision(
            action=Action(
                kind=ActionKind.NONE,
                voice_line=spoken.voice_line,
                message=spoken.message,
            ),
            reason_code="snoozed",
            reason_vi="Tài xế hoãn lại",
            stage="action",
        )

    # `AC-14`: no answer within the 6-second window is `ignored`, not a
    # refusal — `BR-10` forbids treating it as grounds to speak less often.
    return Decision(
        action=Action(kind=ActionKind.NONE),
        reason_code="ignored",
        reason_vi="Tài xế không phản hồi trong cửa sổ 6 giây",
        stage="judgement",
    )


def audit_context(request: EvaluateRequest) -> dict[str, Any]:
    """The slice of `request` `AC-16`'s audit trail needs, resolved once.

    `/evaluate` is the only place these raw values exist — `/respond` only
    ever sees the driver's answer, never the vehicle's state at the moment the
    recommendation was made. The route carries this dict forward inside the
    Candidate's own `evidence` (opaque by design) so `/respond`'s
    `recommendation_hook` can fold it into the final audit record without the
    platform ever reading a field name that belongs to this feature.
    """
    return {
        "socPct": request.battery_state.soc_pct,
        "driveMode": request.vehicle_state.drive_mode,
        "vehicleState": "Driving" if request.vehicle_state.vehicle_in_drive else "Parked",
        "assistantMode": request.interaction_state.assistant_mode,
        "audioState": "Call" if request.interaction_state.call_active else "Idle",
    }


def public_result(decision: Decision) -> dict[str, Any]:
    """The shape a handler returns, before the platform applies the allowlist.

    Deliberately includes more than `publicResult.allowedFields` names: the
    platform filters, and a feature that pre-filtered would be deciding its own
    privacy policy, which invariant I7 puts on the platform's side.

    `confirmation` is only present when this decision is **asking** for
    something (`action.command` set — the `SET_DRIVE_MODE` offer from
    `evaluate()`). `respond()` reuses `ActionKind.SUGGEST_ECO` for its own
    "Đã chuyển sang Eco Mode." status line, which has no command and asks
    nothing, so it carries no confirmation contract — the platform route that
    mints a `Candidate` (plan P26) only ever sees `evaluate()`'s output, but
    `public_result` is shared by both handlers and must not lie for the other
    one.
    """
    confirmation = (
        {
            # `BR-07`: the mode change must not execute without an explicit
            # confirmation.
            "required": True,
            "voiceAllowed": True,
            # `BR-04`: touch is only a valid yes while Parked.
            "touchAllowedWhenParked": True,
            # Bước 9: the voice response window.
            "windowSeconds": float(RESPONSE_WINDOW_SECONDS),
        }
        if decision.action.command is not None
        else None
    )
    return {
        "ok": True,
        "featureId": "FT-007",
        "resolvedPlan": {
            "kind": decision.action.kind.value,
            "voiceLine": decision.action.voice_line,
            "message": decision.action.message,
            "choices": list(decision.action.choices),
            "responseWindowSeconds": decision.action.response_window_s,
        },
        "actionsToExecute": (
            [
                {
                    "command": decision.action.command,
                    "argument": decision.action.command_argument,
                    "ackTimeoutSeconds": decision.action.ack_timeout_s,
                }
            ]
            if decision.action.command
            else []
        ),
        # The same action as `actionsToExecute` above, said in the vocabulary of
        # the S5 → S7 contract. Two shapes rather than one because they answer
        # different questions: `actionsToExecute` is an instruction for the car
        # (*"send SET_DRIVE_MODE with argument ECO"*), `recommendedActions` is a
        # statement of intent for S7 (*"this recommends driving_mode become
        # ECO"*). Deriving the second from `decision.action.command` would be
        # the platform's job leaking into the feature; both are declared here
        # because both are this feature's vocabulary.
        "recommendedActions": (
            [{"target": TARGET_DRIVING_MODE, "targetState": TARGET_STATE_ECO}]
            if decision.action.command is not None
            else []
        ),
        "eventCode": EVENT_CODE,
        "final": decision.acted,
        "confirmation": confirmation,
        "feedback": {
            "reasonCode": decision.reason_code,
            "reasonVi": decision.reason_vi,
            "stage": decision.stage,
        },
    }
