"""Thresholds and the silence rules — the values, and what checks them.

Thresholds are **Python constants with types and tests**, not YAML. A string in
a configuration file has nothing checking it still means what it meant; a
constant here is read by the same test that asserts the behaviour it produces.

Every number below traces to a decision. Where a company document fixed it, that
is said; where nothing fixed it, that is said too — and said loudly, because a
number with no source looks exactly like a number somebody approved.

**Scope.** This package is a **narrower** feature than
`ft007_battery_status_recommendation`, not a variant of it. Its `ba.md` (source
requirement UC-01 v0.1, 3 Sep 2026) puts Navigation, Safety/ADAS, calls,
Assistant Mode, user response and ECU execution out of scope, so the constants
and reason codes those gates needed are **gone rather than kept unread** — a
caller cannot set a value that changes nothing. If a concept from the wider
document (proximity suppression, the response window, the acknowledgement
ceiling, the confidence floor) reappears here, that is a regression.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

__all__ = [
    "EVENT_CODE",
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
# These three strings live here and **only** here. The platform is not allowed
# to know that `driving_mode` exists (invariant 1), so the catalogue belongs to
# whichever feature emits one.
#
# All three come from `ba.md` `Bước 3`, which lists what a Candidate carries.
# Two of that list's five entries are **not** here on purpose: *Loại sự kiện*
# ("gửi khuyến nghị chủ động") is the platform's own classification of a
# proactive recommendation, and *Nguồn gửi* (S5) is which service emitted it —
# neither is this feature's vocabulary to define.

#: `Hành động khuyến nghị` — what this recommendation asks the vehicle to
#: change. A statement of intent, never an instruction: `ba.md` §Phạm vi puts
#: ECU execution out of scope, so nothing downstream of this feature may act
#: on it.
TARGET_DRIVING_MODE: Final = "driving_mode"
#: What it asks it to change to.
TARGET_STATE_ECO: Final = "ECO"
#: `Mã sự kiện` — names the kind of recommendation on the wire. Distinct from
#: the internal `ActionKind.SUGGEST_ECO`: one is our enum, the other is a string
#: the other side of a contract reads.
EVENT_CODE: Final = "battery_low_eco_suggestion"


# ── inherited from the company document ───────────────────────────────────

#: Speak when charge falls to this mark or below. `BR-01` and `AC-01` both read
#: as a closed bound ("SoC ≤ 20%"): `service.py` compares with `>`, not `>=`,
#: so exactly 20.0 is still eligible. Reading it as an open bound would make the
#: system silent at precisely the number the document names and the spoken line
#: reads out.
SOFT_RECOMMENDATION_SOC_PCT: Final = 20.0

#: How old a battery reading may be and still be worth speaking on.
#:
#: **This number has no source in `ba.md`, and that is a defect in the brief,
#: not a gap to be filled here.** `Preconditions §2` requires SoC and drive-mode
#: to satisfy "chính sách độ tươi được phê duyệt quy định trong bảng Yêu cầu phi
#: chức năng" — but the NFR table holds no such policy. Its only data figure is
#: `NFR-01`, *"S5 lấy dữ liệu SoC: 3 phút một lần"*, which is a **polling
#: cadence**, not an age ceiling: how often a reading is fetched says nothing
#: about how old one may be before it stops being actionable.
#:
#: 10.0 is inherited from the source requirement the POC was cut down from. It
#: is kept because the tighter of two candidate numbers is the safe direction —
#: a shorter ceiling refuses more readings, and refusing to speak is recoverable
#: in a way that speaking on a stale number is not. It is **not** kept because
#: anyone approved it.
#:
#: Ask BA, then write the answer into `ba.md` and let this line follow. Do not
#: settle it here: a number settled in code is a number the brief will never
#: learn about.
SOC_MAX_AGE_SECONDS: Final = 10.0


@dataclass(frozen=True, slots=True)
class Thresholds:
    """The values this evaluation runs on, after any overrides are applied.

    Resolved once and passed down, so every rule in a single evaluation sees the
    same numbers. Reading the constants directly inside each rule would let an
    override apply to some of them and not others, and the resulting behaviour
    would be a mixture nobody specified.
    """

    soft_soc_pct: float = SOFT_RECOMMENDATION_SOC_PCT
    soc_max_age_seconds: float = SOC_MAX_AGE_SECONDS


class SilenceReason(StrEnum):
    """Reason codes a dashboard can group silences by.

    Codes rather than sentences because "every silence for reason X this month"
    should be a query. The Vietnamese wording lives beside them in
    `SILENCE_REASONS`.

    Declared in the order `service.py` checks them, so the enum reads as the
    decision procedure it belongs to.

    Seven, where the wider feature has nineteen. Twelve went out with the gates
    they belonged to: `assistant_mode_not_allowed`, `assistant_unavailable`,
    `system_state_not_normal`, `call_active`, `safety_preempted`,
    `navigation_unavailable`, `navigation_stale`, `destination_type_unknown`,
    `proximity_suppressed`, and the four `memory_*` codes — see
    `SESSION_HISTORY_UNAVAILABLE` for what replaced the last group.
    """

    #: Charge is simply above the mark. The ordinary case, and still recorded,
    #: because a QA report needs to distinguish it from a rule that suppressed.
    ABOVE_THRESHOLD = "above_threshold"
    #: `BR-01`/`AC-01` — the vehicle is already in Eco Mode. Proposing what the
    #: driver has already done is the clearest evidence an assistant is not
    #: paying attention.
    ALREADY_IN_ECO_MODE = "already_in_eco_mode"
    #: `Preconditions §2` — the vehicle cannot reach the cloud.
    OFFLINE = "offline"
    #: `Preconditions §2` — a required field is missing.
    DATA_MISSING = "data_missing"
    #: `Preconditions §2` — the battery reading is older than the freshness
    #: policy allows. See `SOC_MAX_AGE_SECONDS` for what that policy currently
    #: is and why that is unsatisfactory.
    DATA_STALE = "data_stale"
    #: `Bước 2`/`AC-02` — Session History shows an Eco recommendation for this
    #: driver already awaiting a response or being processed. A second one would
    #: be two competing offers for one decision.
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    #: Session History could not be read, so `AC-02` cannot be evaluated.
    #:
    #: **`ba.md` does not cover this case.** §6 Luồng ngoại lệ and §7 Luồng thay
    #: thế are both empty headings, so the document says nothing about what
    #: happens when the duplicate check is unanswerable. Failing closed is the
    #: reading that keeps `NFR-04` true — it demands 100% accuracy in *not*
    #: creating a Candidate when the duplicate condition holds, and a check that
    #: did not run cannot establish that it does not.
    #:
    #: One code where the wider feature has four (`memory_timeout`,
    #: `memory_unavailable`, `memory_inconsistent`, `memory_expired`). Those four
    #: are `E02`'s own vocabulary and `E02` does not exist here; inventing a
    #: four-way split with no document behind it would be this file deciding
    #: what the brief should have said. Ask BA to fill §6, then split if the
    #: answer distinguishes cases.
    SESSION_HISTORY_UNAVAILABLE = "session_history_unavailable"


#: What the driver would be told if they asked why nothing was said. The demo
#: dashboard always shows it; the driver sees it only on asking. Two audiences,
#: two levels of visibility.
SILENCE_REASONS: Final[dict[SilenceReason, str]] = {
    SilenceReason.ABOVE_THRESHOLD: "Mức pin còn trên ngưỡng",
    SilenceReason.ALREADY_IN_ECO_MODE: "Xe đã ở Eco Mode",
    SilenceReason.OFFLINE: "Xe đang mất kết nối tới cloud",
    SilenceReason.DATA_MISSING: "Thiếu dữ liệu bắt buộc",
    SilenceReason.DATA_STALE: "Dữ liệu pin không đủ mới",
    SilenceReason.DUPLICATE_CANDIDATE: "Đã có một khuyến nghị Eco đang chờ xử lý",
    SilenceReason.SESSION_HISTORY_UNAVAILABLE: "Không đọc được Session History",
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
