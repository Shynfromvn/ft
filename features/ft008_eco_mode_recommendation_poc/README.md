# FT-007 — Khuyến nghị chế độ vận hành theo trạng thái pin

- Yêu cầu: [`docs/ba.md`](docs/ba.md) — UC-01, 34 `BA-nn`
- Tiêu chí: [`docs/qa-qc.md`](docs/qa-qc.md)
- Ngưỡng bằng code: [`backend/rules.py`](backend/rules.py)
- Câu nói: [`backend/copy.py`](backend/copy.py)

Khi mức pin **đi qua** ngưỡng 20% trong lúc xe đang Parked hoặc Driving, trợ lý nói đúng một câu
cho tài xế biết mức pin và đề nghị chuyển sang Eco Mode. Không có luồng khẩn cấp, không tự động
chuyển chế độ — mọi thay đổi chờ tài xế xác nhận tường minh (`BR-07`).

**`DEBT-020` (plan P25, 2026-08-28):** bản trước của package này chạy trên một `ba.md` rộng hơn,
có luồng khẩn cấp 5%/Turtle Mode, một khoảng nghỉ (cooldown) sau khi từ chối, và một cổng chỉ nói
khi đang Driving. Không cái nào có trong `ba.md` hiện hành — `BR-10` còn cấm thẳng cơ chế cooldown
— nên tất cả đã bị gỡ, không giữ lại dưới dạng code chết. Nếu bạn thấy một khái niệm trong tài
liệu cũ (Turtle, khoảng nghỉ, "not driving") xuất hiện lại, đó là một hồi quy.

---

## Ngưỡng — con số, không phải mô tả

| Ngưỡng | Giá trị | Nguồn |
|---|---|---|
| Ngưỡng thấp (nhắc mềm) | **20%** | `BR-01`, inclusive (`soc_pct > 20` mới im lặng) |
| Bán kính im lặng quanh Nhà/trạm sạc | **5 km** | `BR-09`, strict `<` |
| Độ tươi tối đa — dữ liệu pin | **10 giây** | `NFR-01` |
| Độ tươi tối đa — bối cảnh Navigation | **120 giây** | `NFR-01` |
| Cửa sổ trả lời bằng giọng nói | **6 giây** | Bước 9 |
| Trần chờ xác nhận chuyển Eco | **3 giây** | Nội bộ, chưa có số trong `ba.md` |
| Sàn độ tin cậy nhận diện — để được nói | **0,90** | `DEBT-012`, chưa có nguồn thật |
| Tốc độ đọc dùng để suy thời lượng | **16 ký tự/giây** | Đo cho tiếng Việt |

`BR-09` chỉ suppress khi đồng thời **destination_type ∈ {Home, ChargingStation}** *và* khoảng
cách < 5km (plan P25 T14/T15, đã đóng `DEBT-063`) — một `OTHER` gần vẫn phải nói (`AC-04`).

---

## Các cổng — đúng thứ tự `_evaluate_soft` chạy

1. `above_threshold` — SoC > 20%.
2. `already_in_eco_mode` — xe đã ở Eco.
3. `assistant_mode_not_allowed` — Assistant Mode khác Balanced/Proactive (`E04`).
4. `offline` — xe không kết nối cloud (`Preconditions §2`).
5. `system_state_not_normal` — System State khác Normal (plan P25 T13).
6. `assistant_unavailable` — ViTa không Available.
7. `call_active` — đang trong cuộc gọi (`E06`/`BR-06`).
8. `safety_preempted` — Safety/System Alert hoặc ADAS đang Warning/Intervention (`E05`/`BR-05`,
   [ADR-0029](../../docs/adr/0029-canh-bao-an-toan-la-trang-thai-xe-khong-phai-guardrail.md), plan
   P27). `UNKNOWN` không tự chặn — chỉ giá trị tường minh mới chặn.
9. `data_missing`/`data_stale` — dữ liệu pin thiếu hoặc quá 10 giây, hoặc độ tin cậy dưới sàn (`E01`).
10. `navigation_unavailable`/`navigation_stale`/`destination_type_unknown` — bối cảnh Navigation
    thiếu, quá 120 giây, hoặc active mà không phân loại được, **fail-closed** (không tạo Candidate) —
    khác với logic cũ từng coi "không biết" là tín hiệu để nói (`DEBT-020`).
11. `proximity_suppressed` — gần điểm đến trong bán kính 5km (xem ghi chú `destinationType` ở trên).
12. `memory_timeout`/`memory_unavailable`/`memory_inconsistent` — S7 Shared Memory không trả lời
    hợp lệ trong 300 ms (`E02`/`BR-11`, [ADR-0030](../../docs/adr/0030-s7-shared-memory-mo-rong-tu-versioned-snapshot.md),
    plan P28). `memory_expired` khai cho đủ từ vựng `ba.md` nhưng chưa có kịch bản kích hoạt riêng
    trong lát cắt hẹp này (xem plan P28's "Not in scope").
13. `duplicate_candidate` — một Candidate Eco cho tài xế này đang chờ trả lời, còn trong 90 giây
    (plan P28).
14. Không cổng nào chặn → `SUGGEST_ECO`.

## `/evaluate` trả về một `Candidate` thật, và lưu lại (plan P26 + P28)

`POST /api/v1/features/FT-007/evaluate` không còn chỉ trả `resolvedPlan` mờ và một chuỗi id trần.
Trường `candidate` (kiểu `pa.kernel.candidates.Candidate`) mang `expiresAt` (90 giây,
`DEFAULT_LIFETIME` — FT-007 cố tình không tự khai `candidateLifetimeSeconds`, xem `feature.yaml`),
`confirmation` (đúng `BR-07`/`BR-04`/Bước 9: bắt buộc, cho phép voice, cho phép touch khi Parked,
cửa sổ 6 giây — do chính `service.public_result()` khai, platform chỉ đọc lại), và
`classification`/`responseType`. `candidateId` trần vẫn còn (tương thích ngược), giờ khớp
`candidate.candidateId`.

`turn_id` luôn `None` trên đường này — route REST không mở một turn bền vững nào, khác đường
bus/`ProactiveEngine`. Thay vào đó (plan P28), route tự `remember` Candidate vừa phát ra vào S7
Shared Memory với `dedup_key=candidate.candidateId`. `/respond` tra lại bằng đúng khoá đó
(`find_by_dedup_key`) trước khi gọi `handlers.respond` — không thấy hoặc đã hết hạn thì trả thẳng
`candidate_expired`/`E09`, không chạm tới `service.respond()`. Sau khi tính năng đã trả lời,
`/respond` gọi `memory.transitions()` (hook khai trong `feature.yaml`) rồi ghi kết quả **vào cùng
dòng** đó (upsert theo `dedup_key`, không phải một dòng mới) — dòng thôi đọc như "còn đang chờ" kể
từ đó, đúng điều `versioned_snapshot`'s `duplicateCandidate` cần để không chặn Candidate kế tiếp.

**S7 Shared Memory là một cổng chung, feature-agnostic** — route `/evaluate` chỉ chuyển tiếp một
`Mapping` do `ContextAggregator.assemble()` soạn, không tự biết vocabulary của tính năng nào;
`handlers.evaluate()` (`_facts_from`) là nơi duy nhất dịch nó sang `MemoryFacts` của riêng FT-007.

---

## Vì sao chia file như vậy

| File | Giữ gì | Vì sao tách |
|---|---|---|
| `rules.py` | Ngưỡng và các mã lý do im lặng | Ngưỡng là hằng số Python **có type và có test**, không phải YAML |
| `copy.py` | Mọi câu tài xế nghe hoặc đọc | `QC-06.2` kiểm **nội dung** câu nói; gom một chỗ thì đo được |
| `service.py` | Quyết định — **thuần** | Không DB, không đồng hồ ⇒ test đơn vị không cần Postgres |
| `agent.py` | Dựng `EvaluateRequest` từ snapshot | `feature.yaml`'s `agent.adapter` cần một symbol tồn tại; đọc trí nhớ chuyển sang `handlers.py` từ plan P28, nơi snapshot của S7 thật sự tới |
| `runtime.py` | Projection trạng thái | Thuần, fail-closed: thiếu domain thì gắn cờ, không đoán |
| `memory.py` | Hook trí nhớ | Nền tảng sở hữu lưu trữ và phạm vi; đây chỉ nói *cái gì* xảy ra |

Có một test khẳng định `service.py` không import `sqlalchemy`, `AsyncSession` hay `httpx` — nếu
nó import, cách chia này đã thôi trả công cho chính nó.

---

## Hai kênh nói, viết riêng

`voiceLine` (đọc lên) và `message` (thẻ liếc mắt) **không dẫn xuất từ nhau**. Cắt câu nói thành thẻ
cho ra một thẻ đọc như câu bị cụt, và phá âm thầm ngay khi một trong hai ràng buộc đổi. Nội dung
ba câu chính (`eco_suggestion`, `eco_confirmed`, `eco_mode_change_failed`) khớp nguyên văn
`UI/UX 9.1` của `ba.md`.

---

## Nợ liên quan

| Dòng | Ảnh hưởng gì tới tính năng này |
|---|---|
| [`DEBT-008`](../../docs/devlog/debts-ledger.md) | Mọi ngưỡng và câu chữ kế thừa từ một bản chưa qua review; một lần review của bên cấp tài liệu có thể đổi chúng |
| `DEBT-012` | Sàn độ tin cậy nhận diện chưa có nguồn thật; mặc định **0** là fail-closed |
| `DEBT-025` | Chưa có tập câu thoại tiếng Việt đã duyệt — `QC-27.1` chưa chạy được |
| `DEBT-064` | Độ chính xác định tuyến Candidate S7→S6 (`NFR-09`/`QC-25.1`/`QC-25.2`) — đường bus/edge thật, ngoài phạm vi REST mà QC test |
| `DEBT-065` | `duplicateCandidate` trong `versioned_snapshot` quét toàn bộ hồ sơ, không lọc theo tính năng — đúng khi chỉ FT-007 ghi Shared Memory |

**Đã trả, không còn ảnh hưởng:** `DEBT-021` (`systemState`, plan P25 T13/T16), `DEBT-022` (Audio/Call
plan P25 T8, Safety/System Alert plan P27), `DEBT-050` (hai bảng `ft007_*` bị xoá ở
[P34](../../docs/plans/done/2026-09-01-p34-db-xoay-truc-ve-demo-platform.md) T11 —
[ADR-0038](../../docs/adr/0038-nen-tang-demo-luu-gi-o-dau.md) cho mọi tính năng ghi vào
`runs.trace` thay vì mỗi tính năng một bảng), `DEBT-063` (`destinationType`, plan P25 T14/T15).
