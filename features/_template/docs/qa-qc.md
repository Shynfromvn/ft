# FT-xxx — Tiêu chí nghiệm thu

- **Yêu cầu nguồn:** [`ba.md`](ba.md)
- **Người viết / Người duyệt:** — / —
- **Ngày viết / Ngày duyệt:** YYYY-MM-DD / —
- **Test script:** `tests/FT-xxx-<slug>/`
- **Báo cáo lần chạy:** `artifacts/reports/qc-runs/FT-xxx/`

Tài liệu này ra đời **từ `ba.md` đã duyệt và trước khi có code**. Nếu nó được viết sau khi code
chạy, nó sẽ mô tả code thay vì kiểm thử code, và mọi lần đối chiếu sau đó đều báo "khớp".

---

## Bảng phủ

Mỗi `BA-nn` trong `ba.md` phải xuất hiện đúng một lần ở cột đầu. Một dòng trống ở cột thứ hai
là một yêu cầu không kiểm chứng được.

| Yêu cầu | Được phủ bởi |
|---|---|
| BA-01 | QC-01.1, QC-01.2 |
| BA-02 | QC-02.1 |
| BA-S1 | QC-S1.1 |
| BA-S2 | QC-S2.1 |

---

## Tiêu chí

Mỗi tiêu chí phải **đo được**. Kiểm thử tốt: `"trong vòng 30 giây"`, `"đúng một lần"`,
`"không quá 2 lần trong 10 phút"`. Kiểm thử vô nghĩa: `"phản hồi hợp lý"`, `"trải nghiệm mượt"`.

Cột **Chặng** dùng thuật ngữ trong
[`architecture/event-lifecycle.md`](../../architecture/event-lifecycle.md) — khi tiêu chí trượt,
nó cho biết trượt ở chặng nào, vì năm chặng có năm cách sửa khác nhau.

| id | Điều kiện ban đầu | Việc xảy ra | Kết quả phải thấy | Chặng | Cách đo |
|---|---|---|---|---|---|
| QC-01.1 | | | | sự kiện | tự động |
| QC-01.2 | | | | hành động | tự động |
| QC-02.1 | | | | phán đoán | thủ công |
| QC-S1.1 | | | *không có hành động nào phát ra* | phán đoán | tự động |
| QC-S2.1 | | | *không lặp lại hành động đã phát* | phán đoán | tự động |

Cách đo: `tự động` (có script trong `tests/`) · `thủ công` (người kiểm, ghi lại trong report) ·
`quan sát` (đánh giá chất lượng diễn đạt, cần người đọc).

---

## Kịch bản dùng để kiểm thử

Trỏ tới file trong [`docs/demo/scenarios/`](../../demo/scenarios/). Cùng file mà demo dùng —
không viết một bộ dữ liệu riêng cho QA, vì hai bộ sẽ trôi khỏi nhau
([ADR-0002](../../adr/0002-simulator-la-first-class.md)).

| Kịch bản | Phủ tiêu chí | Mô tả tình huống |
|---|---|---|
| `ft-xxx-<slug>.yaml` | QC-01.1, QC-01.2 | |
| `ft-xxx-<biên>.yaml` | QC-S1.1, QC-S2.1 | tình huống biên, kiểm tra im lặng |

---

## Điều kiện đạt

Tính năng được coi là qua nghiệm thu khi:

- [ ] Mọi tiêu chí `bắt buộc` (phủ các `BA-nn` bắt buộc) đều đạt
- [ ] Mọi tiêu chí `QC-S*` về im lặng đều đạt — **không có ngoại lệ**, kể cả khi tính năng chính chạy tốt
- [ ] Không có tiêu chí nào ở trạng thái "chưa chạy được"
- [ ] Báo cáo lần chạy đã nằm trong `artifacts/reports/qc-runs/FT-xxx/`

Tiêu chí trượt mà được chấp nhận có điều kiện thì phải mở một dòng `DEBT-nnn` trong
[ledger](../../devlog/debts-ledger.md) và ghi số hiệu đó vào báo cáo. Không có "tạm bỏ qua" không dấu vết.
