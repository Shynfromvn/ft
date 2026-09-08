"""`FEATURE_SPEC` — reads the brief next door and validates it.

Read from YAML rather than restated in Python: the brief is the source and the
spec is derived from it. Copying the document here would create two places
describing one feature, and they would drift.
"""

from __future__ import annotations

from pathlib import Path

from pa.kernel.features_platform.spec import parse_feature_brief

FEATURE_SPEC, FEATURE_DOCS = parse_feature_brief(
    Path(__file__).with_name("feature.yaml").read_text(encoding="utf-8")
)
