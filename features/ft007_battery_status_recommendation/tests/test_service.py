"""Business rules, one test per requirement, naming the `ba.md` id it covers.

`DEBT-020`: this file used to also cover an emergency flow, a re-arm
hysteresis, a two-tier cooldown, a three-refusal throttle, a demanding-driving
defer, a Do Not Disturb switch and an end-of-trip reminder — none of which the
current, company-approved `ba.md` has, and `BR-10` forbids the cooldown
outright. Those tests are gone with the code, not kept red.

Every test uses a `FrozenClock`. Nothing here waits for a response window or
an acknowledgement ceiling in real time.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from features.ft007_battery_status_recommendation.backend import copy, service
from features.ft007_battery_status_recommendation.backend.rules import SilenceReason
from features.ft007_battery_status_recommendation.backend.schemas import (
    BatteryState,
    ConnectivityState,
    EvaluateRequest,
    InteractionState,
    NavigationState,
    RespondRequest,
    RuleOverrides,
    SafetyState,
    Settings,
    VehicleState,
)
from features.ft007_battery_status_recommendation.backend.service import (
    ActionKind,
    MemoryFacts,
)
from pa.kernel.core.clock import FrozenClock

NOW = datetime(2026, 8, 25, 9, 0, tzinfo=UTC)


def make_request(**overrides: object) -> EvaluateRequest:
    """A driving car with trustworthy data — the case where speaking is allowed.

    Everything else in this file is a departure from this baseline, which makes
    each test's one difference the thing it is about.
    """
    base: dict[str, object] = {
        "profile_id": "p-1",
        "battery_state": BatteryState(soc_pct=19.0, data_age_seconds=1.0),
        "vehicle_state": VehicleState(
            vehicle_in_drive=True,
            gear_state="D",
            drive_mode="NORMAL",
            system_state="NORMAL",
        ),
        "navigation_state": NavigationState(
            active=True,
            nearest_charger_km=None,
            destination_type="OTHER",
            data_age_seconds=10.0,
        ),
        "interaction_state": InteractionState(
            assistant_available=True, assistant_mode="BALANCED", inference_confidence=0.95
        ),
        "connectivity_state": ConnectivityState(online=True),
        "settings": Settings(
            battery_state_reliable=True,
            vehicle_state_reliable=True,
            navigation_state_reliable=True,
            interaction_state_reliable=True,
        ),
    }
    base.update(overrides)
    return EvaluateRequest(**base)


def evaluate(request: EvaluateRequest, facts: MemoryFacts | None = None) -> service.Decision:
    return service.evaluate(request, clock=FrozenClock(NOW), facts=facts)


# ── BR-01 · the soft threshold ─────────────────────────────────────────────


def test_speaks_below_the_mark() -> None:
    assert evaluate(make_request()).action.kind is ActionKind.SUGGEST_ECO
    assert (
        evaluate(
            make_request(battery_state=BatteryState(soc_pct=19.9, data_age_seconds=1))
        ).action.kind
        is ActionKind.SUGGEST_ECO
    )


def test_speaks_at_exactly_the_mark() -> None:
    """`BR-01` reads as a closed bound: "SoC chạm mức 20%" includes 20.0 itself.

    Regression for the off-by-one this plan (P25 T3-T5) fixed: the comparison
    used to be `>=`, which made exactly 20.0% silent.
    """
    decision = evaluate(make_request(battery_state=BatteryState(soc_pct=20.0, data_age_seconds=1)))
    assert decision.action.kind is ActionKind.SUGGEST_ECO


def test_stays_quiet_above_the_mark() -> None:
    decision = evaluate(make_request(battery_state=BatteryState(soc_pct=20.01, data_age_seconds=1)))
    assert decision.action.kind is ActionKind.NONE
    assert decision.reason_code == SilenceReason.ABOVE_THRESHOLD.value


# ── Preconditions §2 · Parked and Driving are both valid ──────────────────


def test_still_speaks_when_the_car_is_parked() -> None:
    """`ba.md` Preconditions §2: "Trạng thái xe: Parked hoặc Driving" — both.

    Regression for the gate this plan (P25 T3-T5) removed: a parked vehicle
    used to be silenced with `not_driving`, a reason code `ba.md` does not
    have at all.
    """
    request = make_request(
        vehicle_state=VehicleState(
            vehicle_in_drive=False, gear_state="P", drive_mode="NORMAL", system_state="NORMAL"
        )
    )
    assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


# ── what is actually said ──────────────────────────────────────────────────


def test_the_line_has_three_components_in_order() -> None:
    """`UI/UX 9.1-1` — charge, then the proposal, then a question that waits."""
    line = evaluate(make_request()).action.voice_line
    charge = line.index("19%")
    proposal = line.index("Eco Mode")
    question = line.index("?")
    assert charge < proposal < question


def test_the_card_is_short_enough_for_a_glance() -> None:
    message = evaluate(make_request()).action.message
    assert len(message) <= copy.MAX_MESSAGE_LENGTH


def test_the_two_channels_are_written_separately() -> None:
    """ADR-0008 — the card is not a truncation of the spoken line."""
    action = evaluate(make_request()).action
    assert action.message != action.voice_line


# ── the offer ───────────────────────────────────────────────────────────────


def test_the_voice_window_is_six_seconds() -> None:
    assert evaluate(make_request()).action.response_window_s == 6


def test_there_are_exactly_two_choices() -> None:
    assert len(evaluate(make_request()).action.choices) == 2


# ── BR-08 / AC-09 / AC-10 · claim success only after observing it ─────────


def test_no_success_claimed_while_the_mode_has_not_changed() -> None:
    """`BR-08`/`AC-10` — accepting is not enough on its own.

    Hearing "switched successfully" and then seeing the old mode on the dash
    costs trust in the whole assistant, permanently.
    """
    decision = service.respond(
        RespondRequest(candidate_id="r-1", outcome="accept", channel="voice"),
        clock=FrozenClock(NOW),
        mode_changed=False,
    )
    assert decision.action.kind is ActionKind.EXECUTION_FAILED
    assert decision.reason_code == "execution_failed"
    assert "đã chuyển" not in decision.action.voice_line.lower()


def test_success_is_claimed_once_the_mode_really_changed() -> None:
    decision = service.respond(
        RespondRequest(candidate_id="r-1", outcome="accept", channel="voice"),
        clock=FrozenClock(NOW),
        mode_changed=True,
    )
    assert decision.action.voice_line == "Đã chuyển sang Eco Mode."


def test_the_acknowledgement_ceiling_is_three_seconds() -> None:
    assert evaluate(make_request()).action.ack_timeout_s == 3.0


# ── AC-14 · refusing is not the same as not answering ─────────────────────


def test_refusing_and_not_answering_are_different_outcomes() -> None:
    """`AC-14` — a driver watching the road who said nothing has not refused.

    `BR-10`: neither outcome may read as a promise to speak less often.
    """
    clock = FrozenClock(NOW)
    rejected = service.respond(RespondRequest(candidate_id="r", outcome="reject"), clock=clock)
    ignored = service.respond(RespondRequest(candidate_id="r", outcome="timeout"), clock=clock)

    assert rejected.reason_code == "rejected"
    assert ignored.reason_code == "ignored"
    assert not rejected.action.voice_line
    assert not ignored.action.voice_line


# ── silence rules that remain ──────────────────────────────────────────────


def test_stays_quiet_when_already_in_eco() -> None:
    """`BR-01` — proposing what the driver already did is the clearest evidence
    the assistant is not watching them."""
    request = make_request(
        vehicle_state=VehicleState(vehicle_in_drive=True, drive_mode="ECO", system_state="NORMAL")
    )
    decision = evaluate(request)
    assert decision.action.kind is ActionKind.NONE
    assert decision.reason_code == SilenceReason.ALREADY_IN_ECO_MODE.value


def test_stays_quiet_on_stale_data() -> None:
    request = make_request(battery_state=BatteryState(soc_pct=19.0, data_age_seconds=60.0))
    decision = evaluate(request)
    assert decision.reason_code == SilenceReason.DATA_STALE.value
    assert decision.stage == "vehicle_state"


def test_stays_quiet_when_the_battery_domain_never_reported() -> None:
    """`E01` — `battery_state_reliable=False` means the domain never arrived,
    which is `data_missing`, not `data_stale`."""
    request = make_request(settings=Settings(battery_state_reliable=False))
    assert evaluate(request).reason_code == SilenceReason.DATA_MISSING.value


def test_stays_quiet_below_the_confidence_floor() -> None:
    request = make_request(
        interaction_state=InteractionState(
            assistant_available=True, assistant_mode="BALANCED", inference_confidence=0.5
        )
    )
    assert evaluate(request).reason_code == SilenceReason.DATA_STALE.value


def test_stays_quiet_when_assistant_mode_does_not_allow_it() -> None:
    """`E04`/`BR-02` — only Balanced or Proactive may self-initiate this."""
    for mode in ("QUIET", "UNKNOWN"):
        request = make_request(
            interaction_state=InteractionState(
                assistant_available=True, assistant_mode=mode, inference_confidence=0.95
            )
        )
        assert evaluate(request).reason_code == SilenceReason.ASSISTANT_MODE_NOT_ALLOWED.value


def test_speaks_in_balanced_or_proactive_mode() -> None:
    for mode in ("BALANCED", "PROACTIVE"):
        request = make_request(
            interaction_state=InteractionState(
                assistant_available=True, assistant_mode=mode, inference_confidence=0.95
            )
        )
        assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


def test_stays_quiet_when_the_assistant_is_unavailable() -> None:
    """`Bước 5` Eligibility gates — ViTa must be Available."""
    request = make_request(
        interaction_state=InteractionState(
            assistant_available=False, assistant_mode="BALANCED", inference_confidence=0.95
        )
    )
    assert evaluate(request).reason_code == SilenceReason.ASSISTANT_UNAVAILABLE.value


def test_stays_quiet_when_system_state_is_not_normal() -> None:
    """`Bước 5` Eligibility gates — "System State = Normal"."""
    for state in ("DEGRADED", "UNKNOWN"):
        request = make_request(
            vehicle_state=VehicleState(
                vehicle_in_drive=True, drive_mode="NORMAL", system_state=state
            )
        )
        assert evaluate(request).reason_code == SilenceReason.SYSTEM_STATE_NOT_NORMAL.value


def test_stays_quiet_when_offline() -> None:
    """`Preconditions §2` — "Chỉ hoạt động khi Online"."""
    request = make_request(connectivity_state=ConnectivityState(online=False))
    assert evaluate(request).reason_code == SilenceReason.OFFLINE.value


def test_stays_quiet_when_a_call_is_active() -> None:
    """`E06`/`BR-06` — a call blocks Voice and Sound outright."""
    request = make_request(
        interaction_state=InteractionState(
            assistant_available=True,
            assistant_mode="BALANCED",
            call_active=True,
            inference_confidence=0.95,
        )
    )
    assert evaluate(request).reason_code == SilenceReason.CALL_ACTIVE.value


def test_stays_quiet_when_a_safety_warning_is_active() -> None:
    """`E05`/`BR-05` — the assistant yields, does not compete."""
    request = make_request(safety_state=SafetyState(alert_level="WARNING"))
    assert evaluate(request).reason_code == SilenceReason.SAFETY_PREEMPTED.value


def test_stays_quiet_when_a_safety_intervention_is_active() -> None:
    request = make_request(safety_state=SafetyState(alert_level="INTERVENTION"))
    assert evaluate(request).reason_code == SilenceReason.SAFETY_PREEMPTED.value


def test_stays_quiet_when_adas_intervenes() -> None:
    request = make_request(safety_state=SafetyState(adas_state="INTERVENTION"))
    assert evaluate(request).reason_code == SilenceReason.SAFETY_PREEMPTED.value


def test_speaks_when_safety_state_is_unknown() -> None:
    """`ADR-0029` — `UNKNOWN` is not itself a reason to yield.

    A vehicle that never reported this is not the same as one confirming a
    clear alert state, but no approved document lists "unknown safety state"
    as its own blocking reason (unlike Navigation's `E03`).
    """
    request = make_request(safety_state=SafetyState())
    assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


def test_stays_quiet_when_navigation_never_reported() -> None:
    """`E03` — fail closed. `ba.md` requires the opposite of what an earlier
    version of this code did with an unknown Navigation context."""
    request = make_request(
        settings=Settings(
            battery_state_reliable=True,
            vehicle_state_reliable=True,
            navigation_state_reliable=False,
            interaction_state_reliable=True,
        )
    )
    assert evaluate(request).reason_code == SilenceReason.NAVIGATION_UNAVAILABLE.value


def test_stays_quiet_when_navigation_is_stale() -> None:
    request = make_request(
        navigation_state=NavigationState(active=True, data_age_seconds=121.0)
    )
    assert evaluate(request).reason_code == SilenceReason.NAVIGATION_STALE.value


def test_stays_quiet_near_a_charging_station_it_knows_about() -> None:
    """`BR-09`/`AC-03` — Home or a suitable charging station, within 5 km."""
    request = make_request(
        navigation_state=NavigationState(
            active=True,
            nearest_charger_km=3.0,
            destination_type="CHARGING_STATION",
            data_age_seconds=10,
        )
    )
    decision = evaluate(request)
    assert decision.action.kind is ActionKind.NONE
    assert decision.reason_code == SilenceReason.PROXIMITY_SUPPRESSED.value


def test_stays_quiet_near_home() -> None:
    request = make_request(
        navigation_state=NavigationState(
            active=True,
            distance_to_destination_km=2.0,
            destination_type="HOME",
            data_age_seconds=10,
        )
    )
    assert evaluate(request).reason_code == SilenceReason.PROXIMITY_SUPPRESSED.value


def test_speaks_near_a_destination_that_is_not_home_or_a_charger() -> None:
    """`AC-04` — distance alone is never sufficient. A CoffeeShop 1 km away
    must not be silenced just because it happens to be close."""
    request = make_request(
        navigation_state=NavigationState(
            active=True,
            distance_to_destination_km=1.0,
            destination_type="OTHER",
            data_age_seconds=10,
        )
    )
    assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


def test_speaks_when_it_does_not_know_where_a_charger_is() -> None:
    """Navigation itself is reliable, fresh, and classified as "Other" — it
    simply has no charger or destination distance to report. That is not the
    same as Navigation being unavailable
    (`test_stays_quiet_when_navigation_never_reported`), so `E03` does not
    apply and there is nothing nearby to suppress on."""
    request = make_request(
        navigation_state=NavigationState(
            active=True,
            nearest_charger_km=None,
            distance_to_destination_km=None,
            destination_type="OTHER",
            data_age_seconds=10,
        )
    )
    assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


def test_stays_quiet_when_an_active_destination_cannot_be_classified() -> None:
    """`E03` — Navigation is active but never said what kind of place this is.

    Different from `test_speaks_when_it_does_not_know_where_a_charger_is`:
    there the destination type is known ("Other"), just not nearby. Here the
    type itself is missing, which `ba.md` treats as a Navigation failure.
    """
    request = make_request(
        navigation_state=NavigationState(
            active=True, destination_type="UNKNOWN", data_age_seconds=10
        )
    )
    assert evaluate(request).reason_code == SilenceReason.DESTINATION_TYPE_UNKNOWN.value


def test_speaks_when_navigation_is_simply_not_active() -> None:
    """No destination at all is not the same as an unclassifiable one — there
    is nothing to fail closed on."""
    request = make_request(
        navigation_state=NavigationState(
            active=False, destination_type="UNKNOWN", data_age_seconds=10
        )
    )
    assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


# ── E02 / BR-11 · S7 Shared Memory must answer validly (plan P28) ──────────


def test_stays_quiet_when_memory_times_out() -> None:
    decision = evaluate(
        make_request(),
        facts=MemoryFacts(available=False, error_reason=SilenceReason.MEMORY_TIMEOUT),
    )
    assert decision.action.kind is ActionKind.NONE
    assert decision.reason_code == SilenceReason.MEMORY_TIMEOUT.value


def test_stays_quiet_when_memory_is_unavailable() -> None:
    decision = evaluate(
        make_request(),
        facts=MemoryFacts(available=False, error_reason=SilenceReason.MEMORY_UNAVAILABLE),
    )
    assert decision.reason_code == SilenceReason.MEMORY_UNAVAILABLE.value


def test_stays_quiet_when_memory_answers_without_a_generation() -> None:
    decision = evaluate(
        make_request(),
        facts=MemoryFacts(available=False, error_reason=SilenceReason.MEMORY_INCONSISTENT),
    )
    assert decision.reason_code == SilenceReason.MEMORY_INCONSISTENT.value


def test_stays_quiet_when_memory_is_expired() -> None:
    """Fourth `E02` reason — P22 T12'. Content stale, not just late or absent."""
    decision = evaluate(
        make_request(),
        facts=MemoryFacts(available=False, error_reason=SilenceReason.MEMORY_EXPIRED),
    )
    assert decision.action.kind is ActionKind.NONE
    assert decision.reason_code == SilenceReason.MEMORY_EXPIRED.value


def test_unavailable_memory_with_no_reason_still_fails_closed() -> None:
    """Belt and braces: `available=False` alone is enough, even without a
    specific `error_reason` set — silence is the safe default, not a crash."""
    decision = evaluate(make_request(), facts=MemoryFacts(available=False))
    assert decision.action.kind is ActionKind.NONE
    assert decision.reason_code == SilenceReason.MEMORY_UNAVAILABLE.value


# ── Bước 5 Memory checks · a live Candidate is not doubled (plan P28) ──────


def test_stays_quiet_when_a_candidate_is_already_outstanding() -> None:
    decision = evaluate(make_request(), facts=MemoryFacts(duplicate_candidate=True))
    assert decision.action.kind is ActionKind.NONE
    assert decision.reason_code == SilenceReason.DUPLICATE_CANDIDATE.value


def test_speaks_normally_when_memory_is_available_and_not_duplicate() -> None:
    """The default `MemoryFacts()` — every test above this section already
    relies on this being the quiet, do-nothing-extra case."""
    decision = evaluate(make_request(), facts=MemoryFacts())
    assert decision.action.kind is ActionKind.SUGGEST_ECO


def test_every_silence_carries_a_reason_and_a_stage() -> None:
    """`BR-12` — without this, "considered and chose not to speak" and "broke,
    so nothing happened" produce the same observable: nothing."""
    cases = [
        evaluate(
            make_request(
                vehicle_state=VehicleState(
                    vehicle_in_drive=True, drive_mode="ECO", system_state="NORMAL"
                )
            )
        ),
        evaluate(make_request(battery_state=BatteryState(soc_pct=19, data_age_seconds=999))),
    ]
    for decision in cases:
        assert decision.action.kind is ActionKind.NONE
        assert decision.reason_code, "a silence with no code cannot be grouped"
        assert decision.reason_vi, "a silence with no wording cannot be explained"
        assert decision.stage in {
            "signal",
            "vehicle_state",
            "event",
            "distribution",
            "judgement",
            "expression",
            "action",
        }


# ── RuleOverrides · bounds reject rather than clamp ────────────────────────


def test_a_value_outside_a_bound_is_rejected_not_clamped() -> None:
    """Silently clamping means running on a number nobody chose."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RuleOverrides(soft_recommendation_soc_pct=45)
    with pytest.raises(ValidationError):
        RuleOverrides(min_inference_confidence=0.5)


def test_overrides_apply_to_the_whole_evaluation_at_once() -> None:
    """Resolved once and passed down, so no rule sees a different set."""
    request = make_request(
        battery_state=BatteryState(soc_pct=14.0, data_age_seconds=1),
        rule_overrides=RuleOverrides(soft_recommendation_soc_pct=15),
    )
    assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


def test_repeated_rejections_never_silence_a_later_crossing() -> None:
    """`BR-10`/`QC-28.1` — the sixth consecutive low-SoC crossing must still
    speak normally, with no automatic cooldown or throttle.

    There is no rejection count left anywhere to seed (`MemoryFacts` is
    empty) — evaluating the same request six times in a row is the proof.
    """
    request = make_request()
    for _ in range(6):
        assert evaluate(request, MemoryFacts()).action.kind is ActionKind.SUGGEST_ECO


# ── determinism ───────────────────────────────────────────────────────────


def test_the_same_inputs_always_give_the_same_decision() -> None:
    """`features/README.md` — the property the whole design rests on."""
    request = make_request()
    first = evaluate(request)
    second = evaluate(request)

    assert first.action == second.action
    assert first.reason_code == second.reason_code


def test_the_wire_shape_is_camel_case() -> None:
    """The alias path, which is the one the vehicle and the browser actually use."""
    request = EvaluateRequest.model_validate(
        {
            "profileId": "p-1",
            "batteryState": {"socPct": 19.0, "dataAgeSeconds": 1.0},
            "vehicleState": {
                "vehicleInDrive": True,
                "driveMode": "NORMAL",
                "systemState": "NORMAL",
            },
            "navigationState": {
                "active": True,
                "destinationType": "OTHER",
                "dataAgeSeconds": 10.0,
            },
            "interactionState": {
                "assistantAvailable": True,
                "assistantMode": "BALANCED",
                "inferenceConfidence": 0.95,
            },
            "connectivityState": {"online": True},
            "settings": {
                "batteryStateReliable": True,
                "vehicleStateReliable": True,
                "navigationStateReliable": True,
                "interactionStateReliable": True,
            },
        }
    )
    assert request.battery_state.soc_pct == 19.0
    assert evaluate(request).action.kind is ActionKind.SUGGEST_ECO


# ── public_result · confirmation contract (plan P26) ──────────────────────


def test_public_result_carries_a_confirmation_contract_when_acted() -> None:
    """`BR-07`/`BR-04` — present only when there is a command awaiting yes."""
    decision = evaluate(make_request())
    result = service.public_result(decision)
    assert result["confirmation"] == {
        "required": True,
        "voiceAllowed": True,
        "touchAllowedWhenParked": True,
        "windowSeconds": 6.0,
    }


def test_public_result_has_no_confirmation_when_silent() -> None:
    decision = evaluate(make_request(battery_state=BatteryState(soc_pct=21.0, data_age_seconds=1)))
    result = service.public_result(decision)
    assert result["confirmation"] is None


def test_public_result_has_no_confirmation_for_a_status_message() -> None:
    """`respond()`'s success line reuses `SUGGEST_ECO` but asks nothing."""
    decision = service.respond(
        RespondRequest(candidate_id="r-1", outcome="accept", channel="voice"),
        clock=FrozenClock(NOW),
        mode_changed=True,
    )
    result = service.public_result(decision)
    assert result["confirmation"] is None


def test_an_unknown_field_is_rejected_rather_than_ignored() -> None:
    """`extra="forbid"` — a misspelled field is a caller bug, not a default."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BatteryState.model_validate({"socPct": 50.0, "socPercent": 50.0})
