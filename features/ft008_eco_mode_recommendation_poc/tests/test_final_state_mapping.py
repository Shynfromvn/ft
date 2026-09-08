"""This feature's four words map into the platform's eight endings, totally.

The platform requires exactly one property of a feature's mapping: that it be
total. This is where that requirement goes red — when somebody adds a seventh
`RecordKind` and does not decide how it ends.
"""

from __future__ import annotations

import pytest

from features.ft007_battery_status_recommendation.backend.memory import (
    RecordKind,
    final_state_of_record,
)
from pa.kernel.candidates.outcomes import FinalState

ALL_KINDS = [
    value
    for name, value in vars(RecordKind).items()
    if not name.startswith("_") and isinstance(value, str)
]


def test_the_five_kinds_are_discovered_not_listed() -> None:
    """Guards the parametrisation below: a sixth kind must reach the test.

    Đã làm đúng việc của nó ở P39: `SNOOZED` được thêm và bài này đỏ ngay, nên
    loại mới không lặng lẽ đi vào mà không có ai kiểm kết cục của nó.
    """
    assert len(ALL_KINDS) == 5


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_every_record_kind_has_exactly_one_ending(kind: str) -> None:
    assert isinstance(final_state_of_record(kind), FinalState)


def test_an_unmapped_kind_raises_rather_than_guessing() -> None:
    with pytest.raises(ValueError, match="chưa có kết cục"):
        final_state_of_record("something_nobody_declared")


def test_silence_and_refusal_stay_apart_where_ba_23_needs_them() -> None:
    """The two words differ even though two of the endings coincide.

    `BA-23` reads `RecordKind`, not `FinalState` — which is why collapsing
    `NO_ANSWER` and `REJECTED` into one ending costs nothing, and collapsing
    them into one *kind* would cost the requirement.
    """
    assert RecordKind.NO_ANSWER != RecordKind.REJECTED
    assert final_state_of_record(RecordKind.REJECTED) is FinalState.REJECTED
    assert final_state_of_record(RecordKind.NO_ANSWER) is FinalState.IGNORED


def test_accepting_is_acted_not_completed() -> None:
    """`AC-09`: completion waits for the vehicle, and this feature never sees it."""
    assert final_state_of_record(RecordKind.ACCEPTED) is FinalState.ACTED


def test_a_postponement_is_not_a_refusal() -> None:
    """`AC-14` liệt ba kết cục, `BR-10` gắn hệ quả khác nhau cho hai trong ba.

    Trước P39 nút *"Để sau"* gửi `reject`, nên một tài xế xin nhắc lại sau bị
    ghi là đã nói không — và `FinalState.SNOOZED` có tên trong nền tảng mà không
    đường nào sinh ra nó.
    """
    # Hai loại, hai kết cục. Không khẳng định `SNOOZED is not REJECTED` — mypy
    # chỉ ra đó là một phép so hai literal khác nhau, tức luôn đúng và không đo
    # gì cả. Thứ đáng đo là **ánh xạ**, và nó ở hai dòng dưới.
    assert final_state_of_record(RecordKind.SNOOZED) is FinalState.SNOOZED
    assert final_state_of_record(RecordKind.REJECTED) is FinalState.REJECTED
