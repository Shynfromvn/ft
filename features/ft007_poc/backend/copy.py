"""Everything the driver hears or reads. Deterministic, by decision.

ADR-0008: no model generates this. `QC-06.2` checks the *content* of the eco
suggestion — three components in order, inside a few seconds to read — and a
generated sentence turns that from an automatic check into a manual one. It
also makes the demo able to say something wrong in front of a vendor.

**Two channels, written separately, never derived from each other.**

| | `voice_line` | `message` |
|---|---|---|
| Reaches the driver by | being read aloud | being glanced at |
| Written for | someone with both hands on the wheel | someone stopped at a light |

Deriving one from the other — truncating the spoken line into the card, say —
produces a card that reads like a cut-off sentence, and the moment either
constraint changes the other silently breaks.

`DEBT-020`: this file used to also carry an emergency flow (critical battery,
forced Turtle Mode), a three-refusal throttle, an end-of-trip reminder, and a
range estimate on confirmation — none of which `ba.md`'s UC-01 has. Removed
rather than kept unused, so a reader does not have to work out which lines are
live.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "CHARS_PER_SECOND",
    "MAX_MESSAGE_LENGTH",
    "Spoken",
    "eco_confirmed",
    "eco_mode_change_failed",
    "eco_refused",
    "eco_snoozed",
    "eco_suggestion",
    "reading_seconds",
]

#: Vietnamese TTS at a normal rate — used by the test to measure a line's
#: length rather than trusting the wording.
CHARS_PER_SECOND: Final = 16.0
#: A glance, not a paragraph — the card's ceiling.
MAX_MESSAGE_LENGTH: Final = 120


@dataclass(frozen=True, slots=True)
class Spoken:
    """The two channels of one utterance."""

    voice_line: str
    message: str

    @property
    def reading_seconds(self) -> float:
        return reading_seconds(self.voice_line)


def reading_seconds(text: str) -> float:
    """How long a line takes to read aloud. Used by the test, not guessed at."""
    return round(len(text) / CHARS_PER_SECOND, 2)


def _percent(value: float) -> str:
    """Whole numbers read better aloud: "19%", not "19.0%"."""
    return f"{value:.0f}%"


def eco_suggestion(soc_pct: float) -> Spoken:
    """`UI/UX 9.1-1` of `ba.md`, word for word.

    "Pin còn 20%. Chuyển sang Eco Mode có thể giúp tiết kiệm pin hơn. Bạn
    muốn chuyển không?" — three components in order: the fact, the proposal
    with its benefit, and a question that waits rather than announces.
    """
    return Spoken(
        voice_line=(
            f"Pin còn {_percent(soc_pct)}. Chuyển sang Eco Mode có thể giúp "
            "tiết kiệm pin hơn. Bạn muốn chuyển không?"
        ),
        message=f"Pin còn {_percent(soc_pct)} · Chuyển sang Eco Mode?",
    )


def eco_confirmed() -> Spoken:
    """`UI/UX 9.1-3` — said **only** after the mode change was actually observed.

    Hearing "switched successfully" and then seeing the old mode on the dash
    costs trust in the whole assistant, not just this feature, and it costs it
    permanently (`BR-08`). So this sentence has exactly one caller, and that
    caller has already read the drive mode back.
    """
    return Spoken(voice_line="Đã chuyển sang Eco Mode.", message="Đã chuyển sang Eco Mode.")


def eco_refused() -> Spoken:
    """`AC-14` — the interaction ends, the current mode stays.

    No spoken line: `ba.md` does not mandate one for a refusal, and `BR-10`
    forbids anything that reads like the assistant will now speak less often.
    A driver who said no gets silence, not a promise about the future.
    """
    return Spoken(voice_line="", message="Đã bỏ qua.")


def eco_snoozed() -> Spoken:
    """`AC-14` — *"để sau"*, và chỉ vậy thôi.

    Cũng không có câu nói, cùng lý do `eco_refused` không có: `BR-10` cấm mọi
    thứ nghe như trợ lý sẽ nói ít đi. Nhưng câu hiển thị **khác**, và khác biệt
    ấy là điều duy nhất tài xế nhìn thấy giữa hai kết cục: *"đã bỏ qua"* nói
    chuyện đã xong, *"để sau nhé"* nói chuyện chưa xong.
    """
    return Spoken(voice_line="", message="Để sau nhé.")


def eco_mode_change_failed() -> Spoken:
    """`UI/UX 9.1-4` / `AC-10` — the vehicle refused or did not comply.

    "Mình chưa chuyển được sang Eco Mode. Bạn thử lại khi an toàn nhé." — STATUS
    Error, never a false Success (`BR-08`).
    """
    return Spoken(
        voice_line="Mình chưa chuyển được sang Eco Mode. Bạn thử lại khi an toàn nhé.",
        message="Chưa chuyển được sang Eco Mode.",
    )
