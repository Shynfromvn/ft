"""The contract: spec valid, symbols resolve, nothing imported across features.

These would also be caught by the startup checker and by `make feature-check`.
Having them here too means a developer working inside this directory finds a
broken contract from `pytest features/ft007_*/tests` rather than from an app
that will not start twenty minutes later.
"""

from __future__ import annotations

import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_spec_validates() -> None:
    from features.ft007_battery_status_recommendation.spec import FEATURE_SPEC

    assert FEATURE_SPEC.identity.feature_id == "FT-007"
    assert FEATURE_SPEC.schema_version == 2


def test_every_declared_symbol_resolves() -> None:
    """Invariant I5, from inside the feature.

    A typo in a handler path would otherwise surface the first time a battery
    crosses a threshold in front of an audience — and the symptom is that
    nothing happens, which is the least debuggable symptom there is.
    """
    from features.ft007_battery_status_recommendation.spec import FEATURE_SPEC
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
    """
    pattern = re.compile(r"(?:from|import)\s+features\.(\w+)")
    for path in PACKAGE.rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = pattern.search(line)
            if match:
                assert match.group(1) == "ft007_battery_status_recommendation", (
                    f"{path.name}: {line.strip()}"
                )


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
    # sentence describing it gets switched off rather than fixed (C012).
    for path in (PACKAGE / "backend").rglob("*.py"):
        body = path.read_text(encoding="utf-8")
        for token, remedy in banned.items():
            assert token not in body, f"{path.name} uses {token!r} — {remedy}"


def test_the_service_layer_is_pure() -> None:
    """`service.py` must stay testable without a database or a clock.

    That purity is why the memory lookup lives in `agent.py` instead. If an
    import of a repository or a session appears here, the unit tests stop being
    unit tests and the split has quietly stopped paying for itself.
    """
    body = (PACKAGE / "backend" / "service.py").read_text(encoding="utf-8")
    for token in ("sqlalchemy", "AsyncSession", "repositories", "httpx", "fastapi"):
        assert token not in body, f"service.py imports {token!r} and is no longer pure"


def test_respond_model_validates_a_realistic_driver_answer() -> None:
    """`DEBT-049` worried the route would push `{"response": answer}` into this
    model. It does not — `respond_to_feature` validates `body.root` as-is — but
    that was only confirmed by reading the route, not by a test. This is that
    test: a realistic camelCase driver answer must validate against FT-007's
    own `RespondRequest`, the same way `resolve_model` hands it to the route.
    """
    from features.ft007_battery_status_recommendation.backend.schemas import RespondRequest

    request = RespondRequest.model_validate(
        {
            "candidateId": "cand-123",
            "outcome": "accept",
            "channel": "voice",
            "respondedAfterSeconds": 2.4,
        }
    )
    assert request.candidate_id == "cand-123"
    assert request.outcome == "accept"
    assert request.channel == "voice"


def test_business_logic_never_reads_the_clock_directly() -> None:
    """`features/README.md` — determinism.

    A rule that calls `datetime.now()` makes every test about a cooldown, a
    response window or an acknowledgement ceiling depend on the wall clock.
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


def test_the_factors_this_feature_reads_reach_its_spec() -> None:
    """Khối `factors:` chỉ có nghĩa nếu nó ra tới `FEATURE_SPEC` — nếu không, nó
    là một comment dài trong YAML.

    Ở đây chứ không ở `backend/tests/`: bài này nói về **tính năng này đọc gì**,
    và một bài ở nền tảng khẳng định điều đó sẽ là nền tảng biết tên một tính
    năng (bất biến 1, ADR-0003 về vị trí test).
    """
    from features.ft007_battery_status_recommendation.spec import FEATURE_SPEC

    declared = {need.key: need.freshness for need in FEATURE_SPEC.factors}
    assert "motion.socPct" in declared
    # Hai trường navigation từng nằm dưới `world.*`; chúng về đúng miền của mình
    # từ ADR-0061 điều 2, và lời khai ở đây phải theo.
    assert "navigation.nearestChargerKm" in declared
    assert "navigation.destinationType" in declared
    # Độ tươi là một MÃ, không phải con số — con số sống ở `docs/ba.md`.
    assert set(declared.values()) == {"NFR-01"}


def test_every_factor_says_how_it_is_fetched() -> None:
    """ADR-0054 điều 3: tính năng khai **cái gì** và **lấy thế nào**; nền tảng viết
    **cách nào**.

    `strategy = None` không phải một lỗi ở tầng nền tảng — nó nghĩa *chưa ai
    nghĩ tới*, và phần lớn tính năng chưa nghĩ tới. Nhưng tính năng **này** đã
    nghĩ, và bài đo ở đây là chỗ lời khai ấy không lặng lẽ rơi mất khi ai đó
    thêm một factor thứ bảy.

    `latest` cho cả sáu, và đó là một lựa chọn chứ không phải một mặc định:
    `NFR-07` đòi số nói với tài xế khớp 100% dữ liệu gốc của TBox, và mọi chiến
    lược khác đều trả về một giá trị không số đo nào từng mang.
    """
    from features.ft007_battery_status_recommendation.spec import FEATURE_SPEC

    chosen = {need.key: need.strategy for need in FEATURE_SPEC.factors}
    assert None not in chosen.values(), (
        f"factor chưa khai chiến lược: {sorted(k for k, v in chosen.items() if v is None)}"
    )
    assert set(chosen.values()) == {"latest"}


def test_the_freshness_code_resolves_to_a_number_this_feature_declared() -> None:
    """Độ tươi đi qua hai chặng, và cả hai sống trong `feature.yaml`.

    `factors[].freshness` cho một **mã**; `budgets[]` cho **con số** dưới cùng
    mã ấy. Nền tảng chỉ biết cách tra (`FactorReader`), và một mã không có dòng
    `budgets:` tương ứng là một fail-closed không bao giờ chạy — nên bài này ghim
    rằng đường tra khép kín cho chính tính năng này.

    **Nó cũng ghim một chỗ chưa đúng, thay vì để nó im.** `ba.md` cho `NFR-01`
    hai con số — telemetry ≤10 giây, bối cảnh Navigation ≤2 phút — và bốn factor
    `navigation.*` dưới đây tra ra **10**, không phải 120. Đó là `DEBT-173`:
    độ tươi khoá theo mã `NFR`, và một mã mang hai con số thì không khai được
    hai trần. Con số chặt hơn là con số đang chạy, nên hướng sai là hướng an
    toàn — nhưng nó vẫn sai, và dòng dưới đây là chỗ nó được nói ra.
    """
    from features.ft007_battery_status_recommendation.spec import FEATURE_SPEC

    seconds_of = {budget.nfr: budget.budget_s for budget in FEATURE_SPEC.budgets}
    for need in FEATURE_SPEC.factors:
        assert need.freshness in seconds_of, (
            f"factor {need.key} khai {need.freshness} mà không dòng `budgets:` nào mang mã ấy"
        )

    assert seconds_of["NFR-01"] == 10.0
    # `DEBT-173`: khi vế Navigation có nhà, bốn factor này tra ra 120 và dòng
    # dưới đây đỏ — đúng lúc nó nên đỏ.
    navigation = [need for need in FEATURE_SPEC.factors if need.key.startswith("navigation.")]
    assert len(navigation) == 4
    assert {seconds_of[need.freshness] for need in navigation} == {10.0}
