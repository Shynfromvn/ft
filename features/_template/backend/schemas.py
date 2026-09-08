"""Model vào/ra của tính năng. Typed ở mọi biên — không `dict[str, Any]`."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class FeatureModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class EvaluateRequest(FeatureModel):
    """TODO: trường đầu vào của lần đánh giá."""

    profile_id: str = ""


class RespondRequest(FeatureModel):
    """TODO: trường của một lần tài xế phản hồi."""

    candidate_id: str = ""
    response: str = ""
