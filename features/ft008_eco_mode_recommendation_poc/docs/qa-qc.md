# FT-007 — Tiêu chí nghiệm thu

<!-- internal -->
- **Yêu cầu nguồn:** [`ba.md`](ba.md) — bản sao nguyên văn của `[SYS2] Khuyến nghị theo trạng thái pin` v0.1
- **Người viết / Người duyệt:** trinq / trinq (chủ dự án)
- **Ngày viết / Ngày duyệt:** 2026-08-25 / 2026-08-28
- **Test script:** [`tests/FT-007-battery-status-recommendation/`](../../../tests/FT-007-battery-status-recommendation/)
- **Báo cáo lần chạy:** [`artifacts/reports/qc-runs/FT-007/`](../../../artifacts/reports/qc-runs/FT-007/) —
  lần đầu 2026-08-28 (26 đạt · 3 trượt · 16 chờ người kiểm · 6 bị chặn bởi DEBT); lần hai cùng ngày
  sau khi vá `QC-09.1`/`QC-16.2`/`QC-30.1`, 29 đạt · 0 trượt · 16 chờ người kiểm · 6 bị chặn bởi DEBT;
  lần ba cùng ngày sau B3 (S7 tự kiểm bối cảnh trước khi định tuyến Candidate sang S6, đóng
  `DEBT-064`), 32 đạt · 0 trượt · 16 chờ người kiểm · 3 bị chặn bởi DEBT

> **Viết lại toàn bộ ngày 2026-08-25.** Bản trước bám vào một `ba.md` do repo tự soạn, rộng hơn
> tài liệu công ty ở ba mảng lớn: luồng khẩn cấp 5% / chế độ bảo toàn, trí nhớ xuyên chuyến, và
> khoảng nghỉ. `ba.md` nay là **bản sao nguyên văn** của tài liệu BA chính thức, chỉ còn UC-01 và
> mười một NFR — nên toàn bộ mã `QC-nn.m` cũ không còn trỏ về đâu và phải đánh lại.
> Bối cảnh: [C014](../../devlog/sprint-02-nen-backend-va-ft-007/log.md).
>
> `nn` của một `QC-nn.m` luôn khớp `BA-nn` mà nó kiểm chứng, và `BA-nn` được định nghĩa ở
> *Phụ lục — Mã yêu cầu dùng trong repo* của `ba.md`. Cột **Chặng** dùng bảy chặng của
> [`event-lifecycle.md`](../../architecture/event-lifecycle.md); ánh xạ giữa bảy chặng đó và các
> vai S5/S6/S7/S10 của tài liệu công ty nằm ở
> [ADR-0011](../../adr/0011-anh-xa-vai-nang-luc-cong-ty-vao-kien-truc-repo.md).
<!-- internal -->

---

## Bảng phủ

| Yêu cầu | Mã gốc | Được phủ bởi |
|---|---|---|
| BA-01 | AC-01 | QC-01.1, QC-01.2, QC-01.3 |
| BA-02 | AC-02 | QC-02.1, QC-02.2 |
| BA-03 | AC-03 | QC-03.1 |
| BA-04 | AC-04 | QC-04.1 |
| BA-05 | AC-05 | QC-05.1 |
| BA-06 | AC-06 | QC-06.1, QC-06.2 |
| BA-07 | AC-07 | QC-07.1, QC-07.2 |
| BA-08 | AC-08 | QC-08.1 |
| BA-09 | AC-09 | QC-09.1 |
| BA-10 | AC-10 | QC-10.1, QC-10.2 |
| BA-11 | AC-11 | QC-11.1, QC-11.2 |
| BA-12 | AC-12 | QC-12.1, QC-12.2 |
| BA-13 | AC-13 | QC-13.1, QC-13.2 |
| BA-14 | AC-14 | QC-14.1, QC-14.2, QC-14.3 |
| BA-15 | AC-15 | QC-15.1, QC-15.2 |
| BA-16 | AC-16 | QC-16.1, QC-16.2 |
| BA-17 | NFR-01 | QC-17.1, QC-17.2 |
| BA-18 | NFR-02 | QC-18.1, QC-18.2 |
| BA-19 | NFR-03 | QC-19.1 |
| BA-20 | NFR-04 | QC-20.1 |
| BA-21 | NFR-05 | QC-21.1 |
| BA-22 | NFR-06 | QC-22.1 |
| BA-23 | NFR-07 | QC-23.1 |
| BA-24 | NFR-08 | QC-24.1 |
| BA-25 | NFR-09 | QC-25.1, QC-25.2 |
| BA-26 | NFR-10 | QC-26.1 |
| BA-27 | NFR-11 | QC-27.1, QC-27.2 |
| BA-28 | BR-10 | QC-28.1 |
| BA-29 | E01 | QC-29.1 |
| BA-30 | E04 | QC-30.1 |
| BA-31 | E09 | QC-31.1 |
| BA-32 | E10 | QC-32.1 |
| BA-33 | A03 | QC-33.1, QC-33.2 |
| BA-34 | Bước 9 barge-in | QC-34.1 |

---

## Tiêu chí — tạo Candidate

Tất cả nằm ở phía S5. Kết quả đúng của một lần đánh giá là **một trong hai**: đúng một Candidate
hợp lệ, hoặc không Candidate nào cộng một mã lý do. Không có kết quả thứ ba.

| id | Điều kiện ban đầu | Việc xảy ra | Kết quả phải thấy | Chặng | Cách đo |
|---|---|---|---|---|---|
| QC-01.1 | Trợ lý Available · Assistant Mode = Balanced · Online · Vehicle State = Driving · System State = Normal · dữ liệu SoC và drive-mode còn tươi · bối cảnh Navigation hợp lệ với điểm đến cách 40 km · S7 Memory trả snapshot hợp lệ · không cổng Safety/Audio/attention-window nào chặn · xe đang ở `NORMAL` | Mức pin chạm 20% | Đúng **một** Candidate được tạo, phân loại **Direct-impact**, `Topic = Energy and Charging`, `Response Type = SUGGEST`, có thời hạn và có hợp đồng xác nhận | phán đoán | tự động |
| QC-01.2 | Như QC-01.1 nhưng Assistant Mode = Proactive | Mức pin chạm 20% | Vẫn tạo Candidate — Proactive là chế độ thứ hai được phép tự khởi tạo | phán đoán | tự động |
| QC-01.3 | Như QC-01.1 nhưng xe **đã** ở Eco Mode | Mức pin chạm 20% | **Không** Candidate nào; đúng một bản ghi mã lý do `already_in_eco_mode` | phán đoán | tự động |
| QC-01.4 | Như QC-01.1 nhưng xe **khởi động ở 18%** — pin **chưa từng** đi qua ngưỡng ở bất kỳ frame nào | Chuyến thứ nhất kết thúc, tài xế đặt điểm đến khác, chuyến thứ hai bắt đầu | Đúng **một** Candidate được tạo. Đây là vế thứ hai của `ba.md` §3 (*"một chuyến đi mới bắt đầu / lộ trình thay đổi trong khi SoC đã ở mức ≤20%"*) — nếu chỉ vế thứ nhất được cài thì tình huống này im lặng hoàn toàn | phán đoán | tự động |
| QC-01.5 | Như QC-01.4, sau khi Candidate đã được tạo | Nhiều frame nữa trôi qua **trong cùng chuyến thứ hai**, pin vẫn thấp | **Không** Candidate thứ hai. Một chuyến là một lần nói: `Dedupe` khoá theo `(cột mốc, tập)`, và tập ở đây là chuyến đi | phán đoán | tự động |
| QC-01.6 | Như QC-01.4 nhưng pin ở **85%** | Chuyến mới bắt đầu | **Không** Candidate nào. *"Trong khi SoC đã ở mức ≤20%"* là một điều kiện, không phải một lời gợi ý — không có nó, mỗi lần nổ máy là một lần trợ lý mở miệng | phán đoán | tự động |
| QC-02.1 | S5 cần S7 Shared Memory cho attention-window và chống trùng lặp | S7 Memory quá 300 ms chưa trả lời | **Không** Candidate nào; bản ghi mang một trong `memory_unavailable` · `memory_timeout` | phán đoán | tự động |
| QC-02.2 | Như trên | S7 Memory trả snapshot đã hết hạn, hoặc mâu thuẫn với trạng thái đang có | **Không** Candidate nào; bản ghi mang `memory_expired` hoặc `memory_inconsistent` | phán đoán | tự động |
| QC-03.1 | Mức pin chạm 20%; Navigation xác nhận điểm đến đang hoạt động là **Nhà** hoặc **trạm sạc phù hợp**, khoảng cách còn lại 3 km | S5 đánh giá | **Không** Candidate nào, và việc chặn diễn ra **im lặng** — không đầu ra nào tới tài xế. Bản ghi mang `proximity_suppressed` | phán đoán | tự động |
| QC-04.1 | Mức pin chạm 20%; Navigation xác nhận điểm đến **không** phải Nhà và **không** phải trạm sạc, khoảng cách còn lại 3 km; mọi cổng khác đều đạt | S5 đánh giá | Candidate **được tạo**. Chặn ở đây là trượt tiêu chí — khoảng cách đơn thuần không phải lý do chặn | phán đoán | tự động |
| QC-05.1 | Bốn tình huống lần lượt: Navigation không khả dụng · lộ trình cũ quá 2 phút · lộ trình không nhất quán · không xác định được loại điểm đến | S5 đánh giá từng tình huống | Cả bốn đều **không** tạo Candidate, mỗi tình huống một mã lý do tương ứng: `navigation_unavailable` · `navigation_stale` · `navigation_inconsistent` · `destination_type_unknown` | phán đoán | tự động |

## Tiêu chí — phân phối và diễn đạt

| id | Điều kiện ban đầu | Việc xảy ra | Kết quả phải thấy | Chặng | Cách đo |
|---|---|---|---|---|---|
| QC-06.1 | Candidate hợp lệ được phân phối khi Vehicle State = Driving | S6 xuất đầu ra | Chỉ có **Voice** ngắn gọn. Không popup, Answer Card, Toast, Mascot, CTA, Text chi tiết, biểu mẫu, danh sách hay UI thao tác chạm nào tồn tại trên màn hình | diễn đạt | tự động |
| QC-06.2 | Như trên | Đọc nội dung phát ra | Câu nói bằng **tiếng Việt**, chứa ba thành phần đúng thứ tự: mức pin hiện tại → gợi ý chuyển Eco Mode kèm lợi ích → một câu hỏi chờ xác nhận. Đối chiếu với câu mẫu của UI/UX 9.1-1 | diễn đạt | quan sát |
| QC-07.1 | Candidate hợp lệ được phân phối khi Vehicle State = Parked, HMI khả dụng, không có tương tác ưu tiên cao hơn | S6 xác thực đầu ra | Voice kèm một **Answer Card** hiện SoC, gợi ý Eco Mode và lợi ích ngắn; đúng **hai** CTA tiếng Việt: "Chuyển sang Eco Mode" và "Để sau" | diễn đạt | tự động |
| QC-07.2 | Như trên, thẻ còn hợp lệ | Tài xế chạm CTA "Chuyển sang Eco Mode" | Thao tác chạm được chấp nhận như một xác nhận — nhưng **chỉ** khi Parked | hành động | tự động |
| QC-11.1 | Mức pin chạm 20% khi Vehicle State = Driving và Audio State = Call | S6 xác thực đầu ra | Voice và Sound bị chặn; **không** popup tĩnh, **không** phương án thay thế bằng Text trên HMI. Candidate được hoãn hoặc để hết hạn theo expiry. Bản ghi mang `call_active` | phán đoán | tự động |
| QC-11.2 | Mức pin chạm 20% khi Vehicle State = Parked và Audio State = Call | S6 xác thực đầu ra | UI/Text chỉ được hiện nếu nó **không che giao diện cuộc gọi** và expiry vẫn cho phép; che hoặc hết hạn thì không hiện gì và ghi `call_active` hoặc `candidate_expired` | diễn đạt | quan sát |
| QC-12.1 | Một Candidate Eco đang chờ hoặc đang được phân phối | Một Safety/System Alert loại **Warning** trở nên hoạt động | Voice bị tạm dừng hoặc bị chặn; trợ lý không cạnh tranh với đầu ra Safety. Bản ghi mang `safety_preempted` | hành động | tự động |
| QC-12.2 | Như trên | Alert loại **Intervention** trở nên hoạt động | Toàn bộ Voice-Sound của trợ lý dừng, nội dung hiển thị không còn hợp lệ bị gỡ, và **không tự động lặp lại**. Bản ghi mang `safety_preempted` | hành động | tự động |
| QC-13.1 | Answer Card, CTA, Mascot, Text chi tiết, biểu mẫu hoặc danh sách Eco đang hiển thị khi Parked | Xe chuyển sang Driving | Toàn bộ UI hiển thị/chạm bị ẩn trong vòng **≤ 100 ms**, và **không** bị thu nhỏ thành một thẻ chữ nhỏ | diễn đạt | tự động |
| QC-13.2 | Tiếp theo QC-13.1, Candidate vẫn còn hợp lệ và an toàn | Quan sát | Chỉ được tiếp tục bằng **Voice ngắn gọn**. Nếu không còn hợp lệ thì dừng và ghi `candidate_expired` hoặc `safety_preempted` | diễn đạt | tự động |

## Tiêu chí — xác nhận, thực thi và kết thúc

| id | Điều kiện ban đầu | Việc xảy ra | Kết quả phải thấy | Chặng | Cách đo |
|---|---|---|---|---|---|
| QC-08.1 | Một khuyến nghị Eco đã được phân phối | Tài xế **chưa** xác nhận rõ ràng qua kênh được phép | **Không** có lời gọi nào tới bộ điều khiển xe. Không có `SET_DRIVE_MODE` nào rời khỏi hệ thống | hành động | tự động |
| QC-09.1 | Tài xế xác nhận tường minh bằng giọng nói ("Có" / "Chuyển sang Eco" / "Bật Eco đi") | ECU xác nhận Eco Mode đang hoạt động | STATUS thành công phát ra — và **chỉ** sau khi ECU xác nhận. Kết quả cuối ghi `acted` hoặc `completed`. Câu nói đối chiếu UI/UX 9.1-3 | hành động | tự động |
| QC-10.1 | Tài xế xác nhận việc chuyển Eco | ECU từ chối hoặc thực hiện thất bại | STATUS **Error**; **không** có câu nào báo Success; chế độ vận hành hiện tại giữ nguyên. Bản ghi mang `execution_failed` kèm nguyên nhân nếu có | hành động | tự động |
| QC-10.2 | Như QC-10.1, Vehicle State = Driving | Quan sát toàn bộ đầu ra | Phương án khôi phục **chỉ bằng Voice**; **không** hiển thị hướng dẫn thao tác thủ công nào trên HMI | diễn đạt | quan sát |
| QC-14.1 | Khuyến nghị Eco đã được phân phối | Tài xế nói "Không" / "Để sau" / "Bỏ qua", hoặc chạm "Để sau" | Tương tác kết thúc, chế độ vận hành giữ nguyên, kết quả ghi `rejected` hoặc `snoozed` theo đúng intent được hỗ trợ | hành động | tự động |
| QC-14.2 | Khuyến nghị Eco đã được phân phối | Không phát hiện phản hồi được hỗ trợ nào trong **6 giây** | Tương tác kết thúc, chế độ vận hành giữ nguyên, kết quả ghi `ignored` | hành động | tự động |
| QC-14.3 | Khuyến nghị Eco đã được phân phối khi xe đang đỗ | Tài xế bấm **"Để sau"** | Kết cục là `snoozed`, **không phải** `rejected`. `AC-14` liệt ba kết cục riêng và `BR-10` gắn hệ quả khác nhau: từ chối mang khoảng nghỉ đầy đủ, hoãn thì không | hành động | tự động |
| QC-15.1 | Phản hồi của tài xế không rõ, bị nhiễu, chồng tiếng, hoặc không ánh xạ được sang một intent xác nhận đã duyệt | S6 đánh giá phản hồi | **Tuyệt đối không** thực thi chuyển Eco. Đây là tiêu chí không có ngoại lệ | hành động | tự động |
| QC-15.2 | Như trên | Vehicle State và Audio State cho phép | S6 phát một câu VERIFY hỏi lại. Nếu state **không** cho phép thì kết thúc mà không VERIFY | diễn đạt | tự động |
| QC-31.1 | Ba tình huống lần lượt: Candidate đạt tới thời hạn **trước khi phân phối** · **trước khi xác nhận** · **trước khi thực thi** | Chờ tới hết expiry | Cả ba đều dừng tương tác, gỡ đầu ra không còn hợp lệ, và ghi `candidate_expired`. Không tình huống nào dẫn tới một lời gọi ECU | hành động | tự động |
| QC-32.1 | Ba tình huống lần lượt: phát Voice lỗi · render Answer Card khi Parked lỗi · MHU không xác nhận | S6 phân phối | Không tình huống nào được coi là đã phân phối thành công. Mỗi tình huống ghi `delivery_failed`, và **không** có lần thử lại trùng lặp nào khi Vehicle State = Driving | hành động | tự động |
| QC-33.1 | Khuyến nghị đã phát, Vehicle State = Driving | Tài xế hỏi "Tại sao?" hoặc "Eco Mode là gì?" | Một câu giải thích **ngắn gọn, chỉ bằng Voice**, nội dung nêu Eco Mode giảm tiêu thụ năng lượng và giúp kéo dài quãng đường | diễn đạt | quan sát |
| QC-33.2 | Như trên nhưng Vehicle State = Parked, thẻ còn hợp lệ | Tài xế hỏi để làm rõ | Chi tiết được hiển thị trên Answer Card, và sau khi giải thích xong hệ thống **quay lại chờ phản hồi xác nhận** chứ không tự kết thúc | diễn đạt | tự động |
| QC-34.1 | TTS của khuyến nghị Eco đang phát | Tài xế cắt ngang bằng một yêu cầu khác | TTS hiện tại dừng trong ngưỡng barge-in; kết quả của Candidate Eco **được ghi nhận** vì đầu ra đã bắt đầu; intent mới nhất của tài xế được xử lý | hành động | tự động |

## Tiêu chí — ghi vết và chính sách

| id | Điều kiện ban đầu | Việc xảy ra | Kết quả phải thấy | Chặng | Cách đo |
|---|---|---|---|---|---|
| QC-16.1 | Một lần đánh giá bất kỳ chạy tới trạng thái cuối | Đọc bản ghi | Trạng thái cuối là **đúng một** trong tám giá trị: `acted` · `rejected` · `snoozed` · `ignored` · `suppressed` · `expired` · `failed` · `completed`. Không có giá trị thứ chín, và không có lần đánh giá nào kết thúc mà không có trạng thái | phán đoán | tự động |
| QC-16.2 | Như trên | Đọc bản ghi | Bản ghi có đủ: Candidate ID khi có · SoC · trạng thái drive-mode · Vehicle State · Assistant Mode · Audio State · kênh đầu ra · trạng thái cuối · timestamp · mã lý do · **chặng** chịu trách nhiệm. Thiếu một trường là trượt | phán đoán | tự động |
| QC-28.1 | Cùng một bối cảnh, tài xế từ chối khuyến nghị Eco **năm lần liên tiếp** | Lần thứ sáu mức pin chạm 20% | Khuyến nghị **vẫn phát bình thường bằng Voice**. Hệ thống không tự tắt Voice, không thay đầu ra Voice khi Driving bằng một biểu tượng HMI tĩnh, và không tự hạ cấp kênh. Lịch sử từ chối vẫn được lưu | phán đoán | tự động |

## Tiêu chí im lặng

Không tiêu chí nào dưới đây được miễn, kể cả khi luồng chính chạy tốt. Mọi tiêu chí đều đòi **hai**
thứ: không có đầu ra nào tới tài xế, **và** một bản ghi nêu mã lý do cùng chặng — để phân biệt
"cân nhắc rồi chọn không nói" với "hỏng nên không nói gì".

Tài liệu gốc không gom các trường hợp này thành một mục riêng; chúng nằm rải trong `Bước 5`,
`E01`–`E06` và `BR-09`/`BR-11`. Mục này gom lại vì repo coi im lặng là một hành vi phải nghiệm
thu, không phải phần còn lại sau khi trừ đi hành động.

| id | Điều kiện ban đầu | Việc xảy ra | Kết quả phải thấy | Chặng | Cách đo |
|---|---|---|---|---|---|
| QC-29.1 | Bốn tình huống lần lượt: SoC thiếu · timestamp cũ hơn 10 giây · source metadata thiếu · drive-mode không nhất quán với SoC | Mức pin chạm 20% | Cả bốn đều **không** tạo Candidate, và mỗi tình huống ghi đúng một mã: `data_missing` · `data_stale` · `invalid_payload` | phán đoán | tự động |
| QC-30.1 | Ba tình huống lần lượt: Assistant Mode = Quiet · Assistant Mode không xác định · Network = offline | Mức pin chạm 20% | Cả ba đều **không** tạo Candidate. Hai tình huống đầu ghi `assistant_mode_not_allowed`, tình huống thứ ba ghi `offline` | phán đoán | tự động |
| QC-24.1 | Bộ kiểm thử đi qua toàn bộ các tổ hợp cổng của `Bước 5` | Chạy hết bộ | **0** lần tạo Candidate khi bất kỳ điều kiện bắt buộc nào không thoả — độ tươi, Navigation, S7 Memory, safety, call, trùng lặp, hoặc điều kiện tiên quyết. 100% kết quả tuân thủ quy tắc | phán đoán | tự động |

Ba tiêu chí im lặng khác đã nằm ở các mục trên vì chúng cũng là tiêu chí của một `BA-nn` khác:
QC-01.3 (`already_in_eco_mode`), QC-02.1 và QC-02.2 (S7 Memory fail-closed), QC-03.1
(`proximity_suppressed`), QC-05.1 (Navigation fail-closed), QC-11.1 (`call_active`), QC-12.1 và
QC-12.2 (`safety_preempted`). Chúng chịu cùng luật hai-thứ ở trên.

## Tiêu chí phi chức năng

Mọi con số dưới đây là số của tài liệu gốc, đo trong **điều kiện online bình thường**.

| id | Điều kiện ban đầu | Việc xảy ra | Kết quả phải thấy | Chặng | Cách đo |
|---|---|---|---|---|---|
| QC-17.1 | Telemetry của S10 lấy từ TBox với `SyncType = OnWakeupAndOnChange` | S5 sử dụng một giá trị telemetry | Giá trị được dùng cũ **không quá 10 giây**. Cũ hơn thì S5 fail closed | tín hiệu | tự động |
| QC-17.2 | Bối cảnh Navigation dùng cho đánh giá khoảng cách gần | S5 sử dụng bối cảnh lộ trình | Bối cảnh cũ **không quá 2 phút**. Cũ hơn thì S5 fail closed | tín hiệu | tự động |
| QC-18.1 | Bối cảnh bắt buộc đã sẵn sàng và còn tươi | S5 chạy một lần đánh giá | Thời gian tới lúc tạo hoặc chặn Candidate **≤ 1 giây** | phán đoán | tự động |
| QC-18.2 | S5 yêu cầu snapshot từ S7 Memory | Chờ phản hồi | Snapshot hợp lệ, có phiên bản, chưa hết hạn về trong **≤ 300 ms**; quá ngưỡng thì S5 fail closed | phán đoán | tự động |
| QC-19.1 | S7 nhận một Candidate | S7 chạy kiểm tra bối cảnh rồi định tuyến | Thời gian tới lúc định tuyến sang S6 **≤ 1 giây** | phân phối | tự động |
| QC-20.1 | S6 nhận một yêu cầu đã được định tuyến | S6 xác thực lần cuối và xuất đầu ra | Thời gian tới đầu ra được phép **đầu tiên** ≤ **1 giây** | diễn đạt | tự động |
| QC-21.1 | S5 vừa tạo một Candidate | Chờ tới đầu ra đầu tiên hướng tới tài xế | Tổng thời gian đầu-cuối **≤ 3 giây** | diễn đạt | tự động |
| QC-22.1 | UI hiển thị/chạm đang hiện khi Parked | Vehicle State đổi sang Driving | UI bị ẩn trong **≤ 100 ms** và không bị thu nhỏ thành thẻ chữ nhỏ. Cùng hành vi với QC-13.1, ở đây đo bằng đồng hồ | diễn đạt | tự động |
| QC-23.1 | S10 cung cấp telemetry cho S5 | So sánh với dữ liệu gốc của TBox tại cùng thời điểm tham chiếu | SoC, drive-mode, Vehicle State, Audio/Call, Safety/System Alert và kết nối khớp **100%**. Giá trị không hợp lệ hoặc ngoài dải **không được sử dụng** | trạng thái xe | tự động |
| QC-25.1 | S7 định tuyến một Candidate tới S6 | So sánh payload hai đầu | Bảo toàn **100%**: Candidate ID · response type · hợp đồng xác nhận · payload CTA · thời hạn · trạng thái bối cảnh | phân phối | tự động |
| QC-25.2 | Bối cảnh ở mức S7 chặn việc phân phối | S7 xử lý Candidate | **0** lần định tuyến tới S6. Kết quả suppressed được cập nhật vào Memory và mã lý do được ghi | phân phối | tự động |
| QC-26.1 | Một vòng đời Candidate chạy hết và ghi vào S7 Memory | Đọc bản ghi bộ nhớ | **100%** bản ghi bảo toàn nguồn · loại sự kiện · Candidate ID khi có · timestamp · phiên bản · tính hợp lệ/thời hạn · metadata kết quả. **Không** bản ghi cũ, trùng lặp hay mâu thuẫn nào được S5 sử dụng | phán đoán | tự động |
| QC-27.1 | Tập câu thoại tiếng Việt đã được phê duyệt | Chạy toàn bộ tập qua nhận diện intent | Nhận diện đúng **≥ 95%**, và **0** xác nhận Eco dương tính giả | hành động | tự động |
| QC-27.2 | Toàn bộ các lần chạy của chiến dịch | Đếm các lần báo STATUS thành công | **0** báo cáo thành công dương tính giả — mỗi lần báo thành công đều có một xác nhận Eco Mode từ bộ điều khiển đứng trước nó | hành động | tự động |

---

## Kịch bản dùng để kiểm thử

Bốn kịch bản đã được viết lại theo UC-01 (plan P10 T11, 2026-08-26). Bảng dưới là thứ chúng
mô tả; *chạy được* và *khẳng định được* vẫn là hai chuyện khác nhau, và cột cuối nói rõ chỗ nào
còn phải đọc bằng mắt.

| Kịch bản | Phủ tiêu chí | Mô tả tình huống | Còn phải đọc bằng mắt |
|---|---|---|---|
| `ft-007-duong-thuan.yaml` | QC-01.1, QC-06.1, QC-06.2, QC-08.1, QC-09.1, QC-21.1 | Đang Driving, điểm đến cách 40 km, mức pin chạm 20%, tài xế xác nhận bằng giọng nói, bộ điều khiển xác nhận thành công | — |
| `ft-007-im-lang.yaml` | QC-01.3, QC-03.1, QC-04.1, QC-05.1, QC-29.1, QC-30.1 | Sáu lần chạm mốc: năm lần im vì năm cổng khác nhau của `Bước 5`, một lần **phải nói** — đích cách 3 km nhưng không phải Nhà và không phải trạm sạc | — |
| `ft-007-chiem-quyen.yaml` | QC-11.1, QC-12.1, QC-12.2, QC-13.1, QC-13.2 | Nhường quyền: cuộc gọi chen vào khi Driving, Safety Alert loại Warning rồi Intervention, và Parked chuyển sang Driving lúc thẻ đang hiện | — |
| `ft-007-that-bai.yaml` | QC-10.1, QC-10.2, QC-15.1, QC-31.1, QC-32.1 | Bộ điều khiển từ chối, phản hồi mơ hồ không được coi là xác nhận, đề cử hết hạn giữa chừng, phân phối thất bại | QC-15.1 — câu trả lời "mơ hồ" của tài xế chưa có giá trị riêng để mô phỏng[^qc-15-1] |

`ft-007-khan-cap` đã đổi tên thành `ft-007-chiem-quyen`: "khẩn cấp" mô tả luồng 5% và chế độ bảo
toàn, hai khái niệm thuộc phạm vi đã bị loại. Đổi tên kéo theo `docs.demoScenarios` trong
`feature.yaml`, nên hai việc đi cùng một lần.

---

## Điều kiện đạt

- [ ] Mọi `QC-nn.m` đều đạt — tài liệu gốc không phân mức ưu tiên giữa các `AC`, nên ở đây cũng
      không có tiêu chí nào là *nên có*
- [ ] Mọi tiêu chí ở mục *Tiêu chí im lặng* đều đạt, **không có ngoại lệ**, kể cả khi luồng chính
      chạy tốt
- [ ] Không có tiêu chí nào ở trạng thái "chưa chạy được"
<!-- internal -->
- [ ] Báo cáo lần chạy đã nằm trong `artifacts/reports/qc-runs/FT-007/`

## Tiêu chí bị chặn bởi một `DEBT-nnn`

Ngưỡng đã có; thứ còn thiếu là một hợp đồng dữ liệu hoặc một phần nền tảng chưa dựng. Không được
đánh dấu *đạt*, và cũng không được đánh dấu *trượt*.

| Tiêu chí | Món nợ | Trạng thái | Ra khỏi trạng thái này khi |
|---|---|---|---|
| QC-27.1 | [`DEBT-025`](../../devlog/debts-ledger.md) | **chưa chạy được** | Có tập câu thoại tiếng Việt được phê duyệt để đo tỷ lệ nhận diện — có một bản nháp 54 câu chờ chủ dự án duyệt, chưa phải bản chính thức |

**Đã ra khỏi bảng này:** `QC-25.1`/`QC-25.2` (`DEBT-064`, đóng ở B3 — `EventHub` tự kiểm bối cảnh
trước khi giao Candidate cho S6, đo qua một uvicorn thật trên `<db>_test` cô lập, xem
`tests/FT-007-.../test_distribution_qc.py`); `QC-01.1`/`QC-01.2`/`QC-30.1` (`DEBT-021`, đóng ở plan P25 — `assistantMode`,
`assistantAvailable` và `systemState` đều đã có và đã được S5 đọc); `QC-11.1`/`QC-11.2` (`DEBT-022`
nửa Audio/Call, đóng ở plan P25 T8); `QC-12.1`/`QC-12.2` (`DEBT-022` nửa Safety/System Alert, đóng
ở plan P27 qua [ADR-0029](../../adr/0029-canh-bao-an-toan-la-trang-thai-xe-khong-phai-guardrail.md));
`QC-02.1`/`QC-02.2`/`QC-18.2`/`QC-26.1`/`QC-31.1` (phần còn lại của `DEBT-023` sau bổ sung P26, đóng
hẳn ở plan P28 — S7 Shared Memory thật qua `remember`/`find_by_dedup_key`/`versioned_snapshot`'s
`duplicateCandidate`, và Candidate được lưu lại để `/respond` phát hiện `candidate_expired`).

Tiêu chí trượt mà được chấp nhận có điều kiện thì phải mở một dòng `DEBT-nnn` trong
[ledger](../../devlog/debts-ledger.md) và ghi số hiệu đó vào báo cáo.

[^qc-15-1]: [`DEBT-030`](../../devlog/debts-ledger.md).
<!-- internal -->
