"""The business rules. **Pure** — in, out, nothing else.

No HTTP, no database, no clock read from the ambient. Every flag the rules need
is already resolved by the time they run. That is what lets a unit test drive
every gate below without Postgres and without waiting.

| file | holds |
|---|---|
| `rules.py` | the numbers, and the reason codes |
| `copy.py` | every sentence the driver reads |
| `service.py` | the decisions — this file |
| `agent.py` | looking things up, so this file does not have to |

The reason is not tidiness. `service.py` staying pure is what makes it testable
without a database, and reading Session History is the one thing that would
break that — so that lookup lives one layer out.

**What this package removed.** `ft007_battery_status_recommendation` also holds
`respond()`, `audit_context()`'s wider slice, and six more gates: Assistant
Mode, assistant availability, System State, active call, Safety/ADAS
pre-emption, and the Navigation pair (fail-closed context plus proximity
suppression). This brief's §Phạm vi puts every one of them out of scope, and
`Bước 4` ends the flow at the moment the recommendation is displayed. Removed
rather than kept unreachable: a gate that can never fire still has to be read
and understood by everyone who opens this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from features.ft008_eco_mode_recommendation_poc.backend import copy
from features.ft008_eco_mode_recommendation_poc.backend.rules import (
    EVENT_CODE,
    SILENCE_REASONS,
    TARGET_DRIVING_MODE,
    TARGET_STATE_ECO,
    SilenceReason,
    Thresholds,
)
from features.ft008_eco_mode_recommendation_poc.backend.schemas import (
    EvaluateRequest,
    RuleOverrides,
)
from pa.kernel.core.clock import Clock

__all__ = [
    "Action",
    "ActionKind",
    "Decision",
    "SessionHistoryFacts",
    "audit_context",
    "evaluate",
    "public_result",
    "resolve_thresholds",
]

#: `identity.featureId` của gói này. Một chuỗi, một chỗ — `public_result` là nơi
#: duy nhất phát nó ra, nên đổi ID là sửa đúng dòng này cộng `feature.yaml`.
_FEATURE_ID = "FT-008"


class ActionKind(StrEnum):
    """What the assistant decided to do, if anything.

    Two, not three. `EXECUTION_FAILED` belonged to `ft007_*`'s execution flow —
    the vehicle refusing a mode change — and this brief never asks the vehicle
    for anything.
    """

    NONE = "NONE"
    #: Show the eco recommendation. Waits for nothing: `Bước 4` renders the two
    #: confirmation buttons **disabled** (`BA-03`), so there is no answer to
    #: wait for.
    SUGGEST_ECO = "SUGGEST_ECO"


@dataclass(frozen=True, slots=True)
class Action:
    """Ba trường, không phải tám.

    Năm trường đã gỡ và mỗi cái theo một dòng của §Phạm vi: `voice_line` (không
    có kênh giọng nói — xem `copy.py`), `command` và `command_argument` (không
    ra lệnh cho xe), `ack_timeout_s` (không chờ xe xác nhận), và
    `response_window_s` (không nhận phản hồi).
    """

    kind: ActionKind
    message: str = ""
    #: Nhãn hai nút. Chúng **không bấm được** (`BA-03`); trạng thái ấy là việc
    #: của màn hình, còn chữ trên nút là việc của `copy.py`.
    choices: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Decision:
    """One evaluation's outcome — what was decided, and why.

    A silence carries a reason and a stage just as an action does. Anyone
    debugging needs that: without it, "considered and chose not to speak" and
    "broke, so nothing happened" produce the same observable. `NFR-04` demands
    100% accuracy in deciding whether to create a Candidate, and an accuracy
    claim that cannot be audited is not a claim.
    """

    action: Action
    reason_code: str
    reason_vi: str
    stage: str = "judgement"

    @property
    def acted(self) -> bool:
        return self.action.kind is not ActionKind.NONE


@dataclass(frozen=True, slots=True)
class SessionHistoryFacts:
    """What Session History answered, resolved **before** the rules run.

    Passed in rather than looked up, which is the whole reason `service.py` can
    be tested without a database.

    Named after the brief. `ba.md` calls this store *Session History* and asks
    it exactly one question (`Bước 2`/`AC-02`): is an equivalent Eco
    recommendation already awaiting a response or being processed. The wider
    feature calls the same platform seam *S7 Shared Memory* and gets four
    distinct failure codes out of it; this brief has no `E02` to name them, so
    there is one flag here and one reason code behind it.

    There is deliberately nothing here for a cooldown or a refusal history.
    `Bước 2` blocks on a recommendation that is **still outstanding**, not on
    one that happened before.
    """

    #: `False` when Session History could not be read at all. The evaluation
    #: must fail closed rather than proceed — see
    #: `SilenceReason.SESSION_HISTORY_UNAVAILABLE` for why, and for the fact
    #: that `ba.md` §6 does not cover this case.
    available: bool = True
    #: An Eco recommendation for this driver is already outstanding.
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
        soc_max_age_seconds=pick(overrides.soc_max_age_seconds, base.soc_max_age_seconds),
    )


def _silent(reason: SilenceReason, *, stage: str = "judgement") -> Decision:
    return Decision(
        action=Action(kind=ActionKind.NONE),
        reason_code=reason.value,
        reason_vi=SILENCE_REASONS[reason],
        stage=stage,
    )


def _battery_data_problem(request: EvaluateRequest, thresholds: Thresholds) -> SilenceReason | None:
    """`Preconditions §2` — dữ liệu pin phải có mặt và đủ tươi.

    `invalid_payload` không tới được đây: `extra="forbid"` cộng các trường có
    kiểu và có biên đã từ chối một request méo ngay ở biên schema, trước khi hàm
    này chạy.
    """
    if not request.settings.battery_state_reliable:
        return SilenceReason.DATA_MISSING
    if request.battery_state.data_age_seconds > thresholds.soc_max_age_seconds:
        return SilenceReason.DATA_STALE
    return None


def _decide(
    request: EvaluateRequest,
    thresholds: Thresholds,
    facts: SessionHistoryFacts,
) -> Decision:
    """`Bước 1` → `Bước 3` của `ba.md`, đúng thứ tự tài liệu viết.

    Thứ tự không phải ngẫu nhiên: mỗi cổng trả lời "có nên xét tiếp không" trước
    khi cổng sau chạy, để mã lý do ghi lại là điều **đầu tiên** chặn lại, chứ
    không phải điều chặn cuối cùng tình cờ chạy tới.

    Tên là `_decide`, không phải `_evaluate_soft` như gói gốc. Ở đó cái tên còn
    nghĩa vì tài liệu cũ từng có một nhánh khẩn cấp để đối lập; brief này chưa
    bao giờ có, nên mang cái tên ấy sang là giữ lại một phân biệt người đọc
    không tra được về đâu.
    """
    # `BR-01`/`AC-01`: "SoC ≤ 20%" đọc theo hướng đóng (inclusive) — đúng 20.0%
    # vẫn đủ điều kiện, chỉ *trên* 20.0% mới im lặng.
    if request.battery_state.soc_pct > thresholds.soft_soc_pct:
        return _silent(SilenceReason.ABOVE_THRESHOLD, stage="event")

    # `BR-01`: xe chưa ở Eco Mode. Đề xuất lại thứ tài xế đã làm là bằng chứng
    # rõ nhất rằng trợ lý không theo dõi họ.
    if request.vehicle_state.drive_mode == "ECO":
        return _silent(SilenceReason.ALREADY_IN_ECO_MODE)

    # `Preconditions §2`: "Kết nối mạng: Online".
    if not request.connectivity_state.online:
        return _silent(SilenceReason.OFFLINE)

    # `Bước 1`/`Preconditions §2`: dữ liệu SoC phải có mặt và đủ tươi.
    battery_problem = _battery_data_problem(request, thresholds)
    if battery_problem is not None:
        return _silent(battery_problem, stage="vehicle_state")

    # `Bước 2`: đọc Session History là việc có I/O duy nhất trong luồng này —
    # đặt sau mọi cổng rẻ khác để không trả giá cho một lần đọc DB khi một cổng
    # khác đã đủ để im lặng.
    if not facts.available:
        return _silent(SilenceReason.SESSION_HISTORY_UNAVAILABLE)

    # `Bước 2`/`AC-02`: một khuyến nghị Eco cho tài xế này đang chờ xử lý — một
    # cái thứ hai là hai lời mời cạnh tranh cho cùng một quyết định.
    #
    # `ba.md` **không đặt mốc thời gian** cho "đang chờ": luật là pop-up cũ chưa
    # tắt thì không được hiện cái mới. Ở đây không có gì để đọc thấy điều đó —
    # cờ này do lớp ngoài dựng, và mốc sống của một đề cử là `feature.yaml`
    # `engine.candidateLifetimeSeconds` chứ không phải một hằng trong file này.
    if facts.duplicate_candidate:
        return _silent(SilenceReason.DUPLICATE_CANDIDATE)

    # `Bước 3`: mọi kiểm tra đều đạt, dựng nội dung khuyến nghị.
    displayed = copy.eco_suggestion(request.battery_state.soc_pct)
    return Decision(
        action=Action(
            kind=ActionKind.SUGGEST_ECO,
            message=displayed.text,
            choices=(copy.CHOICE_ACCEPT, copy.CHOICE_DECLINE),
        ),
        reason_code="soft_threshold_crossed",
        reason_vi="Pin đi qua ngưỡng thấp",
        stage="action",
    )


# ── entry point ───────────────────────────────────────────────────────────


def evaluate(
    request: EvaluateRequest,
    *,
    clock: Clock,
    facts: SessionHistoryFacts | None = None,
) -> Decision:
    """Decide whether to recommend anything. Pure: same inputs, same answer.

    `facts` defaults to "Session History readable, nothing outstanding" rather
    than being required, so a test that is not exercising `AC-02` does not have
    to construct one. `handlers.evaluate()`, the real path, always passes a
    value it actually resolved.

    `clock` is taken and discarded. It stays in the signature because the
    platform calls every feature's rules the same way, and because dropping a
    parameter the caller supplies would move the breakage from here to there.
    Nothing in this brief is time-dependent: there is no response window, no
    acknowledgement ceiling, and no cooldown.

    Đây là điểm vào **duy nhất**. Gói gốc còn `respond()`; brief này không có
    câu trả lời nào để ghi nhận.
    """
    del clock
    thresholds = resolve_thresholds(request.rule_overrides)
    return _decide(request, thresholds, facts or SessionHistoryFacts())


def audit_context(request: EvaluateRequest) -> dict[str, Any]:
    """Lát cắt của `request` mà một bản ghi truy vết cần, dựng một lần.

    ── CHƯA CHỐT ────────────────────────────────────────────────────────────
    Không `BA-nn` nào của brief này đòi bản ghi audit — gói gốc có `AC-16` cho
    việc đó, POC không có. Theo luật của repo thì thứ không ai đòi phải được
    gỡ.

    Nó vẫn ở đây vì đường REST đọc `result["context"]` để nhét vào `evidence`
    của Candidate, và bỏ khoá ấy đi có thể làm route nổ ở một chỗ file này
    không nhìn thấy. Kiểm route trước, rồi xoá cả hàm lẫn dòng gọi nó trong
    `handlers.py` nếu route chịu được.

    Hai trường, không phải năm: `vehicleState`, `assistantMode` và `audioState`
    của gói gốc đọc những miền mà `schemas.py` không còn khai.
    """
    return {
        "socPct": request.battery_state.soc_pct,
        "driveMode": request.vehicle_state.drive_mode,
    }


def public_result(decision: Decision) -> dict[str, Any]:
    """The shape a handler returns, before the platform applies the allowlist.

    Deliberately includes more than `publicResult.allowedFields` names: the
    platform filters, and a feature that pre-filtered would be deciding its own
    privacy policy, which is the platform's side of the line.

    Hai khoá của gói gốc **không** có ở đây, và cả hai đều bị `feature.yaml`
    loại khỏi allowlist cùng lý do:

    `actionsToExecute` là một MỆNH LỆNH gửi xuống xe. §Phạm vi loại "thực thi
    lệnh ECU" ra ngoài, nên tính năng này không được phát ra mệnh lệnh nào.

    `confirmation` là hợp đồng xác nhận — bắt buộc xác nhận, cho phép voice,
    cho phép touch khi Parked, cửa sổ 6 giây. Nó chỉ có nghĩa nếu có một đường
    nhận xác nhận, và `Bước 4` nói hai nút **không ấn được**.

    `recommendedActions` thì ở lại: nó là lời khai Ý ĐỊNH ("đề cử này khuyến
    nghị driving_mode thành ECO"), đúng dòng *Hành động khuyến nghị* của
    `Bước 3`. Khai một ý định không phải là ra một lệnh.
    """
    return {
        "ok": True,
        "featureId": _FEATURE_ID,
        "resolvedPlan": {
            "kind": decision.action.kind.value,
            "message": decision.action.message,
            "choices": list(decision.action.choices),
            # `BA-03`: hai nút có mặt nhưng không thao tác được. Khai ở đây
            # thay vì để màn hình tự biết, vì đó là một điều `ba.md` quy định
            # chứ không phải một lựa chọn trình bày.
            "choicesInteractive": False,
        },
        "recommendedActions": (
            [{"target": TARGET_DRIVING_MODE, "targetState": TARGET_STATE_ECO}]
            if decision.acted
            else []
        ),
        "eventCode": EVENT_CODE,
        "final": decision.acted,
        "feedback": {
            "reasonCode": decision.reason_code,
            "reasonVi": decision.reason_vi,
            "stage": decision.stage,
        },
    }