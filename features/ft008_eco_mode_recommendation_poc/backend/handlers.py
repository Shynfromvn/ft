"""Entry points the platform calls. Thin, `async`, and free of FastAPI.

A handler resolves what it needs, calls the rules, and returns a dict. No
business rule lives here — that is `service.py` — and no HTTP type appears,
which is what lets the same logic be driven from a scenario runner, a test
harness or a queue consumer without change.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from features.ft008_eco_mode_recommendation_poc.backend import service
from features.ft008_eco_mode_recommendation_poc.backend.schemas import (
    EvaluateRequest,
    RespondRequest,
)
from pa.kernel.core.clock import Clock, SystemClock
from pa.kernel.core.errors import ValidationFailed

__all__ = ["evaluate", "respond"]


def _facts_from(memory: Mapping[str, Any]) -> service.SessionHistoryFacts:
    """Dịch snapshot của nền tảng sang từ vựng của tính năng này.

    Việc dịch nằm ở đây chứ không ở route: route giữ nguyên tính trung lập với
    mọi tính năng (nó chỉ chuyển tiếp một `Mapping`), và chỉ một tính năng mới
    được đặt tên cho mã lý do của chính nó.

    Gói gốc có một bảng bốn dòng ở đây, ánh xạ bốn kiểu hỏng của
    `assemble()` — `timeout`, `absent`, `error`, `expired` — sang bốn mã `E02`
    riêng. Brief này không có `E02`, nên bốn kiểu hỏng gộp về một mã duy nhất
    và bảng ấy không còn gì để tra. Nếu BA điền §6 và phân biệt các trường hợp,
    bảng quay lại cùng lúc với các mã mới trong `rules.py`.
    """
    if memory.get("error") is not None:
        return service.SessionHistoryFacts(available=False)
    return service.SessionHistoryFacts(
        duplicate_candidate=bool(memory.get("duplicateCandidate"))
    )


async def evaluate(
    request: EvaluateRequest,
    memory: Mapping[str, Any] | None = None,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Decide whether to recommend anything, and with what content.

    `memory` is the platform's Session History snapshot for this driver
    (`ba.md` `Bước 2`) — or `{"error": ...}` when the platform could not
    assemble one. `None` reads as "readable, nothing outstanding"
    (`_facts_from`'s default), which is what the trigger/bus path passes: it
    calls every feature's handler with one argument and does not know this
    feature's vocabulary.

    `clock` is an argument with a default rather than a module global, so a
    test drives a scenario without waiting and without patching. Nothing in
    this brief is time-dependent, but the platform supplies one and the
    signature stays uniform across features.
    """
    resolved_clock = clock or SystemClock()
    facts = _facts_from(memory or {})
    decision = service.evaluate(request, clock=resolved_clock, facts=facts)
    result = service.public_result(decision)
    # Không nằm trong `publicResult.allowedFields`, nên nó không bao giờ tới
    # tài xế — chỉ vào `evidence` của Candidate, nơi route đọc nó từ đây.
    # Xem `service.audit_context`: brief này không có `BA-nn` nào đòi bản ghi
    # truy vết, và dòng này đi cùng hàm ấy nếu route chịu được việc thiếu khoá.
    result["context"] = service.audit_context(request)
    return result


async def respond(
    request: RespondRequest,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Không có luồng phản hồi. Từ chối, to và rõ.

    `ba.md` §Phạm vi loại bỏ phản hồi Voice/Touch, timeout phản hồi, thực thi
    lệnh ECU và toàn bộ lifecycle sau khi Candidate được hiển thị; `Bước 4`
    nói hai nút xác nhận **không ấn được** (`BA-03`). Không màn hình nào phát
    ra câu trả lời, `routing.triggers` rỗng, và `agent.operations` không có
    `RESPOND` — nên không đường nào trong hệ thống dẫn tới đây.

    Hàm vẫn tồn tại vì `schemaVersion: 2` đòi đủ bốn trường `handlers.*`.
    **Nếu `make feature-check` chấp nhận `null` cho `respondModel` và
    `respond`, xoá cả hàm này lẫn `RespondRequest`.**

    Nổ chứ không trả về im lặng: một lời gọi tới đây là một hiểu nhầm về phạm
    vi của tính năng, và trả về `{"ok": true}` sẽ khiến bên gọi tin rằng câu
    trả lời của họ đã được ghi nhận. `features/README.md` nói thẳng — một tính
    năng hỏng phải nhìn thấy được, không được degrade thành "hôm nay nó im".
    """
    del clock, request
    raise ValidationFailed(
        "FT-008 không nhận phản hồi: khuyến nghị được hiển thị ở trạng thái "
        "không tương tác (ba.md Bước 4, BA-03)"
    )