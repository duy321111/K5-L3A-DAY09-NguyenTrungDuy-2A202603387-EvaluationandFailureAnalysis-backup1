# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

**Phạm vi: Thí nghiệm phục vụ CP5, không đăng ký điểm bonus.**

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri et al., Why Do Multi-Agent LLM Systems Fail?, NeurIPS 2025, https://arxiv.org/abs/2503.13657 ; nghiên cứu thực nghiệm và taxonomy MAST. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | MAST chia lỗi MAS thành specification/system design, inter-agent misalignment và task verification/termination. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Taxonomy từ các hệ MAS trong nghiên cứu; không chứng minh hiệu quả trên LogiX-VN hoặc single agent. Áp dụng nhóm termination cho single ở đây là giả thuyết của nhóm. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Giảm step cap single từ 8 xuống 2 sẽ dừng trước final trên claim cần đọc order và quote; dự đoán pass rate giảm ít nhất 50 điểm phần trăm và cost/success tăng. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ MockLLM, decide/prompt, tools, 14 claim public, seed 11/22/33/44/55, pricing và evaluator; fresh SQLite mỗi trial. Chỉ thay max_steps 8→2 qua experiments/single_cap2.py. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Termination sớm: status failed, error_reason step_cap dù đã đọc quote. Đo pass rate, pass^5, seed variance và VND mô phỏng/success. Phân loại termination là cách vận dụng của nhóm, không phải kết quả paper về lab này. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn), từ src/:

```powershell
.\.venv\Scripts\python.exe -m lab8.benchmark --shapes single,single_cap2 --extra-shape single_cap2=experiments.single_cap2:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/single_ablation.json
```

- Run id / file report: src/reports/single_ablation.json; 70 trial cho mỗi biến thể, JSON do benchmark sinh lại sau khi viết lại single.py. Không sửa tay JSON.
- Kết quả: phù hợp hypothesis. Cap 8 đạt 70/70, pass rate/pass^5 = 1.000; cap 2 đạt 10/70, pass rate/pass^5 = 0.142857 (giảm 85,71 điểm phần trăm). Seed variance đều 0. Cost/success tăng 31,83→213,41 VND mô phỏng. Cap 2 fail 60 trial: 35 cần resolved, 25 cần denied; đủ đọc quote nhưng thiếu bước trả final.
- Giới hạn bổ sung: đây là ablation step cap, không chứng minh single tốt hơn MAS. Chưa chạy hidden. Mean steps trong benchmark đếm trace events, khác số vòng ReAct. Wrapper cap 2 patch tạm trong tiến trình benchmark tuần tự, không dành cho chạy đồng thời.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Biến thể single_cap2 chỉ dùng làm đối chứng cho research card CP5; shape nộp chính là single.
