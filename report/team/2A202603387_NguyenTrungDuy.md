# Báo cáo cá nhân — Nguyễn Trung Duy

## 1. Thông tin thành viên

- Họ tên: Nguyễn Trung Duy
- MSSV: 2A202603387
- Email: duy321111@gmail.com
- GitHub: duy321111
- Vai trò: Người 2 — Single Agent (ReAct)

## 2. Phần việc phụ trách

| Giai đoạn | Công việc thực hiện | File / bằng chứng |
| --- | --- | --- |
| CP1 | Kiểm tra môi trường Python 3.12.10, dependencies; đọc business_rules.md, contracts.md và swarm_reference.py | src/.venv; pip check và smoke đạt |
| CP2 | Triển khai decide() và run_react với max_steps=8, worker=True | src/lab8/shapes/single.py |
| CP3 | Truyền crash_at tới host, không bắt InjectedCrash; đóng connection trong finally | single.py; test ba điểm crash |
| CP4 | Kiểm approval, injection, secret/PII leak, step cap và ma trận public | src/tests/test_single_agent.py |
| CP5 | Điền research card, chạy ablation cap 8 so với cap 2, viết báo cáo này | research_card.md; src/experiments/single_cap2.py; src/reports/single_ablation.json |

Thí nghiệm phục vụ CP5, không đăng ký điểm bonus. Biến thể single_cap2 chỉ là đối chứng; shape nộp chính là single.

## 3. Đóng góp cụ thể

- decide() lần lượt chọn lookup_order, compute_compensation rồi trả final. Không suy diễn order_id hay delay_days từ ticket.
- Chỉ đưa claim_id, principal_id, order_id và found vào context. Không truyền ticket, parent_secret hay header cho agent.
- Mỗi vòng gọi MockLLM để ghi nhận usage vào Budget. MockLLM mô phỏng chi phí; decide() là adapter chọn tool bằng code, không phải model thật sinh tool call.
- Số tiền được lấy trực tiếp từ observation của compute_compensation, không từ final action. Quote bằng 0 thì denied và không gọi issue_refund.
- Quote dương được truyền đầy đủ cho durability.issue_refund. Host kiểm approval, trần theo đơn và idempotency; shape không tự trừ số đã hoàn.
- Host từ chối thì denied, conflict thì failed; proposal_amount giữ quote đầy đủ. finish() lấy ledger/audit thật và ghi trace cho mọi nhánh trả kết quả.
- Agent chỉ được gọi tool đọc qua worker=True. Runtime giới hạn 8 lần decide(); hết bước trả failed/step_cap và không ghi refund.
- Crash lan truyền ra caller. Test kiểm cả before_effect, after_effect_before_checkpoint và after_checkpoint; resume chỉ có một effect và một committed audit.
- Thêm 12 test: step cap, ticket injection, unknown claim, ba điểm crash, bốn dạng approval sai, approval thấp hơn quote và kiểm tra secret/PII.
- Commit: 1d8278d
## 4. Bằng chứng

Các lệnh chạy từ src/ bằng Python trong .venv:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m lab8.smoke
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= -k 'single and not workflow and not swarm and not orchestrator' -p no:cacheprovider
```

- Dependencies: No broken requirements found.
- Smoke: lab8.smoke pass, trace clean.
- Bộ host và test mới: 66 passed, 248 deselected.
- Ma trận public riêng single: 62 passed, 252 deselected.
- test_single_invalid_approval_is_audited: missing, revoked, expired, claim mismatch đều denied; quote 35000 được giữ, không ghi refund, audit policy_denied đúng reason.
- test_single_full_quote_and_lower_approval: quote 35000, approval 10000 → effect 10000, proposal_amount vẫn 35000.
- test_single_trace_excludes_private_fields: canary trong parent_secret, Authorization header, phone, address, internal_note và item_name không xuất hiện trong trace/kết quả/stdout/stderr; trace đúng run_id và có events.
- Ablation trên 14 claim × 5 seed: single cap 8 đạt 70/70, cap 2 đạt 10/70; cost/success 31,83 so với 213,41 VND mô phỏng. Lệnh và giới hạn ghi ở research_card.md; số liệu từ src/reports/single_ablation.json.

## 5. Công cụ AI đã dùng
Tôi dùng Codex để hỗ trợ đọc tài liệu, giải thích vòng ReAct, gợi ý triển khai single.py, viết test và soạn bản nháp báo cáo. Số liệu kiểm thử lấy từ các lệnh đã chạy, không tự tạo.

## 6. Tự đánh giá

Phần kỹ thuật đã được kiểm tra trên bộ public; chưa chạy hidden. Chưa thể kết luận hiệu quả với model sản xuất: MockLLM và giá đều mô phỏng, latency unavailable. Qua bài lab, tôi nắm được luồng xử lý cơ bản của Single Agent: đọc claim, kiểm tra đơn hàng, gọi tool tính tiền rồi chuyển quote đầy đủ cho host kiểm approval và ghi refund. Tôi hiểu agent chỉ được dùng tool đọc; host chịu trách nhiệm chống hoàn tiền trùng khi chạy lại.
