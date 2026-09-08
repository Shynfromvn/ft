# [SYS2] Khuyến nghị chế độ vận hành theo trạng thái pin — POC rút gọn

## Lịch sử thay đổi (Change History)

| No. | Phiên bản | Ngày | Mô tả thay đổi | Lý do | Người viết | Người review | Hồ sơ review | Người phê duyệt | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1 | 3 Sep 2026 | Khởi tạo tài liệu | Khởi tạo tài liệu | ChiTU2 | | | | |
| 2 | 0.1 | 8 Sep 2026 | Chuẩn hoá requirement rút gọn vào bố cục BA của repo | Tạo POC độc lập, chỉ giữ luồng tạo Candidate và hiển thị không tương tác | Duong | | | | Bản này không kế thừa các quy tắc Navigation, phản hồi người dùng hoặc thực thi ECU của FT-007 gốc |

---

## Hướng dẫn chung về tài liệu (General Document Guidelines)

### Mục đích (Purpose)

Xác định hành vi của POC khuyến nghị chuyển Eco Mode khi mức pin thấp. POC chỉ đánh giá điều kiện, kiểm tra trùng lặp trong Session History, tạo Candidate và hiển thị nội dung khuyến nghị không tương tác.

### Phạm vi (Scope)

Trong phạm vi: dữ liệu SoC và drive-mode, kết nối mạng, kiểm tra độ tươi, Session History chống trùng lặp, Candidate và UI hiển thị.

Ngoài phạm vi: Navigation, Safety/ADAS, cuộc gọi, Assistant Mode, phản hồi Voice/Touch, timeout phản hồi, thực thi lệnh ECU, xác nhận ECU, và lifecycle sau khi Candidate được hiển thị.

### Định nghĩa & Từ viết tắt (Definitions & Abbreviations)

| # | Thuật ngữ | Định nghĩa |
|---|---|---|
| 1 | SoC | State of Charge — mức pin / trạng thái tích điện |
| 2 | S5 | Dịch vụ cloud đánh giá điều kiện và tạo Recommendation Candidate |
| 3 | S10 | Nguồn telemetry xe cung cấp dữ liệu SoC và drive-mode cho S5 |
| 4 | Candidate | Khuyến nghị được tạo khi toàn bộ điều kiện nghiệp vụ đạt |
| 5 | Session History | Lịch sử khuyến nghị dùng để xác định Candidate Eco tương đương đang chờ phản hồi hoặc đang được xử lý |
| 6 | Eco Mode | Chế độ lái tiết kiệm năng lượng |

---

## Yêu cầu chức năng và kỹ thuật (Functional and Technical Requirements)

### Yêu cầu nghiệp vụ (Business Requirements)

| Yêu cầu Sys1 | UC_ID | Use Case |
|---|---|---|
| Khuyến nghị chế độ vận hành theo trạng thái pin | UC-01 | Khuyến nghị chế độ vận hành theo trạng thái pin |

---

## UC-01: Khuyến nghị chế độ vận hành theo trạng thái pin

### 1. Mô tả (Description)

ViTa chủ động giám sát dung lượng pin và hành trình hiện tại để đề xuất chuyển xe sang Chế độ Eco (Eco Mode). Mục tiêu là giúp người dùng kéo dài quãng đường di chuyển và bảo vệ tuổi thọ pin, đồng thời duy trì sự ưu tiên tuyệt đối cho các giới hạn an toàn bắt buộc của xe. Khi mức pin SoC ≤ 20%, ViTa sẽ chủ động đề xuất chuyển sang Chế độ Eco để kéo dài quãng đường di chuyển. 

### 2. Điều kiện tiên quyết (Preconditions)

- **Kết nối mạng:** Online.
- **Độ tươi dữ liệu:** Dữ liệu SoC và chế độ lái phải đáp ứng chính sách độ tươi được phê duyệt quy định trong bảng Yêu cầu phi chức năng (NFR)

### 3. Điều kiện kích hoạt (Trigger)

S5 – Cloud theo dõi giá trị SoC từ S10, phát hiện giá trị mức pin SoC đã giảm xuống ≤ 20%. 

### 4. Luồng chính / Luồng người dùng (Main Flow / User flow)

- **Bước 1:**: S5 – Cloud theo dõi dữ liệu SoC từ S10. Khi SoC ≤ 20% (thỏa mãn trigger), S5 kiểm tra data freshness theo NFR.

- **Bước 2:** Nếu thỏa mãn trigger và data freshness hợp lệ, S5 truy vấn Session History để lấy lịch sử tương tác trước đó cho mốc này. Nếu đã tồn tại một khuyến nghị cùng chủ đề/mục đích (“chuyển sang chế độ Eco để tiết kiệm năng lượng”) đang ở trạng thái chờ người dùng phản hồi hoặc đang được xử lý → S5 không tạo Candidate trùng lặp. 

- **Bước 3:**     Nếu tất cả các kiểm tra đều thỏa mãn, S5 – Cloud tạo Candidate với:  

- Loại sự kiện: Gửi khuyến nghị chủ động đến người dùng 
- Mã sự kiện: Khuyến nghị chuyển sang chế độ lái Eco khi mức pin thấp 
- Nguồn gửi: S5 
- Nội dung khuyến nghị: “Pin còn 20%. Chuyển sang Eco Mode có thể giúp tiết kiệm pin hơn. Bạn có đồng ý chuyển không?” 
- Hành động khuyến nghị: Chuyển chế độ lái sang Eco 

- **Bước 4:** S5 xử lý thông tin Candidate, hiển thị giao diện với câu hỏi “Pin còn 20%. Chuyển sang Eco Mode có thể giúp tiết kiệm pin hơn. Bạn có đồng ý chuyển không?” và các nút xác nhận cảm ứng (“Đồng ý” và “Không đồng ý”). (Không ấn được)

### 5. Điều kiện hậu (Postconditions)

-     Khi SoC ≤ 20%, xe chưa ở chế độ Eco, tất cả preconditions được đáp ứng, dữ liệu SoC còn trong thời gian freshness quy định, không có điều kiện duplicate, S5 đã tạo Recommendation Candidate với nội dung khuyến nghị chuyển sang chế độ Eco. 

### 6. Luồng ngoại lệ (Exception Flows)

### 7. Luồng thay thế (Alternative Flow)

### 8. Quy tắc nghiệp vụ (Business Rules)

- **BR-01 — Ngưỡng kích hoạt:** S5 đánh giá khuyến nghị Chế độ Eco khi mức pin SoC ≤ 20% và xe hiện tại chưa ở Chế độ Eco. 

### 9. UI/UX

#### 9.1 Voice UX


#### 9.2 Visual UX


### 10. Tiêu chí nghiệm thu (Acceptance Criteria)

| AC ID | Tên AC | Mô tả AC |
|---|---|---|
| AC-01 | Chỉ tạo Candidate khi đầy đủ điều kiện cần thiết | **Given** kết nối mạng online và dữ liệu SoC/drive-mode đáp ứng yêu cầu về độ tươi. **When** SoC ≤ 20% và xe chưa ở Eco Mode. **Then** S5 tạo Candidate với loại sự kiện gửi khuyến nghị chủ động, mã sự kiện khuyến nghị chuyển Eco khi pin thấp, nguồn S5, đúng nội dung “Pin còn 20%. Chuyển sang Eco Mode có thể giúp tiết kiệm pin hơn. Bạn có đồng ý chuyển không?” và hành động khuyến nghị chuyển sang Eco. |
| AC-02 | Không tạo khuyến nghị trùng lặp | **Given** các điều kiện kích hoạt được thoả mãn. **When** Session History cho thấy một khuyến nghị Eco tương tự đang được xử lý hoặc chờ phản hồi. **Then** S5 không tạo Candidate mới. |

### 11. Phụ thuộc (Dependencies)

| # | Phụ thuộc | Mô tả |
|---|---|---|
| 1 | S10 Telemetry (CAN bus / TBox) | Cung cấp dữ liệu SoC và trạng thái drive-mode cho S5. |
| 3 | Session History | Lưu trữ và trả về lịch sử khuyến nghị để S5 kiểm tra trùng lặp. |

### 12. Ràng buộc & Giả định (Constraints & Assumptions)

- ASR/TTS và toàn bộ prompt hướng tới người dùng trong giai đoạn này chỉ hỗ trợ tiếng Việt.

---

## Yêu cầu phi chức năng (Non-Functional Requirements)

### Chung (General)

| ID | Chỉ số | Chủ sở hữu | Mô tả | Mục tiêu |
|---|---|---|---|---|
| NFR-01 | Tần suất dữ liệu | S5 | Đảm bảo tần suất S5 lấy dữ liệu SoC để đánh giá điều kiện khuyến nghị. | S5 lấy dữ liệu SoC: 3 phút một lần. |
| NFR-02 | Độ trễ — quyết định Candidate của S5 | S5 | Thời gian từ khi S5 có đầy đủ dữ liệu đầu vào hợp lệ đến khi hoàn tất quyết định tạo hoặc không tạo Candidate. | ≤ 2,5 giây trong điều kiện kết nối trực tuyến bình thường. |
| NFR-04 | Độ chính xác — điều kiện đủ và quyết định của S5 | S5 | Đảm bảo S5 thực hiện chính xác quy tắc kích hoạt, chặn khuyến nghị và quyết định tạo Candidate. | S5 phải đạt 100% độ chính xác trong việc quyết định tạo hoặc không tạo Candidate theo các quy tắc đã định nghĩa; không tạo Candidate khi không đáp ứng các yêu cầu bắt buộc về kết nối mạng, độ tươi dữ liệu SoC hoặc điều kiện duplicate.  |

---

## Phụ lục (Appendix)

### Tài liệu tham chiếu (Reference)

| # | Tài liệu | Ghi chú |
|---|---|---|
| 1 | Requirement UC-01 “Driving mode recommendation based on battery status”, version 0.1, 3 Sep 2026 | Nguồn của tài liệu BA POC này. |

### Trạng thái phê duyệt (Approval Status)

| Mục | Giá trị |
|---|---|
| Mã tính năng | FT-008 |
| Trạng thái | Draft — chờ xác nhận các điểm chưa được requirement định lượng |
| Người viết | ChiTU2 (requirement nguồn) · Duong (chuẩn hoá vào repo) |
| Người phê duyệt | Chưa có |
| Phạm vi | UC-01, hai AC và ba NFR trong tài liệu này |

### Mã yêu cầu dùng trong repo (BA-nn)

| BA-nn | Mã trong tài liệu này | Nội dung |
|---|---|---|
| BA-01 | AC-01 | Chỉ tạo Candidate khi điều kiện online, dữ liệu hợp lệ, SoC ≤ 20% và chưa ở Eco Mode cùng đạt. |
| BA-02 | AC-02 | Không tạo Candidate Eco trùng lặp theo Session History. |
| BA-03 | Bước 4 / UI/UX 9.2 | Hiển thị hai nút xác nhận ở trạng thái không thao tác được. |
| BA-04 | BR-01 | Dùng ngưỡng SoC ≤ 20% và không đề xuất lại khi xe đã ở Eco Mode. |
| BA-05 | NFR-01 | S5 lấy dữ liệu SoC theo chu kỳ 3 phút. |
| BA-06 | NFR-02 | S5 hoàn tất quyết định Candidate trong ≤ 2,5 giây. |
| BA-07 | NFR-04 | S5 quyết định chính xác theo online, độ tươi và duplicate. |