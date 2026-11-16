# Bàn giao Người 3 — Vũ Đức Tâm, 2A202603522

Phạm vi theo `plan.md`: Orchestrator + Handoff, test bảo mật/crash, mục 3 báo cáo nhóm và phần trace trong ADR. Môi trường và kiểm tra dưới đây thực hiện ngày 16/11/2026 trên Windows/Python 3.13.13.

Code Orchestrator, test và benchmark đã được lưu trong commit `9cecb25`. Workflow và Single của đồng đội đã được tích hợp; ADR dùng hash của commit chứa code và report này.

## Mở môi trường trên máy này

Từ gốc repository:

```powershell
cd src
.\.venv\Scripts\Activate.ps1
python --version
python -m pip check
python -m lab8.smoke
```

Nếu PowerShell chặn activation, dùng trực tiếp executable, không cần thay đổi execution policy:

```powershell
cd src
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m lab8.smoke
.\.venv\Scripts\python.exe -m pytest -q
```

Nếu terminal đã ở `src/`, bỏ dòng `cd src`. Lệnh `python` ngoài venv trên máy này trỏ WindowsApps và `py -0p` chưa tìm thấy Python phù hợp; dùng venv đã kiểm chứng. Venv đang có pytest 8.4.2 và PyYAML 6.0.3 đúng requirements, đã bổ sung pip 26.0.1. `.venv/` và `.tools/` không đưa vào Git. Khi sang máy khác, tạo venv mới theo `src/README.md`, không sao chép venv.

## Kiểm phần của Tâm

Sau khi activate, đứng ở `src/`:

```powershell
python -m pytest -q
python -m pytest -q -m student -o addopts= -k orchestrator
python -m pytest -q tests/test_orchestrator_safety.py
```

Kết quả sau tích hợp: cổng host 82 pass, toàn bộ ma trận student 248 pass; student Orchestrator 62 pass, test riêng Orchestrator 14 pass. Các test mới có fixture đổi cwd sang thư mục tạm để trace không đè nhau.

Tái tạo ví dụ handoff và T14; mỗi ví dụ cần DB chưa tồn tại nếu muốn trial mới:

```powershell
python -m lab8.run --shape orchestrator --claim-id C-010 --seed 55 --db reports/tam-handoff.sqlite
python -m lab8.run --shape orchestrator --claim-id C-014 --seed 11 --db reports/tam-topup.sqlite
```

T14: `proposal_amount=150000`, effect `120000`, một audit committed. Lần chạy lại trên cùng DB là retry, không phải trial độc lập. Các file SQLite và `traces/` được ignore.

Kiểm crash riêng Orchestrator bằng DB mới:

```powershell
python -m lab8.run --shape orchestrator --claim-id C-012 --seed 11 --db reports/tam-crash.sqlite --crash-at after_effect_before_checkpoint
python -m lab8.run --shape orchestrator --claim-id C-012 --seed 11 --db reports/tam-crash.sqlite
```

Lệnh đầu trả exit code 2 và thông báo crash; lệnh sau `resolved`, một refund và một audit. Chọn tên DB khác nếu file đã tồn tại. Ba điểm crash đều được kiểm tự động trong test mới trên T14, đồng thời xác nhận phần chênh 120.000 không bị trừ hai lần.

## Bằng chứng đã sinh

```powershell
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.check_submission
```

`benchmark.json` và `crash.json` được công cụ chính thức sinh, không sửa tay. Orchestrator: 70/70 public trial, pass/pass^5 1/1, variance 0, cost/success 47,447142857 VND mô phỏng, mean/p95 steps 5,357142857/6. Crash suite chuẩn host + swarm đạt 20/20; không suy ra đó là 20 crash riêng Orchestrator. Không có `student_drop/`, chưa đo hidden. Latency `unavailable`.

Benchmark đã sinh lại sau khi tích hợp cả ba shape: Workflow, Single và Orchestrator đều đạt 70/70 public trial. `check_submission` đã ra `0 FAIL`; commit `9cecb25` chứa code và report dùng cho ADR.

## Bàn giao để nộp nhóm

1. Tâm review code, report và số liệu đã tích hợp; tự xác nhận phần tự đánh giá trong `report/team/2A202603522_VuDucTam.md`.
2. Commit code và report `9cecb25` đã có. ADR, báo cáo nhóm và TEAM.md dẫn đúng hash này; các chỉnh sửa ghi hash được lưu ở commit tài liệu kế tiếp vì không thể ghi hash của chính một commit vào nội dung commit đó.
3. Chạy `python -m lab8.check_submission` lại; đảm bảo nhánh nộp `main` chứa công việc của `tam` trước khi push/nộp.
4. Mỗi thành viên tự nộp cùng link repo trên LMS; repo GitHub phải mở được cho giảng viên. Chưa có pack hidden nên chưa có kết quả hidden.

Theo SUBMISSION.md: lớp sáng hạn 23h59 GMT+7 ngày lab; lớp chiều/tối hạn 11h59 GMT+7 ngày hôm sau, trừ khi coach thông báo gia hạn. Nhánh hiện tại là `tam`; cần tích hợp vào nhánh nộp do nhóm thống nhất. Repo GitHub phải mở cho giảng viên.

## Những điểm cần tự giải thích

- Handoff chỉ mang task/facts allowlist; runtime từ chối write tool và lọc principal khi đọc order. Bản này điều phối cố định bằng code, không mô phỏng model chọn tool động.
- Ticket là dữ liệu không đáng tin; không được đổi `delay_days` hoặc lấy mã đơn/approval từ ticket.
- `compute_compensation` tính entitlement; host chịu trách nhiệm approval, cap và ledger. T14 truyền 150.000 thay vì 120.000 vì host tự trừ 30.000.
- Checkpoint không bảo đảm exactly once. Ledger có key `refund:{claim_id}`, refund/audit cùng transaction mới làm retry an toàn.
- Trace là bề mặt dữ liệu scanner nhìn thấy. Ghi cả row thô hoặc tóm tắt bằng LLM có thể lộ dữ liệu; field allowlist mới là ranh giới. Mọi nhánh return và nhánh crash đều phải ghi trace.
