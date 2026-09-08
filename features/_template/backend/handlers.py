"""Điểm vào. `async`, ném `AppError` của core, không import FastAPI."""

from __future__ import annotations

from typing import Any

from features.ft000_example.backend.schemas import EvaluateRequest, RespondRequest


async def evaluate(request: EvaluateRequest) -> dict[str, Any]:
    """TODO: gọi service. Handler chỉ điều phối, không chứa luật nghiệp vụ."""
    return {"ok": True}


async def respond(request: RespondRequest) -> dict[str, Any]:
    """TODO: ghi nhận phản hồi của tài xế."""
    return {"ok": True}
