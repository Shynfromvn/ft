"""FT-008 — khuyến nghị chuyển Eco Mode khi pin thấp (POC rút gọn).

Xem [`README.md`](README.md) cạnh file này để biết mọi ngưỡng bằng con số, và
[`ba.md`](docs/ba.md) để biết vì sao từng yêu cầu tồn tại.

Đây là một tính năng **riêng**, không phải biến thể của
`ft007_battery_status_recommendation`: nó chạy trên một `ba.md` riêng, hẹp hơn
hẳn — không Navigation, không Safety/ADAS, không cuộc gọi, không Assistant
Mode, không phản hồi tài xế, không thực thi ECU. Luồng dừng ở chỗ khuyến nghị
được hiển thị.
"""
