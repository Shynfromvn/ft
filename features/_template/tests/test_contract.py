"""Spec hợp lệ, mọi symbol resolve, không import chéo tính năng."""

from __future__ import annotations

from pathlib import Path


def test_the_template_is_never_discovered() -> None:
    """Discovery quét `ft*`; `_template` không khớp, và đó là chủ đích.

    Một scaffold chưa ai điền mà lọt vào registry là một tính năng chạy với giá
    trị mẫu — và `TODO` trong câu nói sẽ hiện ra trước mặt vendor.
    """
    from pa.kernel.features_platform.discovery import iter_feature_dirs

    features_dir = Path(__file__).resolve().parents[2]
    found = {path.name for path in iter_feature_dirs(features_dir)}
    assert "_template" not in found
