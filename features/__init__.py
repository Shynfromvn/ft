"""Namespace package của các tính năng.

KHÔNG liệt kê tính năng nào ở đây, và không import tính năng nào. Discovery nhận
đường dẫn thư mục từ `core.settings`, quét `features/ft*/spec.py` và nạp bằng
`importlib` (ADR-0006). Một `import` tĩnh ở file này là vi phạm bất biến I2.
"""
