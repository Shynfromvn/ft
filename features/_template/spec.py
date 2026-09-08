"""Spec mẫu. Đọc `feature.yaml` cạnh file này và validate nó.

Đọc từ YAML thay vì viết lại document bằng Python: brief là nguồn, spec là thứ
được suy ra. Chép nội dung sang đây sẽ tạo ra hai nơi cùng mô tả một tính năng,
và chúng sẽ lệch nhau.
"""

from __future__ import annotations

from pathlib import Path

from pa.kernel.features_platform.spec import parse_feature_brief

_BRIEF = Path(__file__).with_name("feature.yaml")

FEATURE_SPEC, FEATURE_DOCS = parse_feature_brief(_BRIEF.read_text(encoding="utf-8"))
