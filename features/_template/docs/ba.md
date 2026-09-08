# FT-xxx — <Tên tính năng bằng tiếng Việt>

- **Trạng thái:** đề xuất | đã duyệt | đang làm | đã demo | tạm dừng | bị bỏ
- **Người viết / Người duyệt:** — / —
- **Ngày viết / Ngày duyệt:** YYYY-MM-DD / —
- **Bản nháp gốc:** `artifacts/ba-drafts/FT-xxx-YYYY-MM-DD.md`
- **Tiêu chí nghiệm thu:** [`qa-qc.md`](qa-qc.md)

---

## Một câu

<Tính năng này làm gì, cho ai, trong tình huống nào. Một câu. Nếu cần hai câu thì tính năng
đang bị gộp và nên tách.>

---

## Tài xế là ai trong tình huống này

Không phải chân dung nhân khẩu học. Là **trạng thái** của người ngồi sau vô-lăng lúc tính năng
kích hoạt: họ đang bận gì, tay đang làm gì, chú ý đang ở đâu, mức căng thẳng thế nào.

Một tính năng chủ động can thiệp vào sự chú ý của người đang lái. Mục này quyết định can thiệp
đó có được chào đón hay không.

---

## Kỳ vọng thoải mái nhất

Mô tả điều **tốt nhất có thể xảy ra** từ góc nhìn tài xế — không phải điều tối thiểu chấp nhận
được. Viết như một cảnh, không phải một đặc tả.

> *Ví dụ về giọng văn:* "Trời bắt đầu mưa. Chưa kịp nghĩ đến việc chỉnh gì, xe đã nói nhỏ một
> câu rằng đoạn đèo phía trước đang mưa to và gợi ý giảm tốc. Tài xế chỉ cần ừ. Không có màn
> hình nào phải bấm, không có gì phải xác nhận hai lần."

Đây là mục quan trọng nhất của tài liệu và là mục `pa-user-analysis` viết trước tiên. Nó là
thứ mà `pa-ba-conformity` đối chiếu khi hỏi *"code có đang phục vụ đúng kỳ vọng này không"*.

---

## Yêu cầu nghiệp vụ

Mỗi dòng một `BA-nn`. Viết bằng ngôn ngữ nghiệp vụ, dùng thuật ngữ trong
[`architecture/glossary.md`](../../architecture/glossary.md). **Không nêu tên file, hàm, hay
kỹ thuật triển khai** — đó là việc của plan.

| id | Yêu cầu | Vì sao tài xế cần | Ưu tiên |
|---|---|---|---|
| BA-01 | | | bắt buộc |
| BA-02 | | | bắt buộc |

Ưu tiên: `bắt buộc` (thiếu thì tính năng vô nghĩa) · `nên có` (thiếu thì tính năng vẫn dùng
được) · `nếu còn thời gian`.

---

## Khi nào tính năng phải im lặng

Ràng buộc bắt buộc điền. Một agent chủ động nói sai lúc thì tệ hơn một agent không nói gì —
với khán giả là vendor, đây là thứ đầu tiên họ nhận ra.

| id | Không được lên tiếng khi | Vì sao |
|---|---|---|
| BA-S1 | | |
| BA-S2 | | |

Các mục `BA-S*` cũng cần tiêu chí `QC-S*.m` tương ứng, y như `BA-nn`.

---

## Ngoài phạm vi

Những thứ liền kề mà tính năng này **cố ý không làm**, và vì sao. Một tính năng không có mục
này sẽ tự mọc thêm phạm vi trong lúc code.

---

## Câu hỏi còn mở

| Câu hỏi | Chặn cái gì | Ai trả lời |
|---|---|---|
| | | |

Câu hỏi ở đây phải được đóng trước khi trạng thái chuyển sang `đã duyệt`.
Câu hỏi phát sinh sau khi duyệt thì đi vào [`devlog`](../../devlog/), không sửa ngược file này.
