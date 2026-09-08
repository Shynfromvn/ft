# Sequence — Khuyến nghị theo trạng thái pin

Kịch bản đường thuận của tính năng này: xe đang chạy, pin tụt qua ngưỡng cảnh báo mềm, trợ lý gợi
ý chuyển sang Eco Mode, tài xế đồng ý, xe xác nhận đã chuyển. Hình dưới đây theo đúng luồng chính
tả trong tài liệu yêu cầu nghiệp vụ — xem mục *"tra cứu"* trong wiki nếu cần đối chiếu tên miền
trạng thái xe hay tên sự kiện.

```mermaid
sequenceDiagram
    participant Xe as Chiếc xe
    participant BoCanh as Bộ canh điều kiện
    participant BoPhanDoan as Bộ phán đoán chủ động
    participant TriNho as Trí nhớ dùng chung
    participant DauMay as Đầu máy (giọng nói + thẻ trả lời)

    Note over Xe: Pin đang tụt dần, chưa tới ngưỡng
    Xe->>BoCanh: mẫu tín hiệu SoC liên tục

    Note over BoCanh: Pin đi qua 20% — đúng lúc xe đang chạy
    BoCanh->>BoPhanDoan: điều kiện vừa đúng

    BoPhanDoan->>TriNho: có đề cử Eco nào đang mở, hoặc lịch sử chặn nào không?
    TriNho-->>BoPhanDoan: không trùng, không có lịch sử chặn gần đây

    Note over BoPhanDoan: Kiểm tra khoảng cách còn lại tới điểm đến
    alt Còn xa điểm đến (≥ 5 km, hoặc chưa rõ điểm đến)
        Note over BoPhanDoan: Mọi cổng điều kiện đủ đều đạt
        BoPhanDoan->>DauMay: đề cử — gợi ý chuyển Eco Mode (chỉ giọng nói, vì đang chạy)
        DauMay->>Xe: đọc lên một câu ngắn gọn

        Note over Xe: Cửa sổ xác nhận 6 giây
        Xe->>DauMay: tài xế nói "Chuyển sang Eco"
        DauMay->>Xe: yêu cầu bộ điều khiển chuyển chế độ
        Xe-->>DauMay: bộ điều khiển xác nhận đã chuyển
        DauMay->>Xe: báo kết quả — ngắn gọn, bằng giọng nói
        DauMay->>TriNho: ghi kết cục — đã làm
    else Gần điểm đến (< 5 km tới nhà hoặc trạm sạc)
        Note over BoPhanDoan: Gợi ý bị chặn — sắp tới nơi rồi,<br/>chuyển Eco không còn nhiều giá trị
        BoPhanDoan->>TriNho: ghi lý do chặn — quá gần điểm đến
        Note over Xe: Trợ lý không nói gì. Im lặng đúng là kết cục mong đợi.
    end
```

## Những chỗ dễ đọc sai

- **Đường thuận có một nhánh im lặng hợp lệ ngay trong nó.** Gần điểm đến không phải một lỗi hay
  một trường hợp biên — đó là một trong hai kết cục bình thường của cùng một tình huống kích hoạt,
  và cả hai đều đáng được kiểm chứng.
- **Kết quả không phải "đã nói" mà là "bộ điều khiển đã xác nhận".** Trợ lý không được báo thành
  công cho một việc chưa quan sát thấy thật sự xảy ra — nếu bộ điều khiển từ chối hoặc không phản
  hồi, kết cục là thất bại, không phải đã làm, dù tài xế đã nói đồng ý.
- **Không phản hồi trong 6 giây không phải một lỗi.** Đó là một kết cục có tên riêng (bị bỏ qua),
  khác với việc tài xế nói "không" (bị từ chối) — hai kết cục này kéo theo hai khoảng nghỉ khác
  nhau trước khi trợ lý được hỏi lại.
- **Việc kiểm tra trí nhớ dùng chung xảy ra trước khi kiểm tra khoảng cách**, không phải sau. Một
  đề cử Eco đang mở, hoặc một lần bị chặn gần đây, dừng luồng sớm hơn cả việc hỏi xe đang ở đâu.
