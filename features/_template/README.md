# `_template/` — scaffold nguồn, không phải một tính năng

`scripts/feature-new.sh` copy thư mục này. Nó **không bao giờ** vào registry: discovery chỉ quét
`ft*`, và `_template` không khớp — nên một scaffold chưa ai điền không thể vô tình chạy.

Mỗi file ở đây có một dòng `TODO` ở chỗ phải điền. Nếu một `TODO` còn nguyên khi bật tính năng,
contract checker sẽ chặn ở startup chứ không để nó chạy với giá trị mẫu.

## Vòng đời sáu bước

```
1. brief       feature.yaml  (schemaVersion: 2, enabled: false)
2. validate    python scripts/generate_manifest.py --check
3. generate    spec.py + backend/ + frontend/ + tests/ từ brief
4. implement   CHỈ trong thư mục tính năng
5. gate        contract checker · unit · scenario · lint · typecheck · build
6. enable      identity.enabled: true, cập nhật test "still disabled", mở PR
```

Bước 6 làm **bằng tay**. Không tính năng nào đi thẳng từ scaffold vào runtime discovery
(`features/README.md`).
