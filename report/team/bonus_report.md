# Bonus report: B7 — Kiểm toán grader

- Topic + nguồn: B7, *Rethinking Evaluation of MAS Efficiency* (EMNLP 2026, slide 44, 59), theo danh mục trong `docs/bonus_topics.md`; đặc tả thực thi là `src/grader_audit/README.md`.
- CLAIM theo đề bài: lỗi thước đo có thể làm lệch so sánh kiến trúc dù shape xử lý đúng. Không dùng kết quả audit để khẳng định các con số khác của paper.
- BOUNDARY: ba grader và fixture giảng viên cung cấp, không phải kiểm toán model sản xuất; không thay grader, fixture hoặc `lab8/metrics.py`.
- HYPOTHESIS: thêm lỗi hạ tầng không đổi pass rate được chấm; nhân đôi trial giữ tỷ lệ và nhân đôi tổng; thay delay 2→3 lật entitlement đúng luật; đảo thứ tự trial độc lập không đổi thống kê.
- Biến cố định/thay đổi: giữ nguyên từng cặp fixture cho cả A/B/C; chỉ đổi implementation summarize. Quan hệ delay kiểm chung `compensation.quote`, không phân biệt grader.
- File report + run id: `src/reports/bonus_grader_audit.json`, `B7-c30b412c7324`; JSON do script sinh, kèm SHA-256 của grader/fixture/code audit, expected/actual cho mọi phép kiểm.

## Tái lập

Chạy từ `src/`, không cần mạng hoặc API key:

```powershell
.\.venv\Scripts\python.exe -m bonus.grader_audit --out reports/bonus_grader_audit.json
.\.venv\Scripts\python.exe -m pytest -q tests/test_bonus_grader_audit.py -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q tests/test_bonus_grader_audit.py --runxfail -p no:cacheprovider
```

Lệnh test thường: **17 passed, 5 xfailed**. Năm `xfail(strict=True)` là lỗi của grader được cung cấp: nếu grader bất ngờ hết lỗi, XPASS làm suite đỏ. Năm test riêng kiểm chính xác tập metric bị lỗi để xfail không che sai lệch ở metric khác; ba test kiểm grader trả rỗng phải bị phát hiện. Lệnh `--runxfail` cố ý hiện assertion gốc: **5 failed, 17 passed**, exit code 1. Không chạy `--extra-shape` vì B7 không tạo shape mới.

Bộ test mặc định sau bổ sung: **99 passed, 248 deselected, 5 xfailed**. `python -m lab8.check_submission` hiện có **1 FAIL, 1 WARN**: `_check_bonus` tại `src/lab8/check_submission.py:243` chỉ nhận regex `B[1-6]`, trong khi rubric và `docs/bonus_topics.md` cho phép B7. Đây là lỗi tương thích cần giảng viên xác nhận/cập nhật checker; báo cáo giữ đúng B7 và không sửa checker để vượt cổng. WARN là thay đổi chưa commit. Kết quả “0 FAIL” trước khi tạo báo cáo bonus không còn áp dụng.

## Kết quả

Bảng từ JSON, dấu “lệch” nghĩa là vi phạm quan hệ, không phải test bị thiếu.

| Bản | Delay 2→3 | Thêm lỗi hạ tầng | Nhân đôi danh sách | Đảo thứ tự (mới) |
| --- | --- | --- | --- | --- |
| A | Đạt: 0→35000 | Đạt | Lệch: cost/success 31,50→26,28; tổng 473 thay vì 567; pass^5 2/3→0 | Lệch: tổng cost 283,50→285,00 |
| B | Đạt: 0→35000 | Đạt | Lệch: pass^5 2/3→0 | Đạt |
| C | Đạt: 0→35000 | Lệch: pass rate 0,75→0,5625; graded 12→16 | Lệch: pass^5 2/3→0 | Đạt |

Trên input gốc `metamorphic_duplicate.a`, cả ba có pass rate 0,75; pass^5 0,666667; seed variance 0,006944. Cost/success: A = 31,50; B/C = 21,055556 VND mô phỏng. Fixture chỉ có **2 seed**, nên khóa `pass_5` ở đây thể hiện pass trên mọi seed có trong fixture; không diễn giải là đã chạy 5 seed.

**Chẩn đoán theo hành vi:**

- A cộng thêm chi phí của trial đầu tiên của mỗi claim: tổng gốc thành 283,50 thay vì 189,50. Nhân đôi danh sách không nhân đôi khoản cộng thêm; đảo thứ tự đổi trial được chọn nên đổi cost.
- C đổi `infra_error` thành `passed=False`, làm timeout/crash đi vào mẫu số quyết định nghiệp vụ. Bốn trial hạ tầng làm pass rate từ 9/12 xuống 9/16.
- Cả A/B/C dùng chung base `summarize`: kiểm `len(claim_rows) == len(seeds)` cho pass^5. Nhân đôi trial tạo 4 hàng/claim nhưng vẫn 2 seed, nên các claim vốn pass đều mất điểm pass^5. B đúng với loại trừ hạ tầng và các phép tính cost trong fixture, **không có bản nào đạt toàn bộ quan hệ**. Không sửa thước đo để làm kết quả đẹp hơn.

**Quan hệ mới:** đảo thứ tự những trial độc lập phải giữ mọi thống kê. Test đột biến bổ sung một lỗi chi phí phụ thuộc seed đầu vào trên B: ba quan hệ cũ cho đúng cùng kết quả như B, nhưng quan hệ mới phát hiện sai lệch bổ sung. Điều này kiểm tra được độ nhạy mới, thay vì chỉ kiểm lỗi A đã bị quan hệ nhân đôi bắt.

## Kết luận và giới hạn

Kết quả ủng hộ hypothesis rằng cần kiểm thước đo trước khi suy ra hiệu quả kiến trúc: cả lỗi cost, xử lý hạ tầng và pass^5 đều có bằng chứng tái lập. Không kết luận mọi benchmark trước đó sai: lỗi pass^5 này cần dữ liệu trùng, không phát sinh trên ma trận chuẩn mỗi claim/seed đúng một lần.

Metamorphic testing hữu ích vì biết quan hệ giữa hai input ngay cả khi không có oracle tuyệt đối. Tuy nhiên sai lệch cố định nhân mọi cost với 2 có thể qua cả bốn quan hệ; cần thêm kiểm tra tổng chi phí bằng phép cộng độc lập. Cũng cần thêm ca nhiều shape, không có success, không có trial và seed thiếu. Nếu định nghĩa thống kê đổi, phải xem lại quan hệ; việc tính lỗi hạ tầng vào tỷ lệ hoàn thành toàn hệ thống là metric khác, cần đặt tên riêng.

Không gọi model hoặc thực thi refund trong audit; safety counts là **không áp dụng**, không báo số 0 như bằng chứng an toàn. MockLLM và giá lab là mô phỏng; latency unavailable. Phần CP5 cap 8/cap 2 vẫn là thí nghiệm riêng, không dùng nó làm topic bonus thứ hai.

Kiểm tra hidden cục bộ sau khi nhận pack: `workflow` (shape nhóm chọn) và `single` đều đạt **200/200**, pass rate/pass^5 = 1, variance = 0; cost/success lần lượt **29,00** và **33,1725** VND mô phỏng. Nguồn: `%TEMP%/lab8-hidden-selfcheck.json`, không commit pack/nhãn. Lệnh chạy từ `src/`:

```powershell
.\.venv\Scripts\python.exe -m lab8.benchmark --shapes workflow,single --cases ../instructor/instructor/hidden_claims.jsonl --world ../instructor/instructor/hidden_world_state.json --labels ../instructor/instructor/hidden_labels.json --seeds 11,22,33,44,55 --out "$env:TEMP/lab8-hidden-selfcheck.json"
```

Đã vượt ngưỡng pass rate 0,80 trong benchmark cục bộ; chưa có kết quả grader chính thức xác nhận đầy đủ ba must-pass và các safety counts. Không dùng kết quả này để khẳng định đã nhận điểm bonus.
