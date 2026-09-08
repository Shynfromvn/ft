"""Memory hooks: what is remembered, and what the platform does with it.

The platform owns storage, scoping, idempotency and the outbox. This file
declares a category and projects rows back. It writes no scoping logic of its
own — scoping is where a mistake means one driver reading another's history.

── Vì sao file này chỉ còn một hook ───────────────────────────────────────

`ft007_battery_status_recommendation` khai hai hook: `transitions()` ghi lại
kết cục của một đề cử, và `recommendation_state_read_projection()` đọc trạng
thái về. Ở đó `transitions()` có người gọi — route `/respond` gọi nó sau khi
tính năng đã trả lời, rồi ghi kết quả vào **cùng dòng** đã `remember` lúc
`/evaluate` (upsert theo `dedup_key`), khiến dòng ấy thôi đọc như "còn đang
chờ".

Brief này không có `/respond`: §Phạm vi loại bỏ phản hồi người dùng, `Bước 4`
nói hai nút **không ấn được** (`BA-03`), `routing.triggers` rỗng và
`agent.operations` không có `RESPOND`. Không sự kiện nào làm một đề cử đổi
trạng thái, nên `transitions()` sẽ không bao giờ được gọi — và một hook không
ai gọi là code chết, không phải một chỗ dự phòng.

Cùng lúc gỡ luôn năm `RecordKind` và bảng `_ENDING_OF` ánh xạ chúng sang
`FinalState`. Cả năm tên — `spoke`, `rejected`, `snoozed`, `no_answer`,
`accepted` — mô tả những chuyện brief này không có, và bốn trong năm chỉ tới
được qua một câu trả lời của tài xế.

**Nếu `make feature-check` bắt buộc `recommendationHook` khác `null` khi
`memory.enabled: true`**, khôi phục một `transitions()` tối thiểu ghi đúng một
loại bản ghi (đề cử đã hiển thị) và ghi rõ ngay tại đó rằng nó chưa có đường
gọi. Đừng khôi phục cả bảng năm dòng.

── Điều này để lại một câu hỏi cho cơ chế chống trùng ─────────────────────

`AC-02` chặn khi Session History cho thấy một khuyến nghị Eco *đang được xử lý
hoặc chờ phản hồi*, và `ba.md` **không đặt mốc thời gian** cho trạng thái ấy —
luật là pop-up cũ chưa tắt thì không hiện cái mới.

Ở đây không có gì làm cho nó "tắt". Không phản hồi, không thực thi, không
`transitions()`. Nên dòng route ghi lúc hiển thị sẽ đọc là "còn đang chờ" cho
tới khi hết hạn — và cái hết hạn ấy là `engine.candidateLifetimeSeconds` trong
`feature.yaml`, hiện để `null`, tức mượn `DEFAULT_LIFETIME` của nền tảng.

Một con số mượn quyết định một luật nghiệp vụ: hết hạn là pop-up thứ hai được
phép hiện, dù cái thứ nhất vẫn trên màn hình. Đó là điều `AC-02` cấm. Xem
`feature.yaml` `engine.candidateLifetimeSeconds` — đây là chỗ câu hỏi ấy phải
được trả lời, không phải chỗ này.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

__all__ = [
    "CATEGORY",
    "recommendation_state_read_projection",
]

#: Declared in `feature.yaml`; the platform stores under it and recalls by it.
#:
#: Riêng của gói này, không dùng lại `battery_status` của gói `ft007_battery_status_recommendation`. Hai tính năng
#: chung một category là hai tính năng đọc được bản ghi của nhau, và một đề cử
#: đang chờ bên kia sẽ chặn đề cử bên này.
CATEGORY = "eco_mode_poc"


def recommendation_state_read_projection(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Hook the platform calls to read this feature's remembered state back."""
    return {
        "category": CATEGORY,
        "count": len(rows),
        "lastKind": rows[-1].get("kind") if rows else None,
    }
