"""Everything the driver reads. Deterministic, by decision.

No model generates this. `AC-01` checks the **content** of the recommendation —
it names the sentence and requires that exact content — and a generated line
turns that from an automatic check into a manual one. It also makes the demo
able to say something wrong in front of a vendor.

**One channel, not two.** The wider feature
`ft007_battery_status_recommendation` writes `voiceLine` and `message`
separately, for someone with both hands on the wheel and someone stopped at a
light. This brief describes no spoken output at all: §9.1 Voice UX is an empty
heading, and `Bước 4` names exactly one delivery — *"hiển thị giao diện với câu
hỏi ... và các nút xác nhận cảm ứng"*. Writing a `voiceLine` nobody speaks
would be inventing a channel the document does not have.

**If BA says the POC does speak**, the restoration is not a rewrite: add a
`voice_line` field beside `text`, write it separately rather than deriving it
from `text`, and bring back the reading-rate constant that measured it.
Deriving one channel from the other — truncating the spoken line into the card
— produces a card that reads like a cut-off sentence, and the moment either
constraint changes the other silently breaks.

Four functions went out with the flows they served: `eco_confirmed`,
`eco_refused`, `eco_snoozed` and `eco_mode_change_failed`. All four say
something about what the driver answered or what the vehicle did, and §Phạm vi
puts user response, ECU execution and ECU confirmation out of scope. Removed
rather than kept unused, so a reader does not have to work out which lines are
live.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "CHOICE_ACCEPT",
    "CHOICE_DECLINE",
    "MAX_MESSAGE_LENGTH",
    "Displayed",
    "eco_suggestion",
]

#: A glance, not a paragraph — the card's ceiling. Read by the test that
#: measures the line rather than trusting the wording.
MAX_MESSAGE_LENGTH: Final = 160

#: The two confirmation buttons of `Bước 4`, word for word. They are rendered
#: **disabled** (`BA-03`) — the labels still live here because they are text the
#: driver reads, and this file owns every such string.
#:
#: `Không đồng ý`, not `Bỏ qua`: the wider feature offers a snooze, this brief
#: does not, and a button that says something other than what the document says
#: is a difference nobody chose.
CHOICE_ACCEPT: Final = "Đồng ý"
CHOICE_DECLINE: Final = "Không đồng ý"


@dataclass(frozen=True, slots=True)
class Displayed:
    """One utterance, on the one channel this feature has."""

    text: str

    @property
    def within_limit(self) -> bool:
        return len(self.text) <= MAX_MESSAGE_LENGTH


def eco_suggestion(soc_pct: float) -> Displayed:
    """`Bước 3` *Nội dung khuyến nghị* / `Bước 4` / `AC-01`, word for word.

    Three components in order: the fact, the proposal with its benefit, and a
    question that waits rather than announces.

    ── CHƯA CHỐT: con số trong câu ──────────────────────────────────────────
    `soc_pct` được nội suy vào câu, nên ở 19,4% tài xế đọc *"Pin còn 19%"*. Đó
    là cách gói gốc làm, và ở đó nó đúng: `ba.md` của gói gốc đặt câu này dưới
    cột **"Ví dụ (TTS)"** của bảng Voice UX — một ví dụ thì thay số được.

    Brief này thì khác. Câu xuất hiện hai lần và cả hai đều không phải ví dụ:
    `Bước 3` liệt nó là *Nội dung khuyến nghị* của Candidate, và `AC-01` đòi
    *"đúng nội dung"* rồi trích nguyên văn kèm con số 20%. Đọc chặt thì đây là
    một chuỗi cố định, và nội suy là sai; đọc thoáng thì 20% chỉ là giá trị
    tại ngưỡng.

    Giữ nội suy vì nói *"Pin còn 20%"* khi màn hình bên cạnh hiện 19% là một
    mâu thuẫn tài xế nhìn thấy ngay. Nhưng đây là một lựa chọn, không phải một
    điều tài liệu nói — hỏi BA, và nếu câu trả lời là chuỗi cố định thì bỏ tham
    số `soc_pct` đi thay vì để nó không được dùng.
    """
    return Displayed(
        text=(
            f"Pin còn {soc_pct:.0f}%. Chuyển sang Eco Mode có thể giúp "
            "tiết kiệm pin hơn. Bạn có đồng ý chuyển không?"
        )
    )
