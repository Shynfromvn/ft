# [SYS2] Khuyến nghị theo trạng thái pin

## Lịch sử thay đổi (Change History)

| No. | Phiên bản | Ngày | Mô tả thay đổi | Lý do | Người viết | Người review | Hồ sơ review | Người phê duyệt | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1 | 12 Aug 2026 | Khởi tạo tài liệu | Khởi tạo tài liệu | ChiTU2 | | | | |
| 2 | 0.1 | 25 Aug 2026 | Nhận nguyên văn làm tài liệu BA của FT-007 trong repo `proactive-agent`. Bổ sung mục *Mã yêu cầu dùng trong repo* ở Phụ lục | Đồng bộ tài liệu tính năng về đúng bản gốc của BA | trinq | | | trinq | Toàn bộ nội dung UC-01 và NFR giữ **nguyên văn**, không sửa một câu nào. Phần thêm vào nằm gọn trong Phụ lục |

---

## Hướng dẫn chung về tài liệu (General Document Guidelines)

### Mục đích (Purpose)

### Phạm vi (Scope)

### Định nghĩa & Từ viết tắt (Definitions & Abbreviations)

tu

| # | Thuật ngữ | Định nghĩa |
|---|---|---|
| 1 | SoC | State of Charge (Mức pin / trạng thái tích điện) |
| 2 | MHU | Multimedia Head Unit (Đầu máy đa phương tiện) |
| 3 | ADAS | Advanced Driver Assistance Systems (Hệ thống hỗ trợ lái tiên tiến) |
| 4 | CTA | Call To Action (Nút/lời kêu gọi hành động) |
| 5 | ECU | Electric Control Unit (Bộ điều khiển điện tử) |

---

## Yêu cầu chức năng và kỹ thuật (Functional and Technical Requirements)

### Yêu cầu nghiệp vụ (Business Requirements)

| Yêu cầu Sys1 | UC_ID | Use Case |
|---|---|---|
| Khuyến nghị chế độ vận hành dựa trên trạng thái pin | UC-01 | Khuyến nghị chế độ vận hành dựa trên trạng thái pin |

---

## UC-01: Khuyến nghị chế độ vận hành dựa trên trạng thái pin

### 1. Mô tả (Description)

ViTa chủ động theo dõi dung lượng pin và hành trình hiện tại để gợi ý chuyển sang Eco Mode. Mục tiêu là giúp người dùng kéo dài quãng đường di chuyển và bảo vệ tuổi thọ pin, đồng thời vẫn duy trì ưu tiên tuyệt đối cho các giới hạn an toàn bắt buộc của xe.

- **Ngưỡng cảnh báo mềm (Soft Warning Threshold) (SoC = 20%):** ViTa chủ động gợi ý chuyển sang Eco Mode để kéo dài quãng đường. Gợi ý này bị chặn nếu Navigation xác định khoảng cách còn lại tới điểm đến — dù là nhà hay trạm sạc — nhỏ hơn 5km.

### 2. Điều kiện tiên quyết (Preconditions)

- **Kết nối:** Xe có kết nối internet đang hoạt động (Chỉ hoạt động khi Online).
- **Trạng thái trợ lý:** ViTa đang ở trạng thái Available.
- **Chế độ trợ lý (Assistant Mode):** Balanced hoặc Proactive.
- **Trạng thái xe (Vehicle State):** Parked hoặc Driving.
- **Độ tươi của dữ liệu (Data Freshness):** Dữ liệu SoC và drive-mode từ S10/ECU phải đáp ứng chính sách độ tươi đã được phê duyệt, định nghĩa trong bảng NFR.

### 3. Điều kiện kích hoạt (Trigger)

S5 phát hiện SoC đã giảm xuống ≤20% (đi qua ngưỡng — threshold-crossing) dựa trên dữ liệu telemetry do S10 cung cấp, HOẶC một chuyến đi mới bắt đầu / lộ trình thay đổi trong khi SoC đã ở mức ≤20%.

### 4. Luồng chính / Luồng người dùng (Main Flow / User flow)

- **Bước 1: S10 → S5 — Tiếp nhận sự kiện SoC.** S10 gửi dữ liệu SoC thời gian thực tới S5, bao gồm giá trị SoC, trạng thái drive-mode hiện tại, timestamp và source metadata. Dữ liệu kích hoạt SoC phải đủ tươi theo chính sách độ tươi đã được phê duyệt.

- **Bước 2: S5 — Xác thực điều kiện kích hoạt.** S5 xác thực rằng SoC = 20%, xe chưa ở Eco Mode, và các trường bắt buộc đều hợp lệ. Nếu SoC, trạng thái drive-mode, timestamp hoặc source metadata bị cũ, thiếu hoặc không nhất quán, S5 không tạo Candidate.

- **Bước 3:** S5 truy xuất S7 Shared Memory để kiểm tra mức chiếm dụng attention-window, kết quả của khuyến nghị Eco gần nhất, trạng thái Candidate trùng lặp, và mọi lịch sử chặn (suppression history). Nếu S7 Memory không trả về snapshot hợp lệ trong ngưỡng NFR, S5 fail closed (dừng an toàn, không tạo Candidate).

- **Bước 4:** S5 kiểm tra bối cảnh Navigation / bản đồ lộ trình để xác định khoảng cách còn lại hiện tại từ xe tới điểm đến đang hoạt động, tính bằng ki-lô-mét, và liệu điểm đến đó có được đánh dấu là Nhà (Home) hay trạm sạc hay không. Nếu Navigation xác nhận khoảng cách còn lại tới Nhà hoặc một trạm sạc phù hợp nhỏ hơn 5 km, S5 chặn khuyến nghị Eco và ghi nhận `proximity_suppressed`. Nếu bối cảnh lộ trình bị thiếu, cũ hoặc không nhất quán, S5 áp dụng chính sách fail-closed đã được phê duyệt.

- **Bước 5: S5 — Xác thực điều kiện đủ của Candidate, kiểm tra các cổng chủ động (proactive gate) và phân loại.**
  - **Đầu vào:** Trigger, S7 Memory và các kiểm tra chặn theo Navigation đã vượt qua.
  - **Cổng điều kiện đủ (Eligibility gates):** ViTa Available; Assistant Mode = Balanced/Proactive; Network = Online; Vehicle State = Parked/Driving; System State = Normal; xe chưa ở Eco Mode.
  - **Kiểm tra chặn (Blocking checks):** Không có Safety/System Alert, không có cảnh báo/can thiệp ADAS, không có cuộc gọi đang diễn ra, không có tương tác ưu tiên cao hơn, và không có xung đột attention-window.
  - **Kiểm tra dữ liệu (Data checks):** SoC, trạng thái drive-mode, kết quả khoảng cách lộ trình, timestamp, source metadata và thời hạn Candidate (Candidate expiry) đều tươi, hợp lệ và nhất quán.
  - **Kiểm tra bộ nhớ (Memory checks):** S5 xác nhận không có Candidate Eco đang hoạt động bị trùng và không có kết quả gần đây mâu thuẫn trong Shared Memory.
  - **Fail-closed:** Nếu bất kỳ cổng nào không đạt, S5 không tạo Candidate và ghi log một mã lý do, ví dụ `assistant_mode_not_allowed`, `offline`, `safety_preempted`, `call_active`, `data_stale`, `invalid_payload`, `duplicate_candidate`, `candidate_expired`, hoặc `already_in_eco_mode`.
  - **Phân loại (Classification):** Nếu tất cả các cổng đều đạt, S5 tạo một Candidate hợp lệ, được phân loại là Direct-impact, Topic = Energy and Charging.
  - **Ghi chú chính sách:** Trần tần suất tiện ích (Utility frequency cap) / khoảng nghỉ (cooldown) không áp dụng, nhưng S5 vẫn ghi nhận phản hồi của người dùng và lịch sử chặn để phục vụ audit, chống trùng lặp và các quyết định chính sách trong tương lai.

- **Bước 6:** Nếu tất cả các kiểm tra đều đạt, S5 tạo một Candidate và gửi tới S7 kèm theo Candidate ID, giá trị SoC, trạng thái drive-mode, kết quả chặn theo lộ trình, phân loại Candidate, Topic, tham chiếu nguồn dữ liệu/độ tươi, tham chiếu độ tin cậy/chính sách, thời hạn (expiry), Response Type khuyến nghị = SUGGEST, và hợp đồng xác nhận bắt buộc (required confirmation contract) cho việc chuyển sang Eco Mode.

- **Bước 7:** S7 điều phối bối cảnh toàn cục và định tuyến Candidate tới S6 chỉ khi việc phân phối vẫn còn hợp lệ.

- **Bước 8: S6 thực hiện xác thực thời gian thực lần cuối ngay trước khi phân phối.**
  - **Driving:** S6 phân phối SUGGEST dạng chỉ-giọng-nói (Voice-only), ngắn gọn. Không hiển thị hoặc chấp nhận popup, Answer Card, CTA, Mascot, Text chi tiết, danh sách, biểu mẫu hay thao tác chạm cho khuyến nghị chủ động này.
  - **Parked:** S6 có thể phân phối Voice kèm một Answer Card nêu lợi ích của Eco Mode và các điều khiển xác nhận bằng Voice/Touch, nếu HMI khả dụng và không có tương tác ưu tiên cao hơn đang hoạt động.
  - **Parked → Driving trong khi đang hiển thị:** S6 ẩn Answer Card, CTA, Mascot, Text chi tiết, biểu mẫu hoặc danh sách trong vòng ≤ 100 ms và chỉ tiếp tục bằng Voice ngắn gọn nếu Candidate vẫn còn hợp lệ và an toàn. Không được thu nhỏ thẻ thành một thẻ chữ nhỏ.
  - **Call:** Cuộc gọi chặn Voice và Sound. Driving + Call nghĩa là không có phương án thay thế bằng UI/Text. Parked + Call có thể dùng UI/Text chỉ khi nó không che giao diện cuộc gọi và thời hạn Candidate còn cho phép.

- **Bước 9: Xử lý phản hồi của người dùng.**
  - **Xác nhận bằng giọng nói:** Nếu người dùng xác nhận rõ ràng, ví dụ "Có", "Chuyển sang Eco", hoặc "Bật Eco đi", S6 coi đó là CONFIRM cho việc chuyển Eco Mode và yêu cầu ECU/bộ điều khiển drive-mode chuyển sang Eco.
  - **Xác nhận bằng thao tác chạm:** Xác nhận bằng Touch chỉ được phép khi Parked và Answer Card/CTA còn hợp lệ.
  - **Từ chối hoặc huỷ:** Nếu người dùng nói "Không", "Để sau", "Bỏ qua", hoặc huỷ, S6 kết thúc tương tác, giữ nguyên chế độ vận hành hiện tại, và ghi nhận Candidate là rejected/snoozed theo intent được hỗ trợ.
  - **Không phản hồi:** Nếu không phát hiện phản hồi được hỗ trợ nào trong vòng 6 giây, S6 kết thúc tương tác, giữ nguyên chế độ vận hành hiện tại, và ghi nhận Candidate là ignored.
  - **Làm rõ:** Nếu người dùng hỏi vì sao, S6 có thể trả lời ngắn gọn bằng nội dung đã được phê duyệt. Khi đang Driving, phần làm rõ phải giữ ngắn gọn và chỉ bằng Voice; khi Parked, chi tiết có thể được hiển thị trên Answer Card nếu còn hợp lệ.
  - **Ngắt bằng một yêu cầu khác:** S6 dừng TTS hiện tại trong ngưỡng độ trễ barge-in mục tiêu, ghi nhận kết quả của Candidate Eco nếu đầu ra đã bắt đầu, và xử lý intent mới nhất của người dùng.

- **Bước 10: Thực thi và trạng thái.**
  - Nếu việc chuyển Eco thành công và ECU xác nhận chế độ mới, S6 trả về STATUS. Khi đang Driving, STATUS chỉ bằng Voice và ngắn gọn.
  - Nếu thực thi thất bại, S6 trả về STATUS Error, không báo Success, giữ nguyên chế độ vận hành hiện tại, và cung cấp phương án khôi phục an toàn nhất mà Vehicle State cho phép. Khi đang Driving, phần khôi phục chỉ bằng Voice; không hiển thị hướng dẫn thao tác thủ công trên HMI.

- **Bước 11:** S6 gửi kết quả cuối cùng tới S7 Memory, bao gồm Candidate ID, giá trị SoC, drive-mode trước/sau, kết quả chặn theo lộ trình nếu có, Vehicle State, Assistant Mode, Audio State, kênh đầu ra, nhãn phản hồi người dùng, kết quả thực thi, timestamp và mã lý do. S7 cập nhật Shared Memory để chống trùng lặp, phục vụ việc chặn trong tương lai và audit.

### 5. Điều kiện hậu (Postconditions)

- Nếu đã được phân phối, khuyến nghị Eco được ghi nhận với trạng thái cuối cùng: acted, rejected, snoozed, ignored, suppressed, expired, failed, hoặc completed.
- Nếu người dùng xác nhận tường minh và ECU xác nhận thành công, xe ở trạng thái Eco Mode và ViTa báo STATUS thành công một cách ngắn gọn.
- Nếu người dùng từ chối, không phản hồi, hoặc Candidate hết hạn, không có việc chuyển drive-mode nào được thực thi và chế độ vận hành hiện tại được giữ nguyên.
- Nếu thực thi thất bại, ViTa báo STATUS Error và không ghi nhận thành công giả (false success).
- Mọi sự kiện tạo Candidate, chặn, phân phối, phản hồi người dùng, thực thi và cập nhật bộ nhớ đều truy vết được trong log S7/audit.

### 6. Luồng ngoại lệ (Exception Flows)

- **E01 — Dữ liệu thiếu, cũ hoặc không nhất quán:** Nếu SoC, drive-mode, timestamp, bối cảnh chặn theo lộ trình, hoặc source metadata bị thiếu, cũ hoặc không nhất quán, S5 không được tạo Candidate. Ghi nhận `data_missing`, `data_stale`, hoặc `invalid_payload`.
- **E02 — S7 Memory không khả dụng hoặc không hợp lệ:** Nếu S7 Memory timeout, trả về bối cảnh không hợp lệ/hết hạn/mâu thuẫn, hoặc không thể xác nhận trạng thái attention-window/trùng lặp, S5 fail closed và không tạo Candidate. Ghi nhận `memory_unavailable`, `memory_timeout`, `memory_expired`, hoặc `memory_inconsistent`.
- **E03 — Bối cảnh Navigation không khả dụng hoặc không hợp lệ:** Nếu bối cảnh Navigation / bản đồ lộ trình không khả dụng, bị cũ, không nhất quán, hoặc không thể xác định khoảng cách còn lại và loại điểm đến, S5 fail closed và không tạo Candidate. Ghi nhận `navigation_unavailable`, `navigation_stale`, `navigation_inconsistent`, hoặc `destination_type_unknown`.
- **E04 — Assistant Mode không được phép:** Nếu Assistant Mode không phải Balanced hoặc Proactive, bao gồm cả Quiet hay chế độ không xác định, S5 chặn Candidate và ghi nhận `assistant_mode_not_allowed`.
- **E05 — Safety/System Alert đang hoạt động:** Warning tạm dừng hoặc chặn Voice theo UX Principles. Intervention dừng toàn bộ Voice/Sound của ViTa và gỡ bỏ nội dung hiển thị không còn hợp lệ, không tự động lặp lại. ViTa không được cạnh tranh với các cảnh báo Safety/ADAS.
- **E06 — Cuộc gọi đang diễn ra chặn đầu ra:** Cuộc gọi chặn Voice và Sound. Khi Driving + Call, S6 không được hiển thị popup/text thay thế; hoãn hoặc để Candidate hết hạn dựa trên expiry. Khi Parked + Call, UI/Text chỉ được phép nếu nó không che giao diện cuộc gọi và thời hạn Candidate vẫn cho phép phân phối.
- **E07 — Vehicle State làm nội dung hiển thị mất hiệu lực:** Nếu Parked chuyển sang Driving trong khi Card/CTA đang hiển thị, S6 ẩn UI hiển thị/chạm trong vòng ≤ 100 ms và chỉ tiếp tục bằng Voice ngắn gọn được phép nếu an toàn và hợp lệ.
- **E08 — Thực thi chuyển Eco thất bại:** Nếu ECU/bộ điều khiển drive-mode từ chối hoặc thực hiện thất bại việc chuyển chế độ, S6 báo STATUS Error, không báo Success, và ghi nhận `execution_failed` kèm nguyên nhân nếu có.
- **E09 — Candidate hết hạn:** Nếu Candidate đạt tới thời hạn trước khi được phân phối, xác nhận hoặc thực thi, S6 dừng tương tác, gỡ bỏ đầu ra không còn hợp lệ, và ghi nhận `candidate_expired`.
- **E10 — Phân phối đầu ra thất bại:** Nếu việc phát Voice, hiển thị Card khi Parked, hoặc xác nhận từ MHU thất bại, S6 không được giả định là đã phân phối thành công. Ghi nhận `delivery_failed` và tránh việc thử lại trùng lặp gây mất an toàn khi đang Driving.

### 7. Luồng thay thế (Alternative flow)

- **A01 — Xe đang Parked tại thời điểm phân phối:** Nếu SoC chạm ngưỡng khi đang Parked hoặc Candidate được hoãn tới khi Parked, S6 có thể hiển thị Answer Card kèm phần giải thích về Eco Mode và một CTA xác nhận. Xác nhận bằng Touch chỉ được phép khi Parked.
- **A02 —** S5 chặn khuyến nghị một cách im lặng khi Navigation xác nhận điểm đến đang hoạt động là Nhà hoặc một trạm sạc phù hợp và khoảng cách còn lại nhỏ hơn 5 km. Nếu điểm đến là một nơi khác, S5 có thể tiếp tục luồng khuyến nghị ngay cả khi khoảng cách còn lại nhỏ hơn 5 km, miễn là tất cả các cổng khác đều đạt.
- **A03 — Người dùng hỏi để làm rõ:** S6 giải thích ngắn gọn rằng Eco Mode có thể giảm tiêu thụ năng lượng và giúp kéo dài quãng đường. Khi đang Driving, giữ câu trả lời ngắn gọn và chỉ bằng Voice; khi Parked, có thể hiển thị thêm chi tiết.

### 8. Quy tắc nghiệp vụ (Business Rule)

- **BR-01 — Ngưỡng kích hoạt:** S5 đánh giá khuyến nghị Eco Mode khi SoC chạm mức 20% và xe chưa ở Eco Mode.
- **BR-02 — Phân loại Candidate:** Khuyến nghị này thuộc loại Direct-impact dưới Topic "Energy and Charging" vì nó có thể ảnh hưởng tới chuyến đi/quãng đường hiện tại. Nó chỉ được phép tự khởi tạo trong Assistant Mode Balanced hoặc Proactive.
- **BR-03 — Ràng buộc đầu ra khi Driving:** Khi đang Driving, ViTa phải dùng đầu ra chỉ-giọng-nói, ngắn gọn. Không cho phép popup, Answer Card, CTA, Mascot, Text chi tiết, danh sách, biểu mẫu hay thao tác chạm cho khuyến nghị chủ động này.
- **BR-04 — Parked cho phép xác nhận bằng hình ảnh:** Khi Parked, có thể dùng Answer Card và Touch CTA nếu HMI khả dụng và không có tương tác ưu tiên cao hơn chặn đầu ra.
- **BR-05 — Ưu tiên an toàn:** Safety/System Alert ghi đè UC này. Warning có thể tạm dừng/chặn Voice; Intervention dừng Voice/Card mà không tự động lặp lại. ViTa không bắt chước hay cạnh tranh với các cảnh báo Safety/ADAS.
- **BR-06 — Ưu tiên cuộc gọi:** Cuộc gọi chặn Voice và Sound. Khi Driving + Call, không được chuyển nội dung chủ động sang UI/Text.
- **BR-07 — Bắt buộc xác nhận tường minh:** Việc chuyển Eco Mode ảnh hưởng tới vận hành của xe và không được thực thi tự động. S6 chỉ thực thi việc chuyển chế độ sau khi người dùng xác nhận tường minh qua một kênh được phép.
- **BR-08 — Không báo thành công giả:** ViTa chỉ được báo Success sau khi nhận được xác nhận chuyển Eco Mode thành công từ bộ điều khiển của xe.
- **BR-09 — Chặn theo khoảng cách gần:** S5 chỉ chặn khuyến nghị khi Navigation xác nhận điểm đến đang hoạt động là Nhà hoặc một trạm sạc phù hợp và khoảng cách còn lại nhỏ hơn 5 km. Nếu điểm đến là một nơi khác, S5 có thể tiếp tục luồng khuyến nghị ngay cả khi khoảng cách còn lại nhỏ hơn 5 km, miễn là tất cả các cổng khác đều đạt. Chỉ ghi nhận `proximity_suppressed` cho trường hợp chặn theo Nhà/trạm sạc.
- **BR-10 — Không tự động trừng phạt khi bị từ chối nhiều lần:** Hệ thống không được tắt Voice hay thay thế đầu ra Voice khi Driving bằng một biểu tượng HMI tĩnh sau nhiều lần bị từ chối, trừ khi một quy tắc UX/Product trong tương lai định nghĩa tường minh hành vi đó. Lịch sử từ chối có thể được lưu và dùng để đề xuất thay đổi Assistant Mode theo UX Principles.
- **BR-11 — S7 Memory fail-closed:** Việc tạo Candidate đòi hỏi S7 Shared Memory hợp lệ cho attention-window và việc kiểm soát trùng lặp/lặp lại. Bộ nhớ thiếu hoặc không hợp lệ dẫn tới việc chặn theo nguyên tắc fail-closed cho lần đánh giá đó.
- **BR-12 — Khả năng truy vết (Auditability):** Mọi việc tạo Candidate, chặn, định tuyến, phân phối, phản hồi người dùng, kết quả thực thi, thất bại, hết hạn và cập nhật bộ nhớ đều phải được ghi log kèm giai đoạn chịu trách nhiệm, timestamp, Candidate ID, Vehicle State, Assistant Mode, kênh đầu ra và mã lý do.

### 9. UI/UX

#### 9.1 Voice UX

| # | Kịch bản | Luồng tương tác | Ví dụ (TTS) |
|---|---|---|---|
| 1 | SoC chạm 20% khi đang Driving, bao gồm cả khi điểm đến là một nơi khác trong phạm vi 5 km | SUGGEST loại Direct-impact. Không chặn chỉ dựa trên khoảng cách đối với các điểm đến không phải Nhà/không phải trạm sạc. Chỉ Voice, ngắn gọn, không có touch CTA hay Answer Card. Chỉ phân phối sau khi tất cả các cổng S5/S7/S6 đều đạt. | ViTa: "Pin còn 20%. Chuyển sang Eco Mode có thể giúp tiết kiệm pin hơn. Bạn muốn chuyển không?" |
| 2 | Các trường hợp không có Candidate / không có đầu ra giọng nói | Không phát giọng nói khi S5 không tạo Candidate, khi bối cảnh Navigation không hợp lệ, hoặc khi cuộc gọi chặn Voice/Sound trong lúc Driving. | Không có đầu ra giọng nói. |
| 3 | Người dùng xác nhận | Chỉ thực thi sau khi có xác nhận tường minh; chỉ báo STATUS sau khi bộ điều khiển xác nhận thành công. | ViTa: "Đã chuyển sang Eco Mode." |
| 4 | Thực thi thất bại | STATUS Error; không báo thành công giả; phương án khôi phục tuân theo Vehicle State. | ViTa: "Mình chưa chuyển được sang Eco Mode. Bạn thử lại khi an toàn nhé." |

#### 9.2 Visual UX

| # | Màn hình/Trạng thái | Thành phần hiển thị | Quy tắc |
|---|---|---|---|
| 1 | Driving | Không có UI hiển thị nào của ViTa cho khuyến nghị chủ động này. | Chỉ Voice nếu hợp lệ và an toàn. Không có Answer Card, popup, Toast, CTA, Mascot, text chi tiết, danh sách, biểu mẫu hay UI chuyển tiếp bằng thao tác chạm. |
| 2 | Parked | Answer Card có thể hiển thị SoC, gợi ý Eco Mode, lợi ích ngắn gọn, và các CTA xác nhận: "Chuyển sang Eco Mode" và "Để sau". | Xác nhận bằng Touch chỉ được phép khi Parked. Nếu xảy ra Safety Alert, cuộc gọi, hoặc chuyển sang Driving, tuân theo các quy tắc của luồng chính. |
| 3 | Trạng thái chuyển chế độ | Hiển thị một trạng thái ngắn sau khi người dùng xác nhận: "Đã chuyển sang Eco Mode" hoặc "Chưa chuyển được sang Eco Mode". | Chỉ hiển thị thành công sau khi bộ điều khiển xác nhận. Khi thất bại, không báo thành công; giữ nguyên chế độ vận hành hiện tại và tuân theo các quy tắc của luồng chính. |

### 10. Tiêu chí nghiệm thu (Acceptance Criteria)

| AC ID | Tên AC | Mô tả AC |
|---|---|---|
| AC-01 | Chỉ tạo Candidate khi toàn bộ bối cảnh bắt buộc đều hợp lệ | **Given** ViTa đang Available, Assistant Mode là Balanced hoặc Proactive, Network là Online, dữ liệu SoC/drive-mode còn tươi, bối cảnh Navigation hợp lệ, S7 Memory trả về snapshot hợp lệ, và không có cổng Safety/Audio/attention-window nào chặn tương tác. **When** SoC chạm 20% và xe chưa ở Eco Mode. **Then** S5 tạo một Candidate khuyến nghị Eco với phân loại Direct-impact, Topic = Energy and Charging, các ràng buộc đầu ra, thời hạn, và hợp đồng xác nhận. |
| AC-02 | Không tạo Candidate khi S7 Memory không hợp lệ | **Given** S5 cần S7 Shared Memory cho attention-window, chống trùng lặp, hoặc kiểm soát lặp lại. **When** S7 Memory timeout, không khả dụng, hết hạn, không hợp lệ, hoặc không nhất quán. **Then** S5 fail closed, không tạo Candidate, và ghi nhận mã lý do lỗi bộ nhớ tương ứng. |
| AC-03 | Chặn theo khoảng cách gần | **Given** SoC chạm 20% và Navigation xác nhận điểm đến đang hoạt động là Nhà hoặc một trạm sạc phù hợp với khoảng cách còn lại nhỏ hơn 5 km. **When** S5 đánh giá Candidate. **Then** S5 chặn khuyến nghị một cách im lặng, không tạo Candidate, và ghi nhận `proximity_suppressed`. |
| AC-04 | Điểm đến không phải Nhà trong phạm vi 5 km vẫn có thể khuyến nghị | **Given** SoC chạm 20%, Navigation xác nhận điểm đến đang hoạt động không phải Nhà hay trạm sạc, và khoảng cách còn lại nhỏ hơn 5 km. **When** tất cả các cổng S5/S7/S6 khác đều đạt. **Then** S5 có thể tiếp tục luồng khuyến nghị Eco và không được chặn chỉ dựa trên khoảng cách. |
| AC-05 | Không tạo Candidate khi bối cảnh Navigation không hợp lệ | **Given** bối cảnh Navigation / bản đồ lộ trình là bắt buộc cho việc đánh giá khoảng cách gần. **When** bối cảnh Navigation không khả dụng, bị cũ, không nhất quán, hoặc không thể xác định khoảng cách còn lại hay loại điểm đến. **Then** S5 fail closed, không tạo Candidate, và ghi nhận mã lý do lỗi navigation tương ứng. |
| AC-06 | Đầu ra khi Driving chỉ là giọng nói | **Given** một Candidate Eco hợp lệ được phân phối trong khi xe đang Driving. **When** S6 bắt đầu xuất đầu ra. **Then** S6 chỉ phân phối Voice ngắn gọn và không hiển thị popup, Answer Card, Toast, Mascot, CTA, Text chi tiết, biểu mẫu, danh sách hay UI thao tác chạm. |
| AC-07 | Đầu ra khi Parked có thể bao gồm Answer Card | **Given** một Candidate Eco hợp lệ được phân phối trong khi xe đang Parked. **When** S6 xác thực đầu ra. **Then** S6 có thể hiển thị một Answer Card với các CTA tiếng Việt "Chuyển sang Eco Mode" và "Để sau", và có thể chấp nhận xác nhận bằng Touch trong khi thẻ còn hợp lệ. |
| AC-08 | Bắt buộc xác nhận tường minh trước khi thực thi | **Given** một khuyến nghị Eco đã được phân phối. **When** người dùng chưa xác nhận rõ ràng qua một kênh được phép. **Then** S6 không được yêu cầu bộ điều khiển xe chuyển sang Eco Mode. |
| AC-09 | Chỉ báo chuyển chế độ thành công sau khi bộ điều khiển xác nhận | **Given** người dùng xác nhận tường minh việc chuyển Eco. **When** ECU/bộ điều khiển drive-mode xác nhận Eco Mode đang hoạt động. **Then** ViTa báo STATUS thành công và ghi nhận kết quả completed/acted. |
| AC-10 | Thực thi thất bại không được coi là thành công | **Given** người dùng xác nhận việc chuyển Eco. **When** ECU/bộ điều khiển drive-mode từ chối hoặc thực hiện thất bại việc chuyển chế độ. **Then** ViTa báo STATUS Error, không báo Success, giữ nguyên chế độ vận hành hiện tại, và ghi nhận `execution_failed`. |
| AC-11 | Cuộc gọi đang diễn ra chặn đầu ra khuyến nghị khi Driving | **Given** SoC chạm 20% trong khi Driving và Audio State là Call. **When** S6 xác thực đầu ra. **Then** Voice và Sound bị chặn, hệ thống không hiển thị popup tĩnh hay phương án thay thế bằng Text trên HMI, và Candidate được hoãn hoặc để hết hạn theo expiry. |
| AC-12 | Safety/System Alert chiếm quyền ưu tiên trước khuyến nghị | **Given** một Candidate Eco đang chờ hoặc đang được phân phối. **When** một Safety/System Alert loại Warning hoặc Intervention trở nên hoạt động. **Then** ViTa nhường quyền theo UX Principles, không cạnh tranh với đầu ra Safety của xe, và ghi nhận lý do bị chiếm quyền (preemption). |
| AC-13 | Chuyển Parked sang Driving gỡ bỏ UI hiển thị/chạm | **Given** một Answer Card, CTA, Mascot, Text chi tiết, biểu mẫu hoặc danh sách Eco đang được hiển thị khi Parked. **When** xe chuyển sang Driving. **Then** S6 ẩn toàn bộ UI hiển thị/chạm trong vòng ≤ 100 ms, không thu nhỏ thẻ, và chỉ tiếp tục bằng Voice ngắn gọn được phép nếu hợp lệ và an toàn. |
| AC-14 | Người dùng từ chối hoặc hết giờ thì không thực thi đổi chế độ | **Given** khuyến nghị Eco đã được phân phối. **When** người dùng từ chối, nói "Để sau", huỷ, hoặc không phát hiện phản hồi được hỗ trợ nào trong vòng 6 giây. **Then** S6 kết thúc tương tác, giữ nguyên chế độ vận hành hiện tại, và ghi nhận rejected/snoozed/ignored tuỳ trường hợp. |
| AC-15 | Không chấp nhận xác nhận mơ hồ | **Given** phản hồi của người dùng không rõ ràng, bị nhiễu, chồng tiếng, hoặc không ánh xạ được sang một intent xác nhận đã được phê duyệt. **When** S6 đánh giá phản hồi. **Then** S6 không được thực thi việc chuyển Eco và chỉ được VERIFY nếu Vehicle/Audio State hiện tại cho phép. |
| AC-16 | Bản ghi audit đầy đủ | **Given** bất kỳ sự kiện đánh giá hay sự kiện vòng đời Candidate nào xảy ra, bao gồm created, suppressed, delivered, acted on, rejected, ignored, expired, failed, hoặc preempted. **When** việc đánh giá hoặc tương tác đạt tới trạng thái cuối cùng. **Then** S6/S7 ghi nhận Candidate ID khi có, SoC, trạng thái drive-mode, Vehicle State, Assistant Mode, Audio State, kênh đầu ra, trạng thái cuối cùng, timestamp và mã lý do. |

### 11. Phụ thuộc (Dependency)

| # | Phụ thuộc | Mô tả |
|---|---|---|
| 1 | Telemetry xe từ S10 qua TBox | S10 thu thập toàn bộ telemetry cần thiết của xe từ TBox, bao gồm SoC, trạng thái drive-mode hiện tại, Vehicle State, trạng thái Safety/ADAS/System Alert, trạng thái Audio/Call, trạng thái mạng/kết nối, timestamp và source metadata phục vụ xác thực điều kiện kích hoạt, kiểm soát cổng, xác thực trạng thái thực thi và audit. |
| 2 | Bối cảnh Navigation / lộ trình | Cung cấp loại điểm đến đang hoạt động, khoảng cách còn lại, độ tươi của lộ trình, và mức độ phù hợp của trạm sạc phục vụ việc đánh giá khoảng cách gần. |
| 3 | S7 Shared Memory | Cung cấp bộ nhớ hợp lệ, có phiên bản, chưa hết hạn cho trạng thái attention-window, chống trùng lặp, kết quả gần đây, lịch sử chặn, và lưu trữ audit. |
| 4 | S7 Context Orchestration | Điều phối bối cảnh toàn cục và định tuyến các Candidate hợp lệ tới S6 chỉ khi việc phân phối vẫn hợp lệ, an toàn và còn trong thời hạn. |
| 5 | S6 / MHU / HMI | Thực hiện xác thực lần cuối, phân phối đầu ra Voice hoặc đầu ra hiển thị khi Parked được phép, ghi nhận phản hồi người dùng, yêu cầu chuyển Eco Mode sau khi có xác nhận tường minh, và báo cáo trạng thái. |
| 6 | Telemetry / ghi log audit | Ghi nhận vòng đời Candidate, các lý do chặn/fail-closed, việc phân phối, phản hồi người dùng, kết quả thực thi, và kết quả cuối cùng. |

### 12. Ràng buộc & Giả định (Constraints & Assumptions)

- ASR/TTS và toàn bộ các câu thoại hướng tới người dùng trong giai đoạn này chỉ hỗ trợ tiếng Việt.

---

## Yêu cầu phi chức năng (Non-Functional Requirements)

### Chung (General)

| ID | Chỉ số | Chủ sở hữu | Mô tả | Mục tiêu |
|---|---|---|---|---|
| NFR-01 | Độ tươi của dữ liệu | S10 / S5 | Độ tươi của telemetry từ S10 và bối cảnh Navigation được S5 sử dụng. | S10 lấy SoC từ TBox với SyncType = OnWakeupAndOnChange. Telemetry bắt buộc từ S10 được S5 sử dụng phải cũ không quá 10 giây. Bối cảnh Navigation dùng cho đánh giá khoảng cách gần phải cũ không quá 2 phút. Nếu không, S5 fail closed. |
| NFR-02 | Độ trễ — quyết định Candidate của S5 | S5 | Thời gian từ khi có sẵn bối cảnh bắt buộc còn tươi tới khi tạo hoặc chặn Candidate. | ≤ 1 giây trong điều kiện online bình thường. S7 Memory phải trả về snapshot hợp lệ, có phiên bản, chưa hết hạn trong vòng ≤ 300 ms; nếu không, S5 fail closed. |
| NFR-03 | Độ trễ — định tuyến của S7 | S7 | Thời gian từ khi S7 nhận một Candidate tới khi định tuyến nó tới S6 sau các bước kiểm tra bối cảnh. | ≤ 1 giây trong điều kiện online bình thường. |
| NFR-04 | Độ trễ — xác thực & phân phối của S6 | S6 / MHU | Thời gian từ khi S6 nhận yêu cầu được định tuyến tới khi xác thực lần cuối và xuất đầu ra được phép đầu tiên. | ≤ 1 giây trong điều kiện online bình thường. |
| NFR-05 | Độ trễ — đầu ra đầu-cuối | S5 / S7 / S6 / MHU | Thời gian từ khi S5 tạo Candidate tới đầu ra đầu tiên hướng tới người dùng được phép. | ≤ 3 giây trong điều kiện online bình thường. |
| NFR-06 | Gỡ UI khi chuyển Parked sang Driving | S6 / HMI | Việc gỡ bỏ UI hiển thị/chạm khi Vehicle State đổi sang Driving. | Ẩn UI hiển thị/chạm trong vòng ≤ 100 ms và không thu nhỏ nó thành một thẻ chữ nhỏ. |
| NFR-07 | Độ chính xác — telemetry của S10 | S10 | Độ chính xác của telemetry xe cung cấp cho S5. | Các giá trị SoC, drive-mode, Vehicle State, Audio/Call, Safety/System Alert và kết nối cung cấp cho S5 phải khớp 100% với dữ liệu gốc của TBox tại cùng thời điểm tham chiếu. Các giá trị không hợp lệ hoặc ngoài dải không được sử dụng. |
| NFR-08 | Độ chính xác — điều kiện đủ & quyết định của S5 | S5 | Độ chính xác của logic kích hoạt, chặn, fail-closed và quyết định Candidate. | 100% kết quả tuân thủ quy tắc trong các bài kiểm thử đã được phê duyệt. 0 lần tạo Candidate khi các điều kiện bắt buộc về độ tươi, Navigation, S7 Memory, safety/call, trùng lặp, hoặc các điều kiện tiên quyết bắt buộc không được thoả mãn. |
| NFR-09 | Độ chính xác — định tuyến & bối cảnh của S7 | S7 | Độ chính xác của việc định tuyến payload Candidate và trạng thái bối cảnh tới S6. | Bảo toàn 100% Candidate ID, response type, hợp đồng xác nhận, payload CTA, thời hạn, và trạng thái bối cảnh trong các bài kiểm thử tích hợp. 0 lần định tuyến tới S6 khi bối cảnh ở mức S7 chặn việc phân phối. |
| NFR-10 | Độ chính xác — cập nhật S7 Memory | S7 | Độ chính xác của các bản ghi Shared Memory được dùng cho các quyết định chủ động. | 100% bản ghi bộ nhớ bảo toàn nguồn, loại sự kiện, Candidate ID khi có, timestamp, phiên bản, tính hợp lệ/thời hạn, và metadata kết quả. Không có bản ghi bộ nhớ cũ, trùng lặp hay mâu thuẫn nào được S5 sử dụng. |
| NFR-11 | Độ chính xác — intent & thực thi của S6 | S6 | Độ chính xác của việc xử lý intent Voice/Touch và báo cáo trạng thái thực thi. | Nhận diện intent bằng giọng nói ≥ 95% trên tập câu thoại tiếng Việt đã được phê duyệt. 0 xác nhận Eco dương tính giả. 0 báo cáo thành công dương tính giả; chỉ báo thành công sau khi trạng thái Eco Mode đã được xác nhận. |

---

## Phụ lục (Appendix)

### Tài liệu tham chiếu (Reference)

| # | Tài liệu | Ghi chú |
|---|---|---|
| 1 | `[SYS2] Khuyến nghị theo trạng thái pin`, phiên bản 0.1, ngày 12 Aug 2026, người viết ChiTU2 | Bản gốc. Toàn bộ nội dung từ *Hướng dẫn chung* tới hết bảng NFR ở trên là **bản sao nguyên văn** của tài liệu đó — file này thay thế nó, không đặt cạnh nó |

---

### Trạng thái phê duyệt (Approval status)

| Mục | Giá trị |
|---|---|
| Mã tính năng | FT-007 |
| Trạng thái | đã duyệt |
| Người viết | ChiTU2 (bản gốc) · trinq (nhận vào repo) |
| Người phê duyệt | trinq (chủ dự án) |
| Ngày phê duyệt | 25 Aug 2026 |
| Phạm vi | Đúng UC-01 và mười một NFR ở trên. Không có gì ngoài phần đó thuộc về tính năng này |

---

### Mã yêu cầu dùng trong repo (BA-nn)

Repo `proactive-agent` gọi tên một yêu cầu nghiệp vụ bằng mã `BA-nn`, và mọi tiêu chí nghiệm thu
`QC-nn.m` phải trỏ về đúng một `BA-nn`. Tài liệu này đánh số theo hệ của riêng nó — `AC-nn`,
`NFR-nn`, `BR-nn`, `Enn`, `Ann` — nên bảng dưới đây là **cầu nối giữa hai hệ số hiệu**.

Đây là phần duy nhất được thêm vào tài liệu gốc. Nó **không tạo ra yêu cầu mới**: mỗi dòng chỉ
gán một mã `BA-nn` cho một câu đã có sẵn ở trên, và giữ nguyên nội dung câu đó.

#### Bảng 1 — `BA-nn` gán cho mã nào

| BA-nn | Mã trong tài liệu này | Nội dung |
|---|---|---|
| BA-01 | AC-01 | Chỉ tạo Candidate khi toàn bộ bối cảnh bắt buộc đều hợp lệ |
| BA-02 | AC-02 | Không tạo Candidate khi S7 Memory không hợp lệ |
| BA-03 | AC-03 | Chặn theo khoảng cách gần |
| BA-04 | AC-04 | Điểm đến không phải Nhà trong phạm vi 5 km vẫn có thể khuyến nghị |
| BA-05 | AC-05 | Không tạo Candidate khi bối cảnh Navigation không hợp lệ |
| BA-06 | AC-06 | Đầu ra khi Driving chỉ là giọng nói |
| BA-07 | AC-07 | Đầu ra khi Parked có thể bao gồm Answer Card |
| BA-08 | AC-08 | Bắt buộc xác nhận tường minh trước khi thực thi |
| BA-09 | AC-09 | Chỉ báo chuyển chế độ thành công sau khi bộ điều khiển xác nhận |
| BA-10 | AC-10 | Thực thi thất bại không được coi là thành công |
| BA-11 | AC-11 | Cuộc gọi đang diễn ra chặn đầu ra khuyến nghị khi Driving |
| BA-12 | AC-12 | Safety/System Alert chiếm quyền ưu tiên trước khuyến nghị |
| BA-13 | AC-13 | Chuyển Parked sang Driving gỡ bỏ UI hiển thị/chạm |
| BA-14 | AC-14 | Người dùng từ chối hoặc hết giờ thì không thực thi đổi chế độ |
| BA-15 | AC-15 | Không chấp nhận xác nhận mơ hồ |
| BA-16 | AC-16 | Bản ghi audit đầy đủ |
| BA-17 | NFR-01 | Độ tươi của dữ liệu |
| BA-18 | NFR-02 | Độ trễ — quyết định Candidate của S5 |
| BA-19 | NFR-03 | Độ trễ — định tuyến của S7 |
| BA-20 | NFR-04 | Độ trễ — xác thực và phân phối của S6 |
| BA-21 | NFR-05 | Độ trễ — đầu ra đầu-cuối |
| BA-22 | NFR-06 | Gỡ UI khi chuyển Parked sang Driving |
| BA-23 | NFR-07 | Độ chính xác — telemetry của S10 |
| BA-24 | NFR-08 | Độ chính xác — điều kiện đủ và quyết định của S5 |
| BA-25 | NFR-09 | Độ chính xác — định tuyến và bối cảnh của S7 |
| BA-26 | NFR-10 | Độ chính xác — cập nhật S7 Memory |
| BA-27 | NFR-11 | Độ chính xác — intent và thực thi của S6 |
| BA-28 | BR-10 | Không tự động trừng phạt khi bị từ chối nhiều lần |
| BA-29 | E01 | Dữ liệu thiếu, cũ hoặc không nhất quán |
| BA-30 | E04 | Assistant Mode không được phép |
| BA-31 | E09 | Candidate hết hạn |
| BA-32 | E10 | Phân phối đầu ra thất bại |
| BA-33 | A03 | Người dùng hỏi để làm rõ |
| BA-34 | Bước 9 — *Ngắt bằng một yêu cầu khác* | Barge-in: dừng TTS, ghi nhận kết quả Candidate nếu đầu ra đã bắt đầu, xử lý intent mới nhất |

Mười bốn mã đầu (`BA-01`..`BA-16`) trùng số với `AC-01`..`AC-16` một cách có chủ đích: đọc
`BA-07` là đọc `AC-07`, không phải tra bảng. Bảy mã tiếp theo (`BA-17`..`BA-27`) trùng thứ tự với
`NFR-01`..`NFR-11`. Bảy mã cuối (`BA-28`..`BA-34`) dành cho những câu **có tính bắt buộc nhưng
không có `AC` nào kiểm chứng trực tiếp** — nếu không gán mã, chúng sẽ không có tiêu chí nghiệm
thu nào và sẽ lặng lẽ không được kiểm.

#### Bảng 2 — mỗi mã của tài liệu này được kiểm chứng ở đâu

Bảng này đọc theo chiều ngược lại, để thấy **không mục nào bị bỏ sót**.

| Mã trong tài liệu này | Được kiểm chứng qua |
|---|---|
| Điều kiện tiên quyết (§2) | BA-01, BA-30 |
| Điều kiện kích hoạt (§3) | BA-01 |
| Bước 1 — tiếp nhận sự kiện SoC | BA-01, BA-17, BA-23 |
| Bước 2 — xác thực điều kiện kích hoạt | BA-01, BA-29 |
| Bước 3 — truy xuất S7 Shared Memory | BA-02, BA-18 |
| Bước 4 — kiểm tra bối cảnh Navigation | BA-03, BA-04, BA-05 |
| Bước 5 — cổng điều kiện đủ và phân loại | BA-01, BA-24, BA-28, BA-30 |
| Bước 6 — tạo Candidate | BA-01 |
| Bước 7 — S7 điều phối và định tuyến | BA-19, BA-25 |
| Bước 8 — xác thực lần cuối và phân phối | BA-06, BA-07, BA-11, BA-12, BA-13, BA-20, BA-21, BA-32 |
| Bước 9 — xử lý phản hồi người dùng | BA-08, BA-14, BA-15, BA-27, BA-33, BA-34 |
| Bước 10 — thực thi và trạng thái | BA-09, BA-10 |
| Bước 11 — cập nhật bộ nhớ và audit | BA-16, BA-26 |
| Điều kiện hậu (§5) | BA-09, BA-10, BA-14, BA-16, BA-31 |
| E01 | BA-29 |
| E02 | BA-02 |
| E03 | BA-05 |
| E04 | BA-30 |
| E05 | BA-12 |
| E06 | BA-11 |
| E07 | BA-13, BA-22 |
| E08 | BA-10 |
| E09 | BA-31 |
| E10 | BA-32 |
| A01 | BA-07 |
| A02 | BA-03, BA-04 |
| A03 | BA-33 |
| BR-01 | BA-01 |
| BR-02 | BA-01 |
| BR-03 | BA-06 |
| BR-04 | BA-07 |
| BR-05 | BA-12 |
| BR-06 | BA-11 |
| BR-07 | BA-08 |
| BR-08 | BA-09, BA-10 |
| BR-09 | BA-03, BA-04 |
| BR-10 | BA-28 |
| BR-11 | BA-02 |
| BR-12 | BA-16 |
| UI/UX 9.1 — Voice UX | BA-01, BA-06, BA-09, BA-10 |
| UI/UX 9.2 — Visual UX | BA-06, BA-07, BA-09, BA-10, BA-13 |
| Ràng buộc và giả định (§12) | BA-27 |
| NFR-01 .. NFR-11 | BA-17 .. BA-27 |
| Phụ thuộc 1 (Telemetry S10 qua TBox) | BA-17, BA-23 |
| Phụ thuộc 2 (Bối cảnh Navigation) | BA-05 |
| Phụ thuộc 3 (S7 Shared Memory) | BA-02, BA-26 |
| Phụ thuộc 4 (S7 Context Orchestration) | BA-19, BA-25 |
| Phụ thuộc 5 (S6 / MHU / HMI) | BA-20, BA-27 |
| Phụ thuộc 6 (Telemetry / ghi log audit) | BA-16 |
