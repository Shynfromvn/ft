"""Business rules, one test per requirement, naming the `ba.md` id it covers.

**Bốn mươi bài của gói rộng hơn không có ở đây**, và mỗi nhóm ra đi cùng cổng
nó kiểm: Assistant Mode và trạng thái trợ lý (`E04`, `Bước 5` eligibility),
System State, cuộc gọi (`E06`/`BR-06`), Safety/ADAS (`E05`/`BR-05`), toàn bộ
Navigation gồm fail-closed và chặn theo khoảng cách (`E03`/`BR-09`/`AC-03`/
`AC-04`), sàn độ tin cậy, cửa sổ trả lời sáu giây, trần xác nhận ba giây, phân
biệt từ chối với không trả lời (`AC-14`), và hợp đồng xác nhận (`BR-07`).
`ba.md` của gói này đưa tất cả ra ngoài phạm vi. Chúng bị xoá cùng code chứ
không giữ lại ở trạng thái đỏ.

Không bài nào ở đây cần đồng hồ. Brief này không có cửa sổ, không có timeout,
không có khoảng nghỉ — nên `service.evaluate` nhận `clock` rồi bỏ, và bài kiểm
điều đó nằm ở `test_contract.py`.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from features.ft008_eco_mode_recommendation_poc.backend import copy, service
from features.ft008_eco_mode_recommendation_poc.backend.copy import MAX_MESSAGE_LENGTH
from features.ft008_eco_mode_recommendation_poc.backend.rules import (
    SOFT_RECOMMENDATION_SOC_PCT,
    SilenceReason,
)
from features.ft008_eco_mode_recommendation_poc.backend.schemas import (
    BatteryState,
    ConnectivityState,
    EvaluateRequest,
    RuleOverrides,
    Settings,
    VehicleState,
)
from features.ft008_eco_mode_recommendation_poc.backend.service import (
    ActionKind,
    SessionHistoryFacts,
)
from pa.kernel.core.clock import SystemClock


def make_request(**overrides: object) -> EvaluateRequest:
    """A car below the mark with trustworthy data — the case where speaking is
    allowed.

    Everything else in this file is a departure from this baseline, which makes
    each test's one difference the thing it is about.
    """
    base: dict[str, object] = {
        "profile_id": "p-1",
        "battery_state": BatteryState(soc_pct=19.0, data_age_seconds=1.0),
        "vehicle_state": VehicleState(drive_mode="NORMAL"),
        "connectivity_state": ConnectivityState(online=True),
        "settings": Settings(battery_state_reliable=True, vehicle_state_reliable=True),
        "rule_overrides": RuleOverrides(),
    }
    base.update(overrides)
    return EvaluateRequest(**base)  # type: ignore[arg-type]


def evaluate(
    request: EvaluateRequest, facts: SessionHistoryFacts | None = None
) -> service.Decision:
    return service.evaluate(request, clock=SystemClock(), facts=facts)


# ── BR-01 · the threshold ─────────────────────────────────────────────────


def test_speaks_below_the_mark() -> None:
    decision = evaluate(make_request())
    assert decision.action.kind is ActionKind.SUGGEST_ECO
    assert decision.acted
    assert decision.stage == "action"


def test_speaks_at_exactly_the_mark() -> None:
    """`BR-01`/`AC-01` đọc ngưỡng theo hướng đóng: "SoC ≤ 20%".

    Đúng 20,0% là con số tài liệu nêu tên và cũng là con số câu nói đọc lên.
    Nếu hệ thống im ở đúng đó, nó im ở chính chỗ mọi người sẽ thử đầu tiên.
    """
    decision = evaluate(
        make_request(battery_state=BatteryState(soc_pct=SOFT_RECOMMENDATION_SOC_PCT, data_age_seconds=1.0))
    )
    assert decision.action.kind is ActionKind.SUGGEST_ECO


def test_stays_quiet_above_the_mark() -> None:
    decision = evaluate(
        make_request(battery_state=BatteryState(soc_pct=20.1, data_age_seconds=1.0))
    )
    assert decision.action.kind is ActionKind.NONE
    assert decision.reason_code == SilenceReason.ABOVE_THRESHOLD.value


def test_stays_quiet_when_already_in_eco() -> None:
    """`BR-01` — đề xuất lại thứ tài xế đã làm là bằng chứng rõ nhất rằng trợ
    lý không theo dõi họ."""
    decision = evaluate(make_request(vehicle_state=VehicleState(drive_mode="ECO")))
    assert decision.reason_code == SilenceReason.ALREADY_IN_ECO_MODE.value


# ── Preconditions §2 · network and freshness ──────────────────────────────


def test_stays_quiet_when_offline() -> None:
    decision = evaluate(make_request(connectivity_state=ConnectivityState(online=False)))
    assert decision.reason_code == SilenceReason.OFFLINE.value


def test_stays_quiet_when_the_battery_domain_never_reported() -> None:
    """Không nhận được số đo khác hẳn nhận được một số đo tồi.

    `runtime.py` dựng cờ này từ việc miền `motion` có tới hay không, nên đây là
    đường mà "xe chưa báo gì" đi tới một lời im lặng có tên.
    """
    decision = evaluate(
        make_request(settings=Settings(battery_state_reliable=False, vehicle_state_reliable=False))
    )
    assert decision.reason_code == SilenceReason.DATA_MISSING.value


def test_stays_quiet_on_stale_data() -> None:
    decision = evaluate(
        make_request(battery_state=BatteryState(soc_pct=19.0, data_age_seconds=11.0))
    )
    assert decision.reason_code == SilenceReason.DATA_STALE.value


def test_a_reading_exactly_at_the_freshness_ceiling_is_still_used() -> None:
    """Biên là `>`, không phải `>=`: đúng 10,0 giây vẫn dùng được.

    Ghim vì đây là loại biên bị đảo trong một lần refactor mà không ai nhận ra
    — cả hai chiều đều "gần đúng", và không kịch bản nào chạy đúng vào mốc.
    """
    decision = evaluate(
        make_request(battery_state=BatteryState(soc_pct=19.0, data_age_seconds=10.0))
    )
    assert decision.action.kind is ActionKind.SUGGEST_ECO


# ── Bước 2 / AC-02 · Session History ──────────────────────────────────────


def test_stays_quiet_when_a_recommendation_is_already_outstanding() -> None:
    """`AC-02` — một đề cử thứ hai là hai lời mời cạnh tranh cho một quyết định."""
    decision = evaluate(make_request(), SessionHistoryFacts(duplicate_candidate=True))
    assert decision.reason_code == SilenceReason.DUPLICATE_CANDIDATE.value


def test_fails_closed_when_session_history_cannot_be_read() -> None:
    """`ba.md` §6 để trống, nên đây là chỗ lựa chọn được ghi lại.

    `NFR-04` đòi 100% chính xác trong việc **không** tạo Candidate khi điều kiện
    trùng lặp đang đúng. Một phép kiểm chưa chạy không xác lập được rằng nó
    không đúng, nên im lặng là câu trả lời duy nhất giữ được lời cam kết ấy.
    """
    decision = evaluate(make_request(), SessionHistoryFacts(available=False))
    assert decision.reason_code == SilenceReason.SESSION_HISTORY_UNAVAILABLE.value


def test_speaks_when_history_is_readable_and_nothing_is_outstanding() -> None:
    decision = evaluate(make_request(), SessionHistoryFacts())
    assert decision.action.kind is ActionKind.SUGGEST_ECO


# ── Bước 3 / Bước 4 · what is actually shown ──────────────────────────────


def test_the_line_matches_the_brief_word_for_word() -> None:
    """`Bước 3` *Nội dung khuyến nghị* và `AC-01` trích cùng một câu.

    So nguyên văn chứ không so từng mảnh: `AC-01` đòi "đúng nội dung", và một
    bài chỉ kiểm ba từ khoá sẽ xanh trước một câu bị viết lại.
    """
    decision = evaluate(
        make_request(battery_state=BatteryState(soc_pct=20.0, data_age_seconds=1.0))
    )
    assert decision.action.message == (
        "Pin còn 20%. Chuyển sang Eco Mode có thể giúp tiết kiệm pin hơn. "
        "Bạn có đồng ý chuyển không?"
    )


def test_the_percentage_reads_as_a_whole_number() -> None:
    """"Pin còn 19%", không phải "Pin còn 19.0%"."""
    decision = evaluate(
        make_request(battery_state=BatteryState(soc_pct=19.4, data_age_seconds=1.0))
    )
    assert "19%" in decision.action.message
    assert "19.4" not in decision.action.message


def test_the_card_is_short_enough_for_a_glance() -> None:
    decision = evaluate(make_request())
    assert len(decision.action.message) <= MAX_MESSAGE_LENGTH


def test_there_are_exactly_two_choices_and_they_read_as_the_brief_writes_them() -> None:
    """`Bước 4` — "Đồng ý" và "Không đồng ý".

    Không phải "Bỏ qua": nhãn ấy thuộc về một luồng có hoãn lại, và brief này
    không có. Một nút nói khác điều tài liệu nói là một khác biệt không ai chọn.
    """
    decision = evaluate(make_request())
    assert decision.action.choices == (copy.CHOICE_ACCEPT, copy.CHOICE_DECLINE)
    assert decision.action.choices == ("Đồng ý", "Không đồng ý")


# ── BA-03 · shown, and not operable ───────────────────────────────────────


def test_nothing_asks_the_vehicle_to_do_anything() -> None:
    """`ba.md` §Phạm vi loại thực thi ECU ra ngoài.

    `Action` không còn trường nào mang được một lệnh, nên bài này đo ở tầng
    hình dạng: nếu ai đó thêm lại `command`, nó đỏ trước khi một lệnh kịp rời
    hệ thống.
    """
    decision = evaluate(make_request())
    assert not hasattr(decision.action, "command")
    assert not hasattr(decision.action, "ack_timeout_s")
    assert not hasattr(decision.action, "response_window_s")


def test_the_buttons_are_declared_non_interactive() -> None:
    """`BA-03` — hai nút có mặt nhưng không ấn được.

    Khai ở backend chứ không để màn hình tự biết: đó là điều `ba.md` quy định,
    không phải một lựa chọn trình bày.
    """
    result = service.public_result(evaluate(make_request()))
    assert result["resolvedPlan"]["choicesInteractive"] is False


# ── every silence is accountable ──────────────────────────────────────────


def test_every_silence_carries_a_reason_and_a_stage() -> None:
    """`NFR-04` — một cam kết về độ chính xác mà không truy vết được thì không
    phải một cam kết.

    Không có dòng này thì "đã cân nhắc và chọn không nói" và "hỏng nên không có
    gì xảy ra" cho ra cùng một quan sát.
    """
    silences = [
        evaluate(make_request(battery_state=BatteryState(soc_pct=25.0, data_age_seconds=1.0))),
        evaluate(make_request(vehicle_state=VehicleState(drive_mode="ECO"))),
        evaluate(make_request(connectivity_state=ConnectivityState(online=False))),
        evaluate(make_request(settings=Settings())),
        evaluate(make_request(battery_state=BatteryState(soc_pct=19.0, data_age_seconds=99.0))),
        evaluate(make_request(), SessionHistoryFacts(duplicate_candidate=True)),
        evaluate(make_request(), SessionHistoryFacts(available=False)),
    ]
    assert len(silences) == len(SilenceReason)
    assert {decision.reason_code for decision in silences} == {
        reason.value for reason in SilenceReason
    }
    for decision in silences:
        assert not decision.acted
        assert decision.reason_vi
        assert decision.stage


# ── RuleOverrides · bounds reject rather than clamp ───────────────────────


def test_a_value_outside_a_bound_is_rejected_not_clamped() -> None:
    """Một lần kẹp giá trị nghĩa là hệ thống chạy trên một con số không ai chọn
    và không gì nói ra điều đó."""
    with pytest.raises(ValidationError):
        RuleOverrides(soft_recommendation_soc_pct=25.0)
    with pytest.raises(ValidationError):
        RuleOverrides(soc_max_age_seconds=60.0)


def test_a_bound_only_opens_towards_staying_quieter() -> None:
    """Ngưỡng chỉ được hạ, trần độ tươi chỉ được siết.

    Chiều của mỗi biên không tuỳ tiện: nó mở về phía tính năng nói ít hơn và
    đóng về phía nó cắt ngang dễ hơn mức brief cho phép.
    """
    assert RuleOverrides(soft_recommendation_soc_pct=15.0).soft_recommendation_soc_pct == 15.0
    assert RuleOverrides(soc_max_age_seconds=5.0).soc_max_age_seconds == 5.0


def test_an_override_applies_to_the_whole_evaluation_at_once() -> None:
    request = make_request(rule_overrides=RuleOverrides(soft_recommendation_soc_pct=15.0))
    assert evaluate(request).reason_code == SilenceReason.ABOVE_THRESHOLD.value
    assert service.resolve_thresholds(request.rule_overrides).soft_soc_pct == 15.0


# ── determinism and the wire shape ────────────────────────────────────────


def test_the_same_inputs_always_give_the_same_decision() -> None:
    request = make_request()
    first, second = evaluate(request), evaluate(request)
    assert first == second


def test_the_wire_shape_is_camel_case() -> None:
    """Nền tảng và trình duyệt nói camelCase; Python nói snake_case.

    Biên nằm ở `FeatureModel`, và bài này là chỗ nó được ghim — một alias hỏng
    làm mọi request thật bị từ chối trong khi mọi test dựng model bằng tay vẫn
    xanh.
    """
    request = EvaluateRequest.model_validate(
        {
            "batteryState": {"socPct": 19.0, "dataAgeSeconds": 1.0},
            "vehicleState": {"driveMode": "NORMAL"},
            "connectivityState": {"online": True},
            "settings": {"batteryStateReliable": True, "vehicleStateReliable": True},
        }
    )
    assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


def test_an_unknown_field_is_rejected_rather_than_ignored() -> None:
    """`extra="forbid"` — một trường lạ là một hiểu nhầm, không phải nhiễu.

    Nó cũng là lý do `service.py` không cần mã `invalid_payload`: một request
    méo không bao giờ tới được tầng luật.
    """
    with pytest.raises(ValidationError):
        EvaluateRequest.model_validate(
            {
                "batteryState": {"socPct": 19.0},
                "vehicleState": {"driveMode": "NORMAL"},
                "navigationState": {"active": True},
            }
        )


# ── public_result · the shape the platform filters ────────────────────────


def test_public_result_names_the_action_when_it_acted() -> None:
    result = service.public_result(evaluate(make_request()))
    assert result["final"] is True
    assert result["recommendedActions"] == [{"target": "driving_mode", "targetState": "ECO"}]
    assert result["eventCode"] == "battery_low_eco_suggestion"


def test_public_result_recommends_nothing_when_silent() -> None:
    result = service.public_result(
        evaluate(make_request(battery_state=BatteryState(soc_pct=25.0, data_age_seconds=1.0)))
    )
    assert result["final"] is False
    assert result["recommendedActions"] == []
    assert result["feedback"]["reasonCode"] == SilenceReason.ABOVE_THRESHOLD.value


def test_audit_context_reports_only_domains_this_feature_reads() -> None:
    """Năm trường của gói rộng hơn xuống hai.

    `vehicleState`, `assistantMode` và `audioState` đọc những miền
    `schemas.py` không còn khai — giữ chúng lại sẽ là ghi vào bản truy vết một
    giá trị tính năng chưa từng nhận.
    """
    assert service.audit_context(make_request()) == {"socPct": 19.0, "driveMode": "NORMAL"}