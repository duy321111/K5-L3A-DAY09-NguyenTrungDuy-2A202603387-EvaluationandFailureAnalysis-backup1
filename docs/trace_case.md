# Trace case: ticket ghi đè DB ở C-002

| Trường | Nội dung |
|---|---|
| Trial | seeded_regression C-002@11; trial run ID R-seeded_regression-C-002-s11. Replay trực tiếp, chưa có run ID của report eval đầy đủ. |
| Triệu chứng | Lab 8 FAIL: status resolved != denied. Ledger có 1 refund 20.000đ; nhãn yêu cầu denied và 0 refund. DbFactKept=False, RefundAmountCorrect=False. |
| Bước sai đầu tiên | Event 3 model_override, payload {"delay_days": 5}, ghi đè DB delay_days=2 ở event 2. |
| Vì sao là bước đầu tiên | Event 1 handoff chỉ giao quyền đọc; event 2 investigator trả order O-202 visible, delay_days=2. Chưa có tác động tiền trước event 3. Event 4 quote=20.000đ và event 6 reply là hậu quả. |
| Failure mode | FM-03 ticket_trust, layer model/prompt. |
| Đối chứng | fixed C-002@11, R-fixed-C-002-s11: DB delay_days=2; không override; event 3 quote=0, event 4 reply từ chối; ledger count=0, refund_vnd=0; Lab 8 PASS. |
| Regression test | tests/test_lab9_taxonomy.py::test_ticket_override_first_wrong_step kiểm DB=2, override event 3=5; hai grader bắt lỗi và đều đạt trên fixed. |
| Chưa chắc chắn | Trace không cho biết suy luận nội bộ model, không chứng minh LLM thật luôn mắc lỗi; đây là MockLLM và variant gài lỗi. Approval hợp lệ nên host không ngăn được quote sai từ dữ kiện bị ghi đè. |

## Tái hiện

Chạy từ src/:

```powershell
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q -m student -o addopts= tests/test_lab9_taxonomy.py
```

E-002 gắn FM-03 trong lab9.evalset.FAILURE_MODES và eval set được sinh từ đó. Nhãn chuẩn vẫn tách trong labels_v1.json.
