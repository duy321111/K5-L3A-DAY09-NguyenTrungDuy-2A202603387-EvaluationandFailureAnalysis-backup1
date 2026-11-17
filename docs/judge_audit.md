# Judge audit

Positive class = FAIL: đo khả năng phát hiện lỗi, không phải tỷ lệ đồng ý chung.

| Tiêu chí | n | κ | Precision | Recall | tp/fp/fn/tn | Quyết định |
|---|---|---|---|---|---|---|
| tone | 100 | 0.757 | 0.857 | 0.8 | 24/4/6/66 | Đạt calibration; chỉ dùng cho tone |
| helpful | 100 | 0.375 | 1.0 | 0.3 | 9/0/21/70 | Loại khỏi gate |

Floors: κ ≥ 0.6, P ≥ 0.8, R ≥ 0.7; κ không xác định là FAIL. Helpful bỏ sót 21/30 lỗi dù precision=1: không được dùng làm gate.

## Audit bất đồng và sửa rubric

Audit dưới đây dựa trên nhãn tham chiếu và note công khai; không phải đánh giá người độc lập trên held-out mới.

| Case | Human | Judge | Kết luận theo bằng chứng | Sửa rubric |
|---|---|---|---|---|
| H-008 | FAIL | PASS | Theo human: xưng 'em' + 'nha', quá suồng sã với khách; judge coi là thân thiện | Không coi xưng em/nha quá suồng sã là đạt chỉ vì thân thiện. |
| H-017 | FAIL | PASS | Theo human: xưng 'bạn' với khách lớn tuổi; judge coi là thân thiện | Yêu cầu cách xưng anh/chị đúng ngữ cảnh khách hàng. |
| H-029 | FAIL | PASS | Theo human: giọng ra lệnh ('không cần nhắn thêm'); judge chỉ thấy 'Dạ, vui lòng' | Đánh giá cả câu mang tính ra lệnh, không chỉ nhận diện Dạ/vui lòng. |
| H-042 | PASS | FAIL | Theo human: ngắn nhưng đủ ý; judge phạt vì 'thiếu xin lỗi' | Không bắt buộc xin lỗi cho mọi thông báo; ngắn nhưng rõ vẫn đạt. |
| H-051 | PASS | FAIL | Theo human: dùng từ 'refund' — CS LogiX cho phép; judge phạt vì tiếng Anh | Cho phép thuật ngữ refund theo style guide LogiX. |
| HL-015 | FAIL | PASS | Theo human: ledger ghi 40.000đ | Tiền trong reply phải so với ledger bằng code; không suy ra helpful từ giọng văn. |
| HL-016 | FAIL | PASS | Theo human: ledger ghi 35.000đ | Lời xin lỗi dài không bù được việc báo sai tiền; dùng code kiểm tiền. |

Rogan–Gladen: tone observed FAIL=0.28, sensitivity=0.8, specificity=66/70; corrected=0.30. Helpful observed=0.09, corrected=0.30, nhưng hiệu chỉnh tỷ lệ không sửa được lỗi phân loại từng case và không khiến judge đạt calibration.

Khi sensitivity + specificity ≤ 1, rate correction không xác định/không dùng được. Cần nhãn người mới và held-out trước khi dùng với LLM thật.
