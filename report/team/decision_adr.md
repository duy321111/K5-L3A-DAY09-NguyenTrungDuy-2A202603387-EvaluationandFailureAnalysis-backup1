# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 9cecb25 (commit chứa code Orchestrator và `src/reports/benchmark.json`)
- Run id dẫn chứng: R-workflow-C-014-s11 (`src/reports/benchmark.json`; quote 150.000 VND, effect 120.000 VND)
- Pass rate / pass^5 / seed min-max / variance: 1,000 / 1,000 / 1,000–1,000 / 0,000000 (70 trial public, 14 claim × 5 seed)
- Cost per success (mô phỏng, VND): 27,857142857 (từ `src/reports/benchmark.json`)
- Crash safety: 20/20 (`src/reports/crash.json`, suite host + swarm; crash của shape kiểm thêm bằng T12)
- Secret leak / approval bypass: 0 trace public Workflow chứa canary/PII fixture qua quét 70 trace; 0 approval bypass trong các test public/host đã chạy. Số hidden chưa có.

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Trên 14 claim public × 5 seed, workflow, single và orchestrator đều pass 70/70, pass^5 1, variance 0. Workflow có chi phí mô phỏng thấp nhất (27,86 VND/success so với 31,83 và 47,45), không cần model call để quyết định, và giữ đúng ranh giới host về approval, trần tiền và idempotency. Swarm pass 69/70 vì ở C-002 seed 55 tin số ngày trong ticket. Theo nguyên tắc chọn mức tự chủ thấp nhất đủ làm việc, nhóm chọn workflow trên bộ public. Đây là giả thuyết cho hidden, chưa phải kết quả hidden.

## Có đáng đổi lấy multi-agent không

Trên dữ liệu hiện có, multi-agent không tăng pass rate so với workflow nhưng orchestrator tốn thêm 19,59 VND/success và swarm có một trial sai. Nhóm sẽ đổi quyết định nếu bộ claim mới chứng minh workflow không xử lý đủ các trường hợp mơ hồ hoặc cần phân công đọc độc lập, trong khi shape nhiều agent tăng tỷ lệ đúng một cách ổn định và lợi ích vượt chi phí. Cần đo lại trên cùng claim, seed, giá và evaluator; MockLLM không chứng minh được điều đó cho môi trường sản xuất.

## Trace và bằng chứng

Phần Người 3 — Vũ Đức Tâm (2A202603522), áp dụng cho shape `orchestrator`:

| Event | Dữ liệu được ghi |
| --- | --- |
| `claim` | `claim_id`, `found` |
| `handoff` | Gói do `make_handoff` tạo: `handoff.v1`, mã request/claim, scope, task cố định, facts rỗng, ba tool chỉ đọc, giới hạn output |
| `investigator` | `visible`, `reason`, `policy_count` |
| `quote` | Số tiền, reason, clause IDs và các phần tính từ code |
| `host` | `ok`, `reason`, `conflict` của cổng host |
| `decision` | Status, quote đầy đủ, lý do kết thúc |
| `crash` | Tên điểm crash; trace được flush trước khi ném lại lỗi |

Không ghi claim/order row thô, ticket, principal, `parent_secret`, header, history, SĐT, địa chỉ, internal note, item name hoặc đầu ra MockLLM. Handoff dùng allowlist trong code; không dùng tóm tắt bằng LLM để redact. Investigator nhận `lookup_order`, `lookup_policy`, `compute_compensation`, không nhận tool ghi. Chỉ orchestrator gọi host; host quyết approval, trần tiền và idempotency.

Trace nằm ở `src/traces/<run_id>.json`, là vị trí scanner đọc được qua `RunResult.trace_path`. Shape không tạo side log hoặc in dữ liệu runtime ra stdout. `finish()` ghi trace ở mọi nhánh return; nhánh crash ghi trước khi propagate. Trace và SQLite không commit theo `.gitignore`.

Bằng chứng chạy ngày 16/11/2026:

- `src/tests/test_orchestrator_safety.py`: 14 trường hợp, gồm handoff/PII/injection, các nhánh return sớm, approval thiếu/hết hạn/thu hồi/mượn/0 VND, ba điểm crash trên T14, retry bị conflict.
- Ma trận student của Orchestrator: 62/62 pass. Test mới cùng ma trận: 76/76 pass; sau khi tích hợp cả nhóm, cổng host toàn repo 82 pass và toàn bộ ma trận student 248 pass.
- `src/reports/benchmark.json`, mục `by_shape.orchestrator`: 70/70 trial, pass rate = 1, pass^5 = 1, seed min–max = 1–1, variance = 0, cost/success = 47,447142857 VND mô phỏng, mean/p95 steps = 5,357142857/6. Đây là kết quả public, chưa phải hidden.
- Run id tham chiếu: `R-orchestrator-C-010-s55` (handoff/trace), `R-orchestrator-C-007-s11` (approval hết hạn), `R-orchestrator-C-014-s11` (quote 150.000, effect 120.000). Có thể tái tạo bằng `lab8.run` trên DB mới.
- Quét 70 trace public của Orchestrator với toàn bộ parent canary và các giá trị phone/address/internal_note/item_name từ fixture: 0 file khớp dữ liệu cấm. Test injection còn kiểm cả kết quả, handoff, stdout và stderr.
- `src/reports/crash.json`: 20/20 của suite chuẩn **host + swarm**. Bằng chứng crash riêng Orchestrator là T12 và ba trường hợp trong test mới; không coi suite chuẩn là 20 điểm crash riêng của Orchestrator.

Quyết định phía trên dùng benchmark chạy lại sau khi tích hợp code Workflow và Single. Hướng dẫn tái lập: [bàn giao Người 3](../../docs/person3_handoff.md). Chưa có `student_drop/`, chưa đưa ra số liệu hoặc kết luận về hidden. Commit `9cecb25` chứa code Orchestrator cùng report benchmark được dẫn chứng.

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.
