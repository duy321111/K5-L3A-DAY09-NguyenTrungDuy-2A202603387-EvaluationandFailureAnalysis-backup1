# Báo cáo cá nhân — Nguyễn Quỳnh Trang

## 1. Thông tin thành viên

- Họ tên: Nguyễn Quỳnh Trang
- MSSV: 2A202603477
- Email: nguyenquynhtrang7092005@gmail.com
- GitHub: [NguyenTrang005](https://github.com/NguyenTrang005)
- Nhóm: MEOMEO — Lớp L3A
- Nhánh làm việc: `trang`

## 2. Phần việc phụ trách

Phụ trách Shape A — workflow và phối hợp tổng hợp kết quả của nhóm. Phần đã hoàn thành gồm triển khai `src/lab8/shapes/workflow.py`, bổ sung test bảo vệ ranh giới giữa ticket và dữ liệu đơn hàng, kiểm tra workflow và bộ test host.

Chạy benchmark bốn shape sau khi tích hợp code của các thành viên, tổng hợp số liệu. Viết file `TEAM.md`

## 3. Đóng góp cụ thể

- Commit kỹ thuật: c24ed30 (HEAD -> trang, origin/trang) Implement workflow and ticket injection tests.
- Hoàn thiện workflow theo các bước cố định: đọc claim bằng `get_claim_view`, kiểm tra mã đơn, tra đơn theo principal, tính quote bằng `compute_compensation`, gọi host ghi refund và trả kết quả bằng `finish()`.
- Xử lý claim không tồn tại bằng `failed`; thiếu mã đơn bằng `needs_info`; đơn không hiển thị bằng `escalated`; quote bằng 0 bằng `denied`. Với quote dương, kết quả phụ thuộc kiểm duyệt của host.
- Giữ việc tính tiền trong code. Workflow không gọi model, không dùng số ngày hoặc chỉ dẫn trong ticket để thay đổi dữ liệu đơn hàng.
- Truyền quote đầy đủ vào `issue_refund`, để host kiểm approval và trừ phần đã hoàn trước theo trần của đơn. `proposal_amount` giữ quote gốc, không thay bằng số tiền thực ghi ledger.
- Truyền `crash_at` vào host. Khi gặp `InjectedCrash`, ghi trace rồi phát sinh lại lỗi để kiểm tra crash/resume; đóng kết nối trong `finally`.
- Ghi trace ở mọi nhánh trả về, chỉ dùng dữ liệu order đã lọc qua tool; không ghi ticket hay claim/order row thô.
- Thêm `src/tests/test_workflow_ticket_boundary.py`, với test `test_ticket_cannot_override_order_or_leak_into_trace` chạy ở seed 11 và 55. Test thay ticket bằng yêu cầu bỏ qua policy và khai trễ 99 ngày, kiểm tra workflow vẫn từ chối theo dữ liệu thật, không gọi model và không ghi dấu nhận diện riêng của ticket vào trace.

## 4. Bằng chứng

- [Commit triển khai workflow và test](https://github.com/vuductam20022004/K5-L3A-DAY08-MEOMEO-FromWorkflowsToAgents/commit/c24ed30ebe6f6095972c2e52f70fe1e922f69d92).
- Code: [workflow.py](../../src/lab8/shapes/workflow.py).
- Test bổ sung: [test_workflow_ticket_boundary.py](../../src/tests/test_workflow_ticket_boundary.py).


Kết quả đã ghi nhận trong phiên làm việc:

| Kiểm tra | Kết quả |
| --- | --- |
| Smoke test | `lab8.smoke pass` |
| Ma trận student của workflow | `62 passed, 242 deselected` |
| Test host và test bổ sung | `56 passed, 248 deselected` |

## 5. Công cụ AI đã dùng

Sử dụng ChatGPT/Codex để đọc và tóm tắt tài liệu lab, giải thích phân công, hỗ trợ triển khai workflow và test, chạy kiểm tra trong workspace, hướng dẫn thao tác Git.

Code workflow và test có sự hỗ trợ trực tiếp của AI. Tôi đã chạy test trước khi commit và đẩy phần việc lên nhánh `trang`. Việc kiểm chứng dựa trên ma trận student, test host và test bổ sung; không lấy câu trả lời của AI làm bằng chứng thay cho kiểm tra. Số liệu test và mã commit trong báo cáo lấy từ lần chạy và lịch sử Git, không tạo số liệu benchmark hoặc hidden giả.

## 6. Tự đánh giá
