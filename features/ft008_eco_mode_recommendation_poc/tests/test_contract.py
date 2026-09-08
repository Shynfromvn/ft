"""The contract: spec valid, symbols resolve, nothing imported across features.

These would also be caught by the startup checker and by `make feature-check`.
Having them here too means a developer working inside this directory finds a
broken contract from `pytest features/ft008_*/tests` rather than from an app
that will not start twenty minutes later.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]

#: Tên package, dùng ở nhiều bài dưới đây. Một hằng thay vì bảy chuỗi lặp: đổi
#: tên gói là sửa một dòng, và không bài nào lặng lẽ còn canh tên cũ.
PACKAGE_NAME = "ft008_eco_mode_recommendation_poc"


def test_the_spec_validates() -> None:
    from features.ft008_eco_mode_recommendation_poc.spec import FEATURE_SPEC

    assert FEATURE_SPEC.identity.feature_id == "FT-008"
    assert FEATURE_SPEC.schema_version == 2


def test_every_declared_symbol_resolves() -> None:
    """Invariant I5, from inside the feature.

    A typo in a handler path would otherwise surface the first time a battery
    crosses a threshold in front of an audience — and the symptom is that
    nothing happens, which is the least debuggable symptom there is.
    """
    from features.ft008_eco_mode_recommendation_poc.spec import FEATURE_SPEC
    from pa.kernel.features_platform.contracts import resolve_symbol

    references = [
        FEATURE_SPEC.handlers.evaluate_model,
        FEATURE_SPEC.handlers.respond_model,
        FEATURE_SPEC.handlers.evaluate,
        FEATURE_SPEC.handlers.respond,
        FEATURE_SPEC.agent.adapter,
        FEATURE_SPEC.runtime.projection,
        *[hook for hook in FEATURE_SPEC.memory.hooks if hook is not None],
    ]
    for reference in references:
        assert reference is not None
        assert resolve_symbol(reference) is not None


def test_nothing_here_imports_another_feature() -> None:
    """Invariant I4, checked where it is easiest to break.

    A cross-feature import looks harmless right up until the other feature is
    deleted and this one stops working.

    Bài này là chỗ bản `cp` đầu tiên của gói POC hỏng nặng nhất: nó khẳng định
    mọi import phải trỏ về `ft007_battery_status_recommendation`, tức là nó
    **bảo vệ đúng cái vi phạm** mà nó sinh ra để bắt. Một cổng canh nhầm chiều
    còn tệ hơn không có cổng, vì nó xanh.
    """
    pattern = re.compile(r"(?:from|import)\s+features\.(\w+)")
    for path in PACKAGE.rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = pattern.search(line)
            if match:
                assert match.group(1) == PACKAGE_NAME, f"{path.name}: {line.strip()}"


def test_no_forbidden_call_anywhere_in_the_feature() -> None:
    """The four things `features/README.md` bans outright.

    `os.environ` bypasses settings, `print` bypasses the log pipeline,
    `dict[str, Any]` across a boundary means nothing validated it, and an
    HTTPException in a feature welds business logic to transport.
    """
    banned = {
        "os.environ": "read configuration through core.settings",
        "os.getenv": "read configuration through core.settings",
        "print(": "use core.logging.get_logger",
        "HTTPException": "raise an AppError; only the server layer knows HTTP",
    }
    # `backend/` only, not `tests/`. The ban is about runtime code, and this
    # test's own docstring names every banned token — a gate that fires on the
    # sentence describing it gets switched off rather than fixed.
    for path in (PACKAGE / "backend").rglob("*.py"):
        body = path.read_text(encoding="utf-8")
        for token, remedy in banned.items():
            assert token not in body, f"{path.name} uses {token!r} — {remedy}"


def test_the_service_layer_is_pure() -> None:
    """`service.py` must stay testable without a database or a clock.

    That purity is why the Session History lookup lives in `handlers.py`
    instead. If an import of a repository or a session appears here, the unit
    tests stop being unit tests and the split has quietly stopped paying for
    itself.
    """
    body = (PACKAGE / "backend" / "service.py").read_text(encoding="utf-8")
    for token in ("sqlalchemy", "AsyncSession", "repositories", "httpx", "fastapi"):
        assert token not in body, f"service.py imports {token!r} and is no longer pure"


def test_business_logic_never_reads_the_clock_directly() -> None:
    """`features/README.md` — determinism.

    A rule that calls `datetime.now()` makes every test depend on the wall
    clock. Nothing in this brief is time-dependent, which makes the gate cheap
    to keep and expensive to lose: the day someone adds a window or a timeout,
    this is what stops them adding it against the ambient clock.
    """
    import ast

    for name in ("service.py", "rules.py", "copy.py"):
        tree = ast.parse((PACKAGE / "backend" / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"now", "utcnow", "today"}
                # `clock.now()` is the injected one and is the whole point.
                and not (isinstance(node.func.value, ast.Name) and node.func.value.id == "clock")
            ):
                raise AssertionError(f"{name}:{node.lineno} reads the clock directly")


def test_the_feature_id_in_the_rules_matches_the_brief() -> None:
    """`service._FEATURE_ID` là bản sao thứ hai của `identity.featureId`.

    Không khử được như ngưỡng 20%. Ngưỡng có `thresholdProvider`: `feature.yaml`
    khai *tín hiệu nào*, `rules.py` giữ *bao nhiêu*, và không con số nào có bản
    sao. Ở đây `public_result()` phải phát ra ID trong mọi câu trả lời, mà
    `service.py` không được import `spec.py` — đọc YAML từ tầng luật là mất
    tính thuần, và cùng với nó là khả năng test không cần file nào.

    Nên bản sao ở lại và bài này canh nó. Đó là cách xử lý thứ hai của repo cho
    cùng một vấn đề: khử được thì khử, không khử được thì bắt một cổng canh hai
    bên khớp nhau.

    Đọc một tên bắt đầu bằng gạch dưới là có chủ ý: bản sao ấy là chi tiết nội
    bộ với mọi người gọi khác, chỉ bài này được biết nó tồn tại.
    """
    from features.ft008_eco_mode_recommendation_poc.backend import service
    from features.ft008_eco_mode_recommendation_poc.spec import FEATURE_SPEC

    assert service._FEATURE_ID == FEATURE_SPEC.identity.feature_id


def test_no_route_leads_to_respond() -> None:
    """`ba.md` §Phạm vi: không có phản hồi người dùng.

    Ba lời khai phải cùng nói một điều, và bài này bắt lúc chúng bắt đầu lệch.
    `handlers.respond` vẫn được khai vì `schemaVersion: 2` đòi đủ bốn trường
    `handlers.*`; điều làm nó không tới được là hai lời khai còn lại.
    """
    from features.ft008_eco_mode_recommendation_poc.spec import FEATURE_SPEC

    assert FEATURE_SPEC.routing.triggers == []
    assert "RESPOND" not in FEATURE_SPEC.agent.operations
    assert FEATURE_SPEC.runtime.events == []


def test_respond_refuses_rather_than_pretends() -> None:
    """Gọi tới `respond` là một hiểu nhầm về phạm vi, và nó phải nổ.

    Trả về `{"ok": true}` sẽ khiến bên gọi tin rằng câu trả lời của họ đã được
    ghi nhận, trong khi không có gì được ghi. `features/README.md` nói thẳng —
    một tính năng hỏng phải nhìn thấy được, không được degrade thành "hôm nay
    nó im".
    """
    from features.ft008_eco_mode_recommendation_poc.backend.handlers import respond
    from features.ft008_eco_mode_recommendation_poc.backend.schemas import RespondRequest
    from pa.kernel.core.errors import ValidationFailed

    with pytest.raises(ValidationFailed):
        asyncio.run(respond(RespondRequest(candidateId="cand-1")))


def test_public_result_asks_the_vehicle_for_nothing() -> None:
    """`ba.md` §Phạm vi loại "thực thi lệnh ECU" và "xác nhận ECU".

    Hai khoá này là đường duy nhất một lệnh rời khỏi tính năng, nên vắng mặt
    của chúng **là** ranh giới phạm vi, không phải một chi tiết trình bày.
    `recommendedActions` thì phải có mặt: `Bước 3` đòi Candidate mang *Hành
    động khuyến nghị*, và khai một ý định không phải là ra một lệnh.
    """
    from features.ft008_eco_mode_recommendation_poc.backend import service
    from features.ft008_eco_mode_recommendation_poc.backend.schemas import EvaluateRequest
    from pa.kernel.core.clock import SystemClock

    request = EvaluateRequest.model_validate(
        {
            "batteryState": {"socPct": 19.4, "dataAgeSeconds": 1},
            "vehicleState": {"driveMode": "NORMAL"},
            "connectivityState": {"online": True},
            "settings": {"batteryStateReliable": True, "vehicleStateReliable": True},
        }
    )
    result = service.public_result(service.evaluate(request, clock=SystemClock()))

    assert "actionsToExecute" not in result
    assert "confirmation" not in result
    assert result["recommendedActions"] == [{"target": "driving_mode", "targetState": "ECO"}]
    assert result["resolvedPlan"]["choicesInteractive"] is False


def test_the_allowlist_covers_exactly_what_the_rules_emit() -> None:
    """`publicResult.allowedFields` và `public_result()` phải khớp từng khoá.

    Lệch hai chiều, hai kiểu hỏng khác nhau. Khai thiếu thì bộ lọc cắt mất một
    trường tính năng vừa dựng, và thứ tới nền tảng là một Candidate khuyết mà
    không dòng log nào nói tại sao. Khai thừa thì lời khai mô tả một trường
    không tồn tại — vô hại hôm nay, và là một cái tên sai để tra cứu về sau.

    `context` không nằm ở đây có chủ ý: `handlers.evaluate()` gắn nó **sau**
    `public_result()`, và nó không bao giờ được phép tới tài xế.
    """
    from features.ft008_eco_mode_recommendation_poc.backend import service
    from features.ft008_eco_mode_recommendation_poc.backend.schemas import EvaluateRequest
    from features.ft008_eco_mode_recommendation_poc.spec import FEATURE_SPEC
    from pa.kernel.core.clock import SystemClock

    request = EvaluateRequest.model_validate(
        {
            "batteryState": {"socPct": 19.4, "dataAgeSeconds": 1},
            "vehicleState": {"driveMode": "NORMAL"},
            "connectivityState": {"online": True},
            "settings": {"batteryStateReliable": True, "vehicleStateReliable": True},
        }
    )
    emitted = set(service.public_result(service.evaluate(request, clock=SystemClock())))

    assert emitted == set(FEATURE_SPEC.public_result.allowed_fields)


def test_the_factors_this_feature_reads_reach_its_spec() -> None:
    """Khối `factors:` chỉ có nghĩa nếu nó ra tới `FEATURE_SPEC` — nếu không, nó
    là một comment dài trong YAML.

    Hai, không phải sáu. Bốn dòng `navigation.*` của gói rộng hơn ra đi cùng
    Navigation, và `runtime.stateDomains` phải đồng ý: một factor thuộc miền
    tính năng không xin là một factor không bao giờ tới.
    """
    from features.ft008_eco_mode_recommendation_poc.spec import FEATURE_SPEC

    declared = {need.key: need.freshness for need in FEATURE_SPEC.factors}
    assert set(declared) == {"motion.socPct", "motion.socDataAgeSeconds"}
    # Độ tươi là một MÃ, không phải con số — con số sống ở `docs/ba.md`.
    assert set(declared.values()) == {"NFR-01"}

    domains = {key.split(".")[0] for key in declared}
    assert domains <= set(FEATURE_SPEC.runtime.state_domains)


def test_every_factor_says_how_it_is_fetched() -> None:
    """Tính năng khai **cái gì** và **lấy thế nào**; nền tảng viết **cách nào**.

    `strategy = None` không phải một lỗi ở tầng nền tảng — nó nghĩa *chưa ai
    nghĩ tới*, và phần lớn tính năng chưa nghĩ tới. Nhưng tính năng **này** đã
    nghĩ, và bài đo ở đây là chỗ lời khai ấy không lặng lẽ rơi mất khi ai đó
    thêm một factor thứ ba.

    `latest` cho cả hai, và đó là một lựa chọn: tính năng quyết trên GIÁ TRỊ
    ĐANG CÓ, không trên một giá trị đã bầu — mọi chiến lược khác trả về một số
    không số đo nào từng mang.
    """
    from features.ft008_eco_mode_recommendation_poc.spec import FEATURE_SPEC

    chosen = {need.key: need.strategy for need in FEATURE_SPEC.factors}
    assert None not in chosen.values(), (
        f"factor chưa khai chiến lược: {sorted(k for k, v in chosen.items() if v is None)}"
    )
    assert set(chosen.values()) == {"latest"}


def test_the_freshness_code_resolves_to_a_number_this_feature_declared() -> None:
    """Độ tươi đi qua hai chặng, và cả hai sống trong `feature.yaml`.

    `factors[].freshness` cho một **mã**; `budgets[]` cho **con số** dưới cùng
    mã ấy. Một mã không có dòng `budgets:` tương ứng là một fail-closed không
    bao giờ chạy, nên bài này ghim rằng đường tra khép kín.

    **Nó cũng ghim một chỗ chưa đúng, thay vì để nó im.** Con số 10.0 dưới đây
    không có nguồn trong `ba.md` của gói này: `Preconditions §2` đòi dữ liệu
    đáp ứng "chính sách độ tươi quy định trong bảng NFR", nhưng bảng NFR chỉ có
    `NFR-01` = *"S5 lấy dữ liệu SoC: 3 phút một lần"*, một chu kỳ lấy chứ không
    phải một trần tuổi. 10.0 là số kế thừa từ requirement nguồn, giữ vì chặt
    hơn là hướng an toàn — không phải vì ai đó duyệt nó.

    Ngày BA trả lời, `ba.md` đổi trước, `budgets:` theo sau, và dòng dưới đây
    đỏ đúng lúc nó nên đỏ.
    """
    from features.ft008_eco_mode_recommendation_poc.spec import FEATURE_SPEC

    seconds_of = {budget.nfr: budget.budget_s for budget in FEATURE_SPEC.budgets}
    for need in FEATURE_SPEC.factors:
        assert need.freshness in seconds_of, (
            f"factor {need.key} khai {need.freshness} mà không dòng `budgets:` nào mang mã ấy"
        )

    assert seconds_of["NFR-01"] == 10.0
    # `NFR-02` — trần quyết định của S5, 2,5 giây. Con số này CÓ nguồn:
    # `ba.md` bảng NFR viết đúng nó.
    assert seconds_of["NFR-02"] == 2.5