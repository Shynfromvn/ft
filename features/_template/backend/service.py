"""Business rules. THUẦN — nhận vào, trả ra.

Không HTTP, không I/O toàn cục, không đọc đồng hồ. Nhận `Clock` qua tham số:
cùng sự kiện + cùng ảnh chụp trạng thái + cùng ảnh chụp trí nhớ phải cho cùng
kết quả (`features/README.md`).

Đó là ranh giới cho phép QA gọi thẳng logic nghiệp vụ trong `tests/` mà không
cần dựng HTTP server hay Postgres.
"""

from __future__ import annotations

from pa.kernel.core.clock import Clock


def decide(*, clock: Clock) -> dict[str, object]:
    """TODO: luật nghiệp vụ. Ngưỡng là hằng số Python có type và có test."""
    return {"decidedAt": clock.now().isoformat()}
