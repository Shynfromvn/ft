# `features/` — mỗi tính năng là một thư mục

File này là bản định hướng nhanh: vòng đời, Definition of Done, câu hỏi hay gặp. Hợp đồng đầy đủ
và có thẩm quyền — chín khối của `FEATURE_SPEC`, bảy bất biến kèm gate, luật hai trục về
`references/` — nằm ở
[`docs/architecture/feature-contract.md`](../docs/architecture/feature-contract.md). Hai file phải
nói cùng một thứ; nếu chúng lệch, file kia đúng.

**Đây là lý do repo tồn tại.** `core`, `database`, `server` là hạ tầng mà bất kỳ dự án FastAPI nào
cũng có. Seam mới là thứ làm cho chi phí thêm tính năng thứ mười bằng chi phí thêm tính năng thứ
hai, và làm cho việc bỏ một tính năng không để lại vết.

---

## Vòng đời sáu bước

```bash
# 1. brief — dựng bốn thứ cùng lúc để chúng không lệch ngay từ đầu
make feature-new ID=FT-008 SLUG=power-consumption-optimization
```

| # | Bước | Làm gì | Ai chạy |
|---|---|---|---|
| 1 | **brief** | `feature.yaml` — `schemaVersion: 2`, `enabled: false` | `make feature-new` |
| 2 | **validate** | Brief parse sạch, ràng buộc ngữ nghĩa qua hết | `make feature-check` |
| 3 | **generate** | `spec.py` + `backend/` + `frontend/` + `tests/`, copy từ `_template/` | `make feature-new` |
| 4 | **implement** | Business rules, UI, test — **chỉ trong thư mục tính năng** | người |
| 5 | **gate** | contract checker · unit · scenario · lint · typecheck · build | `make check` |
| 6 | **enable** | `identity.enabled: true`, cập nhật test "still disabled", mở PR | **bằng tay** |

Bước 6 làm bằng tay là một ràng buộc, không phải một bước thủ tục: **không tính năng nào đi thẳng
từ scaffold vào runtime discovery.** Một scaffold chưa ai điền mà chạy được sẽ đọc `TODO` lên trước
mặt vendor.

Sau bước 1, **không viết code ngay.** Đi theo vòng đời chín bước của repo: `pa-user-analysis` điền
`ba.md` và xin duyệt trước.

---

## Definition of Done — mười mục

Một tính năng chỉ được merge khi cả mười mục dưới đây đúng.

- [ ] `feature.yaml` validate sạch; `spec.py` được contract checker chấp nhận
- [ ] `manifest.generated.json` sinh lại khớp **byte-for-byte**
- [ ] `git grep "FT-NNN" -- ':!features/ftNNN_*' ':!docs' ':!tests'` trả rỗng
- [ ] `import-linter` và ESLint boundary rule xanh
- [ ] Unit test business rules phủ ngưỡng, luật im lặng, và đường fallback
- [ ] Ít nhất một kịch bản chạy end-to-end
- [ ] **Tắt được:** `enabled: false` → toàn bộ gate vẫn xanh
- [ ] **Xoá được:** `rm -rf` thư mục tính năng → repo vẫn build và test xanh
- [ ] `README.md` của tính năng ghi lại **con số** ngưỡng và các quyết định thiết kế
- [ ] Không `os.environ`, không `print`, không `dict[str, Any]` xuyên biên, không lời gọi ngoài
      thiếu timeout

Hai mục **tắt được** và **xoá được** là bài kiểm tra thật của kiến trúc này. Một trong hai trượt
nghĩa là tính năng đã rò ra ngoài thư mục của nó. Cả hai có test tự động trong
`backend/tests/features_platform/test_platform.py`.

---

## Codegen có đúng MỘT chủ sở hữu

```bash
make feature-manifest   # SINH RA manifest + frontend registry
make feature-check      # chỉ KIỂM: parity + cô lập tính năng
```

`make feature-manifest` là nơi duy nhất sinh file. Pre-commit và CI chỉ *kiểm*.

Sinh ở hai nơi nghĩa là hai nơi có thể cho ra byte hơi khác nhau — một dấu xuống dòng thừa, một
thứ tự dict khác — và parity gate sẽ đỏ trên máy người khác vì lý do không ai dựng lại được. **Một
gate đỏ ngẫu nhiên là một gate người ta học cách chạy lại cho tới khi nó xanh.**

`manifest.generated.json` và `frontend/src/generated/feature-registry.ts` đều **được commit** (để
frontend build không phụ thuộc runtime Python) và đều **không sửa tay**.

---

## Ba câu hỏi hay gặp

**"Tôi cần một thứ nền tảng chưa có."** Mở rộng seam một cách tổng quát, đừng chọc một lỗ riêng.
PR chạm cả `features/` lẫn `backend/src/` phải giải thích trong mô tả PR **vì sao seam không đủ** —
đó là tín hiệu cần mở rộng nền tảng, và nó nên hiếm.

**"Tính năng của tôi cần dữ liệu của tính năng khác."** Không import chéo (bất biến I4). Cần dùng
chung thì đẩy lên nền tảng. Phân phối là routing trigger khai báo trong `spec.py` cộng outbox —
không có `event_bus`.

**"Vì sao app không lên?"** Contract checker fail-closed (bất biến I5): spec sai, symbol không
resolve, hay component key không tồn tại đều làm app **không khởi động**. Thông báo lỗi nêu đích
danh tính năng, khối spec và trường. Đó là hành vi đúng — một tính năng hỏng phải nhìn thấy được,
không được degrade thành "hôm nay nó im".

---

## Ranh giới sở hữu

| Platform sở hữu (đừng viết lại trong tính năng) | Tính năng sở hữu |
|---|---|
| Turn lifecycle, durable commit, retry, outbox | Business rules, thresholds, suppression |
| Auth, authorization, profile/vehicle/trip scoping | Evaluate/respond handler + schema |
| HMAC subject, privacy sanitization, deletion safety | Agent adapter (event + snapshot → request) |
| Canonical state domains & event vocabulary | Runtime projection hook |
| Memory transport, idempotency, writer plumbing | Memory category, evidence, transition, public projection hook |
| Routing engine, planner, allow-list | Trigger rules khai báo trong `spec.py` |
| Response window, field allow-listing | Danh sách trường public đề xuất (được review) |
| Catalog, component resolver, generic shell | Detail screen + frontend projection |

Nếu tính năng của bạn cần một thứ ở cột trái, **đừng tự làm** — mở rộng seam của nền tảng.

---

## `_template/` không phải một tính năng

Discovery chỉ quét `ft*`, nên `_template` không bao giờ vào registry. Nó cố ý dùng package giả
`ft000_example` để mọi đường dẫn symbol trong đó đọc được như thật; `scripts/feature-new.sh` đổi
sang package thật lúc copy.

`FT-000` là **ID sentinel** — vĩnh viễn không thuộc tính năng nào, và là ID duy nhất được phép xuất
hiện trong `backend/src/` và `frontend/src/` (fixture của test nền tảng cần một ID hợp lệ về hình
thức). `scripts/feature-new.sh` từ chối nó.
