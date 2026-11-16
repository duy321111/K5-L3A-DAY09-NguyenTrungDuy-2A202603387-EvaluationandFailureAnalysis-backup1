# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: MEOMEO
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): `9cecb25` — code Orchestrator và benchmark; tài liệu ghi hash ở commit kế tiếp.

## 2. Mục tiêu và cách tiếp cận

Nhóm xử lý claim hoàn phí vận chuyển theo bốn kiến trúc trên cùng dữ liệu synthetic. Workflow (Nguyễn Quỳnh Trang), Single ReAct (Nguyễn Trung Duy), Orchestrator + Handoff (Vũ Đức Tâm) được đối chiếu với Swarm tham chiếu. Mỗi trial dùng SQLite mới; mọi shape dùng cùng seed, MockLLM, bảng giá và evaluator. Code tính tiền và host kiểm approval, trần theo đơn, idempotency; ticket chỉ là dữ liệu người dùng.

## 3. Giải pháp

Phần Người 3 — Vũ Đức Tâm, MSSV 2A202603522. Trạng thái kiểm tra ngày 16/11/2026:

| Shape | Luồng xử lý và ranh giới code / model |
| --- | --- |
| A — workflow (code hiện có của Người 1) | Python đọc claim qua `get_claim_view`, kiểm visibility bằng `lookup_order`, tính quote bằng `compute_compensation`, rồi gọi host khi quote > 0. MockLLM chỉ soạn câu chữ. |
| B — single (Người 2) | `decide()` lần lượt chọn `lookup_order`, `compute_compensation` trong `run_react` với trần 8 bước và `worker=True`. Mỗi vòng tính chi phí MockLLM. Code lấy quote từ tool rồi gọi host; ticket không được đưa vào observation. |
| C — orchestrator (Người 3) | Code dựng `handoff.v1` bằng `make_handoff`, giao `lookup_order`, `lookup_policy`, `compute_compensation` cho `run_readonly_investigators`. Sau khi kiểm visibility, orchestrator dùng quote có cấu trúc rồi gọi host; investigator không ghi tiền. |

Orchestrator đọc claim qua adapter, không đọc row thô. Thiếu claim trả `failed`; thiếu `order_id` trả `needs_info`; đơn không tồn tại hoặc ngoài principal trả `escalated`; quote bằng 0 trả `denied`. Quote dương luôn đi qua `durability.issue_refund`, kể cả khi approval có thể bị từ chối, để host sinh audit `policy_denied`. Host từ chối trả `denied`; xung đột số tiền khi retry trả `failed`; thành công trả `resolved`. Mọi nhánh dùng `finish()` để lấy effect và số audit thực từ ledger.

Handoff có task cố định, `facts={}`, scope `owner_order_only` và ba tool chỉ đọc. Không sao chép ticket, parent context, secret, header hay history vào gói chuyển giao. Principal truyền từ claim do adapter đọc; nội dung ticket không thể thay principal, tool hoặc số tiền. MockLLM được tính budget nhưng chỉ soạn chữ từ status và proposal do code quyết định; đầu ra model không điều khiển refund.

`proposal_amount` giữ nguyên quote đầy đủ. Ví dụ T14 có entitlement 150.000 VND và đã hoàn ship 30.000 VND: orchestrator truyền 150.000 cho host, host chỉ ghi 120.000. Không trừ trước tại shape. Khi crash, shape ghi event `crash`, flush trace rồi ném lại `InjectedCrash`; connection luôn đóng trong `finally`. Khi resume, host dùng khóa `refund:{claim_id}` và transaction ledger/audit để tránh ghi trùng.

Trace Orchestrator gồm `claim`, `handoff`, `investigator`, `quote`, `host`, `decision`; nhánh crash có thêm `crash`. Event investigator chỉ ghi visibility, lý do và số policy, không ghi payload đơn đầy đủ. Mọi nhánh return ghi trace JSON mới có `run_id` đúng contract. Không log ticket, principal, secret, header, SĐT, địa chỉ, ghi chú nội bộ, tên hàng hay câu trả lời model. Bằng chứng và giới hạn kiểm tra nằm trong [ADR](decision_adr.md#trace-và-bằng-chứng) và [báo cáo cá nhân](2A202603522_VuDucTam.md).

## 4. Kết quả

Kết quả từ `src/reports/benchmark.json` sau khi tích hợp ba shape, 14 claim × 5 seed (70 trial/shape); chi phí là VND mô phỏng:

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success | Mean / p95 steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Workflow | 1,000 | 1,000 | 1,000–1,000 | 0 | 27,86 | 3,79 / 4 |
| Single | 1,000 | 1,000 | 1,000–1,000 | 0 | 31,83 | 5,64 / 6 |
| Orchestrator | 1,000 | 1,000 | 1,000–1,000 | 0 | 47,45 | 5,36 / 6 |
| Swarm | 0,986 | 0,929 | 0,929–1,000 | 0,000816 | 49,57 | 2,80 / 3 |

Swarm sai một trial C-002 seed 55 do lấy số ngày từ ticket. `src/reports/crash.json` ghi 20/20 cho suite host + swarm; T12 trong ma trận student kiểm crash/resume từng shape. Cổng host 82 pass và ma trận student 248 pass. Quét 70 trace public mỗi shape theo parent canary và PII trong fixture: 0 file khớp. Chưa có `student_drop/` nên không báo hidden pass rate.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

Khi tích hợp, `python` ngoài venv trỏ WindowsApps và pytest trong sandbox không truy cập được thư mục tạm Windows. Nhóm dùng `src/.venv/Scripts/python.exe` và chạy test trong terminal được cấp quyền. Benchmark cũ chạy trước khi nhận Single nên Single ra 0; đã chạy lại lệnh chuẩn sau khi tích hợp, hiện 70/70 public trial.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM là bộ mô phỏng theo seed, giá là giả lập và latency `unavailable`. Bộ public 14 claim nhỏ, không đại diện cho hidden hoặc production. Quyết định có thể thay đổi nếu bộ claim mới có tác vụ cần điều tra song song hoặc nhiều trường hợp mơ hồ mà workflow không giải quyết được; phải đo lại dưới cùng điều kiện. Thí nghiệm cap 8→2 của Single trong `research_card.md` chỉ chỉ ra độ nhạy với giới hạn bước trên bộ public.

## 8. Tài liệu tham khảo

- [Đề bài, luật nghiệp vụ và contract](../../README.md)
- [Công thức metric](../../docs/metrics.md)
- [Báo cáo benchmark và crash](../../src/reports/README.md)
- [Phiếu nghiên cứu và nguồn R2](research_card.md)
