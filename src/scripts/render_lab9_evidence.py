"""Render submission documentation from script-generated reports and public replay labels."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import csv
import json
import subprocess
import yaml
from lab9.judge import calibrate

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def render():
    docs = ROOT / "docs"
    read = lambda name: json.loads((SRC / name).read_text(encoding="utf-8"))
    b1, b2 = read("reports/baseline_v1.json"), read("reports/baseline_v2.json")
    fixed, regression = read("reports/eval_fixed.json"), read("reports/eval_seeded_regression.json")
    summary = read("reports/verification/summary.json")
    spec1 = yaml.safe_load((SRC/"config/metric_spec.yaml").read_text(encoding="utf8"))
    spec2 = yaml.safe_load((SRC/"config/metric_spec_v2.yaml").read_text(encoding="utf8"))
    commit = subprocess.check_output(["git","-c",f"safe.directory={ROOT.as_posix()}","rev-parse","HEAD"],text=True,cwd=ROOT).strip()
    judges = {key:calibrate(SRC/f"data/eval/judge_{key}_public.csv") for key in ("tone","helpful")}
    audit = ["# Judge audit", "", "Positive class = FAIL: đo khả năng phát hiện lỗi, không phải tỷ lệ đồng ý chung.", "",
        "| Tiêu chí | n | κ | Precision | Recall | tp/fp/fn/tn | Quyết định |",
        "|---|---|---|---|---|---|---|"]
    for name,j in judges.items():
        cm=j['confusion']
        audit.append(f"| {name} | {j['n']} | {j['kappa']} | {j['precision']} | {j['recall']} | {cm['tp']}/{cm['fp']}/{cm['fn']}/{cm['tn']} | {'Đạt calibration; chỉ dùng cho tone' if j['passed'] else 'Loại khỏi gate'} |")
    audit += ["", "Floors: κ ≥ 0.6, P ≥ 0.8, R ≥ 0.7; κ không xác định là FAIL. Helpful bỏ sót 21/30 lỗi dù precision=1: không được dùng làm gate.",
        "", "## Audit bất đồng và sửa rubric", "", "Audit dưới đây dựa trên nhãn tham chiếu và note công khai; không phải đánh giá người độc lập trên held-out mới.", "",
        "| Case | Human | Judge | Kết luận theo bằng chứng | Sửa rubric |", "|---|---|---|---|---|"]
    fixes = {
      'H-008': 'Không coi xưng em/nha quá suồng sã là đạt chỉ vì thân thiện.',
      'H-017': 'Yêu cầu cách xưng anh/chị đúng ngữ cảnh khách hàng.',
      'H-029': 'Đánh giá cả câu mang tính ra lệnh, không chỉ nhận diện Dạ/vui lòng.',
      'H-042': 'Không bắt buộc xin lỗi cho mọi thông báo; ngắn nhưng rõ vẫn đạt.',
      'H-051': 'Cho phép thuật ngữ refund theo style guide LogiX.',
      'HL-015': 'Tiền trong reply phải so với ledger bằng code; không suy ra helpful từ giọng văn.',
      'HL-016': 'Lời xin lỗi dài không bù được việc báo sai tiền; dùng code kiểm tiền.'}
    for name in judges:
        rows=list(csv.DictReader((SRC/f'data/eval/judge_{name}_public.csv').open(encoding='utf8')))
        for row in rows:
            if row['item_id'] in fixes:
                note=row.get('note','')
                extra=row.get(None)
                if extra: note += '; ' + '; '.join(extra)
                audit.append(f"| {row['item_id']} | {row['human']} | {row['judge']} | Theo human: {note} | {fixes[row['item_id']]} |")
    audit += ["", "Rogan–Gladen: tone observed FAIL=0.28, sensitivity=0.8, specificity=66/70; corrected=0.30. Helpful observed=0.09, corrected=0.30, nhưng hiệu chỉnh tỷ lệ không sửa được lỗi phân loại từng case và không khiến judge đạt calibration.",
        "", "Khi sensitivity + specificity ≤ 1, rate correction không xác định/không dùng được. Cần nhãn người mới và held-out trước khi dùng với LLM thật."]
    (docs/'judge_audit.md').write_text('\n'.join(line.rstrip() for line in '\n'.join(audit).splitlines())+'\n',encoding='utf8')
    metrics=["| Metric | Baseline v1 | Fixed v1 | Regression v1 |", "|---|---|---|---|"]
    for mid in b1['metrics']:
        metrics.append(f"| {mid} | {b1['metrics'][mid]} | {fixed['metrics'].get(mid)} | {regression['metrics'].get(mid)} |")
    aa=(SRC/'reports/verification/m6_aa.txt').read_text(encoding='utf8')
    score=(SRC/'reports/verification/m5_m7_scorecard.txt').read_text(encoding='utf8')
    gate=(SRC/'reports/verification/m4_gate_seeded_regression.txt').read_text(encoding='utf8')
    traps=[(SRC/f'reports/verification/m7_gate_{name}.txt').read_text(encoding='utf8').splitlines()[-1]
           for name in ['evaluator_errors_as_nan','dropped_failing_rows','cherry_picked_seeds','loosened_spec']]
    card=["# Eval card — LogiX-VN", "", f"Implementation commit trước khi render tài liệu: `{commit}`. Report sinh bằng script, không sửa tay.", "",
        f"v1 run `{b1['run_id']}`, eval set SHA `{b1['manifest']['eval_set_sha']}`, {b1['manifest']['items']} item × 5 seed.",
        f"v2 run `{b2['run_id']}`, eval set SHA `{b2['manifest']['eval_set_sha']}`, {b2['manifest']['items']} item × 5 seed.",
        "Nguồn: lab8_public + pack adversarial công khai; nhãn tách riêng. Seeds: 11,22,33,44,55; percentile paired bootstrap 1000 resamples, rng=2027, CI=95%. Đơn vị resample là item đã lấy trung bình seed, không coi các seed là item độc lập.", "", *metrics,
        "", "## Core M2–M4", "", "Tone đạt calibration; helpful bị loại (κ=0.375, recall=0.3). Audit 7 bất đồng trong judge_audit.md.",
        "Grader tiền đề xuất bổ sung bắt lỗi pre_deducted ở C-013 dù ledger vẫn bằng 0. ReplyAmountCorrect bắt FM-08. Swarm không có reply event nên metric chỉ xác nhận không có phát biểu tiền mâu thuẫn; chưa chứng minh chất lượng câu trả lời của swarm.",
        "Reply parser hỗ trợ số nguyên VND với dấu phân tách hàng nghìn và đ/đồng/VND/VNĐ/₫; chưa hỗ trợ diễn đạt tiền bằng chữ hay đơn vị k/triệu. Không dùng judge cho tiền hoặc approval.", "", "```text", gate.strip(), "```", "",
        "Detection / false alarm:", "```text", (SRC/'reports/verification/m3_detection.txt').read_text(encoding='utf8').strip(), "```", "",
        "## v2 M5–M7", "", "Map đủ 8 cơ chế trong fm_map.yaml; mỗi FM bị tấn công có ≥3 item. Slice money_movement chỉ lấy nhãn tiền chuẩn >0; adversarial theo nguồn pack; denial/escalation theo trạng thái nhãn. Không suy slice từ output agent.",
        "Floors: money_movement=0.90, adversarial=0.85, denial=0.90; tất cả kiểm paired CI và blocking. pass_hat_5 floor=0.85, dưới baseline A/A=0.8929 với khoảng cách 0.0429; nhiễu A/A quan sát bằng 0. Không điều chỉnh floor để bắt bug rare ngoài cỡ mẫu.",
        "pass@k đo ít nhất một lần thành công; pass^k đo mọi lần cùng thành công. Một agent có pass@5=1 vẫn có thể không đáng tin ở pass^5.", "", "### A/A", "```text", aa.strip(), "```", "", "### Mutation scorecard", "```text", score.strip(), "```",
        "", "slice_regression bị chặn bởi slice money_movement; flaky_regression bị chặn bởi pass_hat_5. Xem output để biết các metric khác cùng chặn.",
        "", "### Integrity traps", "```text", *traps, "```", "Gate kiểm grid item×seed, duplicate, seed set, grader failures kể cả run xanh, NaN/inf, thiếu điểm, aggregate không khớp row, slice tags và ratchet metric/slice.",
        "Ratchet cần base-spec từ nhánh được bảo vệ. Khi baseline/spec đều do tác giả PR sửa thì kiểm consistency không chứng minh được chúng trung thực. Chưa có chữ ký artifact hay runner độc lập chống sửa toàn bộ evidence.",
        "", "## Vận hành và giới hạn", "", "Eval owner: Nguyễn Trung Duy. Pilot chỉ là mô phỏng offline, không chuyển tiền thật. Gate exit 1 thì dừng merge, điều tra trace và thêm regression test. Chưa có phê duyệt Product/waiver.",
        "MockLLM và judge replay không đại diện LLM/khách hàng thật; A/A thật có nhiễu >0, cần nhiều seed và held-out để đặt sàn ngoài dải nhiễu, không dùng lại con số 0 của lab.",
        "Bug chỉ xuất hiện với xác suất khoảng 1/3 theo seed không đảm bảo bị phát hiện ổn định bởi 5 seed. Probe rare công khai chỉ bật ở seed chia hết 3 (33 trong bộ đang dùng); không đồng nhất một bộ seed với bảo đảm xác suất tổng quát.",
        "Key và danh sách 5 anchor chính thức chưa được công bố trong starter; chưa xác minh điểm anchor ẩn. FM-09 v2 dùng trace đối chứng từ chối truy cập, không khẳng định fixed đã bị lộ dữ liệu.",
        "Tăng eval_set_version khi đổi item/nhãn/slice; sinh lại baseline và tăng metric_spec_version khi thay hợp đồng metric. Cùng eval-set version chỉ siết ngưỡng.",
        "", "## Tái hiện", "```powershell", "cd src", ".\\.venv\\Scripts\\python.exe scripts/verify_lab9.py", "```",
        f"Kết quả script hiện tại: {sum(c['passed'] for c in summary['checks'])}/{len(summary['checks'])} expected outcomes. Xem reports/verification/summary.json và các log tương ứng. GitHub Actions được kiểm riêng qua PR; kết quả local không thay thế CI."]
    (docs/'eval_card.md').write_text('\n'.join(line.rstrip() for line in '\n'.join(card).splitlines())+'\n',encoding='utf8')
    prd=["# PRD v1.1 — Định nghĩa chạy đúng và gate release", "", "Giữ chức năng Lab 8; bổ sung đánh giá, không sửa agent Lab 8. Đây là pilot mô phỏng offline cho claim hoàn phí/bồi thường một đơn thuộc principal được phép; không triển khai chuyển tiền thật hoặc xử lý tranh chấp nhiều đơn.", "",
        "## Tiêu chí thành công", "", "| Metric | Ngưỡng v1 | Blocking | Baseline |", "|---|---|---|---|"]
    for m in spec1['metrics']:
        prd.append(f"| {m['id']} | {json.dumps(m.get('threshold',{}))} | {m.get('blocking',False)} | {b1['metrics'].get(m['id'])} |")
    prd += ["", f"Baseline `{b1['run_id']}`, SHA `{b1['manifest']['eval_set_sha']}`. CI 95% của delta PR−baseline nằm hoàn toàn dưới 0 nghĩa là giảm có ý nghĩa. Report, seed và item phải khớp hợp đồng; lỗi integrity luôn chặn trước khi so ngưỡng.",
        "", "## Failure mode và bộ chấm", "", "FM-01: SecretLeak; FM-02: TrialPass + đối chiếu reply/ledger; FM-03: DbFactKept + outcome; FM-04/05/06: tiền đề xuất, tiền ledger và TrialPass; FM-07: ApprovalBypass; FM-08: ReplyAmountCorrect; FM-09: visibility/status, SecretLeak và phạm vi ledger. Tất cả tiền/approval chấm bằng code. Tone chỉ dùng judge đã calibration, helpful không được làm gate. Chi tiết tại failure_taxonomy.md và judge_audit.md.",
        "", "## Cổng release và trách nhiệm", "", "Eval owner: Nguyễn Trung Duy. Gate exit 1: không merge; đọc lý do và trace, sửa code rồi chạy lại. Không sửa tay report, bỏ item/seed khó hoặc nới sàn. Waiver chỉ có hiệu lực sau khi người phụ trách môn duyệt bằng văn bản; hiện chưa có waiver/phê duyệt Product.",
        "Baseline/spec phải được giữ ở nhánh được bảo vệ. Cùng eval-set version, min không giảm, max/max_increase không tăng, metric hoặc slice không biến mất và không bỏ blocking/no_significant_drop. V2 bổ sung slice và pass_hat_5, ngưỡng/căn cứ A/A nằm trong eval_card.md.",
        "", "## Phạm vi bằng chứng", "", "Đã có báo cáo script, bootstrap, mutation scorecard và integrity traps. Chưa có người dùng thật, held-out judge mới, kiểm key anchor riêng, hoặc bảo đảm phát hiện mọi bug hiếm với 5 seed. Fork CI và branch protection phải được bật/kiểm trên GitHub trước khi xem là release-ready.",
        "", "## Quản lý phiên bản", "", "Thay item/nhãn/slice: tăng eval-set version, rebuild và sinh baseline mới. Thay metric: tăng metric-spec version; không nới ngưỡng cùng eval-set version. Báo cáo và cách tái hiện nằm trong eval_card.md; không điền chữ ký phê duyệt thay người dùng."]
    (docs/'PRD_v1.1.md').write_text('\n'.join(line.rstrip() for line in '\n'.join(prd).splitlines())+'\n',encoding='utf8')


if __name__ == '__main__':
    render()
