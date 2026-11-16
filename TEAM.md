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
| Nguyễn Trung Duy — 2A202603387 | Single Agent (ReAct) | `1d8278d` | `src/tests/test_single_agent.py` |
| Vũ Đức Tâm — 2A202603522 | Orchestrator + Handoff; benchmark, ADR và báo cáo nhóm | `9cecb25` | `src/tests/test_orchestrator_safety.py` (14 trường hợp) |

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

## Cá nhân — Nguyễn Quỳnh Trang (2A202603477)

Báo cáo riêng: [2A202603477_NguyenQuynhTrang.md](report/team/2A202603477_NguyenQuynhTrang.md).

### Phần việc phụ trách

- xây dựng shape Workflow theo các bước Python cố định; kiểm tra nghiệp vụ, approval qua host, trace và crash/resume.
- Phối hợp tích hợp, kiểm tra bản tích hợp và đối chiếu các checkpoint của nhóm.

### Đóng góp cụ thể

- Triển khai `src/lab8/shapes/workflow.py`: đọc claim qua `get_claim_view`, tra đơn theo principal, tính quote bằng `compute_compensation` và gửi quote đầy đủ cho host kiểm approval, trần hoàn tiền và idempotency. Workflow không gọi MockLLM và không dùng chỉ dẫn trong ticket để quyết định số tiền.
- Dùng `finish()` để trả kết quả khớp ledger và ghi trace ở mọi nhánh return. Truyền `crash_at` vào host; khi crash, flush trace rồi phát sinh lại `InjectedCrash`, luôn đóng kết nối trong `finally`.
- Thêm `src/tests/test_workflow_ticket_boundary.py`: kiểm tra ticket yêu cầu bỏ qua policy và khai trễ 99 ngày không thay đổi quyết định dựa trên order; dấu nhận diện trong ticket không xuất hiện trong trace. Test chạy ở seed 11 và 55.
- Hoàn thiện báo cáo cá nhân, khai báo sử dụng AI và ghi bằng chứng commit/test; phối hợp chạy smoke, test host, ma trận student và kiểm tra định dạng bài nộp sau khi tích hợp đủ ba shape.

### Bằng chứng

- Commit code và test: [`c24ed30`](https://github.com/vuductam20022004/K5-L3A-DAY08-MEOMEO-FromWorkflowsToAgents/commit/c24ed30ebe6f6095972c2e52f70fe1e922f69d92).
- Workflow đạt 62/62 test student, gồm retry T11 và crash/resume T12. Test riêng `test_ticket_cannot_override_order_or_leak_into_trace` đạt cả hai seed 11 và 55.
