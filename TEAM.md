# Team

## Thông tin nhóm

- Tên nhóm: MEOMEO
- Lớp: L3A
- Repo nhóm: `https://github.com/vuductam20022004/K5-L3A-DAY08-MEOMEO-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/vuductam20022004/K5-L3A-DAY08-MEOMEO-FromWorkflowsToAgents ; nhánh làm việc `tam`, commit code và benchmark `9cecb25`; tích hợp vào `main` trước khi nộp.

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 |Vũ Đức Tâm|2A202603522|ductamyenphucnamdinh@gmail.com|https://github.com/vuductam20022004 | Trưởng nhóm: Orchestrator + Handoff và hoàn thành báo cáo|
|   2 |Nguyễn Quỳnh Trang|2A202603477|nguyenquynhtrang7092005@gmail.com|https://github.com/NguyenTrang005|Xây dựng bản workflow và tổng hợp kết quả của team|
|   3 |Nguyễn Trung Duy | 2A202603387 | duy321111@gmail.com | https://github.com/duy321111 | Single Agent (ReAct)|
Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Quỳnh Trang — 2A202603477 | Workflow + tích hợp | `c24ed30` | `src/tests/test_workflow_ticket_boundary.py` |
| Nguyễn Trung Duy — 2A202603387 | Single Agent (ReAct); kiểm approval, crash, trace; thí nghiệm CP5 | `1d8278d` | `src/tests/test_single_agent.py`: `test_single_step_cap_never_writes`, `test_single_resume_has_one_effect`, `test_single_invalid_approval_is_audited`, `test_single_trace_excludes_private_fields` (12 trường hợp tổng cộng trong file) |
| Vũ Đức Tâm — 2A202603522 | Orchestrator + Handoff; benchmark, ADR và báo cáo nhóm | `9cecb25` | `src/tests/test_orchestrator_safety.py` (14 trường hợp) |

## Cá nhân — Nguyễn Trung Duy (2A202603387)

Báo cáo riêng: [2A202603387_NguyenTrungDuy.md](report/team/2A202603387_NguyenTrungDuy.md).

### Phần việc phụ trách

- CP1: chuẩn bị môi trường Python, đọc `business_rules.md`, `contracts.md` và `swarm_reference.py`.
- CP2: triển khai shape Single Agent, hàm `decide()` và vòng ReAct tối đa 8 bước.
- CP3: truyền `crash_at` đến host, không bắt `InjectedCrash`; kiểm tra chạy lại sau crash.
- CP4: kiểm approval, ticket injection, secret/PII leak và kết quả trên ma trận public của single.
- CP5: điền research card, chạy thí nghiệm giới hạn bước và viết báo cáo cá nhân.

### Đóng góp cụ thể

- Triển khai `src/lab8/shapes/single.py`: agent chỉ chọn tool đọc qua `worker=True`; số tiền lấy từ kết quả `compute_compensation`. Code truyền quote đầy đủ vào `durability.issue_refund` để host kiểm approval, trần theo đơn và idempotency.
- Dùng MockLLM để ghi nhận usage mô phỏng, không gọi model thật. Trace ghi luồng xử lý và kết quả, không ghi ticket, parent secret, header hoặc PII.
- Thêm `src/tests/test_single_agent.py` với 12 trường hợp: step cap, injection, claim không tồn tại, ba điểm crash, bốn dạng approval sai, approval thấp hơn quote và kiểm dữ liệu riêng tư trong trace/kết quả/stdout.
- Tạo `src/experiments/single_cap2.py` để so sánh cap 8 và cap 2, cập nhật [research card](report/team/research_card.md). Đây là thí nghiệm phục vụ CP5.
- Bổ sung topic bonus B7 riêng: `src/bonus/grader_audit.py`, `src/tests/test_bonus_grader_audit.py` và [bonus_report.md](report/team/bonus_report.md). Kiểm toán ba grader bằng quan hệ metamorphic, phát hiện sai lệch chi phí, mẫu số lỗi hạ tầng và pass^5 khi nhân đôi trial. Phần bonus mới chưa commit.

### Bằng chứng

- Commit triển khai và test: `1d8278d` (`single agent`).
- Ma trận public riêng single đã chạy đạt 62 test; bộ host cùng 12 test bổ sung tại thời điểm kiểm tra đạt 66 test.
- [single_ablation.json](src/reports/single_ablation.json): 14 claim × 5 seed, single cap 8 đạt 70/70 trial; biến thể cap 2 đạt 10/70. Chi phí mô phỏng/success lần lượt 31,83 và 213,41 VND.
- Test crash kiểm ba điểm `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`; resume giữ một refund và một audit committed. Chưa có kết quả hidden.

## Cá nhân — Vũ Đức Tâm (2A202603522)

Báo cáo riêng: [2A202603522_VuDucTam.md](report/team/2A202603522_VuDucTam.md).

### Phần việc phụ trách

- Người 3: xây dựng shape Orchestrator và handoff theo allowlist; kiểm trace, approval, crash và retry.
- Tích hợp kết quả CP5: chạy lại benchmark bốn shape, crash suite, điền quyết định kiến trúc và mục giải pháp/kết quả trong báo cáo nhóm.

### Đóng góp cụ thể

- Triển khai `src/lab8/shapes/orchestrator.py`: investigator chỉ dùng tool đọc; quote lấy từ dữ liệu có cấu trúc; host kiểm approval, trần hoàn tiền và ghi ledger. Trace không chứa ticket, secret, header hoặc PII.
- Thêm `src/tests/test_orchestrator_safety.py` với 14 trường hợp về handoff, quyền truy cập đơn hàng, approval sai, ba điểm crash, top-up và retry xung đột.
- Ghi phần Orchestrator trong [báo cáo nhóm](report/team/group_report.md) và phần trace trong [ADR](report/team/decision_adr.md); cập nhật benchmark/crash report bằng lệnh chuẩn sau khi tích hợp ba shape.

### Bằng chứng

- Cổng host: 82 test pass; ma trận student: 248 test pass, gồm 62 test Orchestrator. Test riêng Orchestrator: 14 trường hợp pass.
- [benchmark.json](src/reports/benchmark.json): Orchestrator 70/70 trial public trên 14 claim × 5 seed; [crash.json](src/reports/crash.json): suite chuẩn host + swarm đạt 20/20. Crash riêng Orchestrator được kiểm bằng T12 và test mới.
- `python -m lab8.check_submission`: 0 FAIL khi chạy sau tích hợp. Commit code và benchmark `9cecb25`; chưa có kết quả hidden.
