# Báo cáo cá nhân - Lê Quốc Anh

- **Họ tên**: Lê Quốc Anh
- **MSSV**: 2A202600824
- **Nhóm**: 24
- **Lab**: Chatbot vs ReAct Agent

---

## 1. Vai trò trong nhóm

Em phụ trách chính phần **baseline chatbot, evaluation và so sánh kết quả giữa baseline với ReAct Agent**. Phần này giúp nhóm có mốc đo rõ ràng thay vì chỉ demo agent bằng một câu hỏi đơn lẻ.

Các file liên quan:

```text
src/chatbot.py
scripts/run_baseline.py
scripts/run_evaluation.py
evaluation/results.json
evaluation/summary.md
report/group_report/GROUP_REPORT_NHOM_24.md
```

---

## 2. Công việc đã thực hiện

### 2.1 Baseline chatbot

Baseline chatbot nằm trong `src/chatbot.py`. Nó không dùng ReAct loop mà xử lý trực tiếp:

```text
query -> extract identifier -> categorize_academic_performance -> answer
```

Vai trò của baseline là làm điểm so sánh. Nếu chỉ cần trả lời một câu hỏi đơn giản, baseline có thể đủ. Nhưng baseline không có trace, không cho biết nó đã đi qua bước validate, tính average hay kiểm tra môn trượt như thế nào.

### 2.2 Script chạy baseline

Script:

```text
scripts/run_baseline.py
```

Mục tiêu là giúp người chấm chạy nhanh baseline mà không cần mở Python shell.

Ví dụ output:

```text
Royce Lowe has an average score of 8.39 and is categorized as Giỏi.
```

### 2.3 Evaluation cases

Em hỗ trợ xây dựng các case benchmark trong `scripts/run_evaluation.py`:

| Case | Mục tiêu kiểm tra |
| --- | --- |
| Royce Lowe | Sinh viên học lực Giỏi |
| Emmanuel Myers | Sinh viên học lực Khá |
| Axl Waters | Sinh viên có môn trượt |
| Invalid student | Không được hallucinate dữ liệu |

Các case này được dùng để so sánh:

```text
baseline_success
agent_success
```

Evaluation sinh ra:

```text
evaluation/results.json
evaluation/summary.md
```

### 2.4 So sánh baseline và ReAct Agent

Kết luận chính:

- Baseline nhanh và đơn giản.
- ReAct Agent rõ ràng hơn vì có `Thought`, `Action`, `Observation`.
- Baseline phù hợp làm mốc kiểm tra logic.
- ReAct Agent phù hợp hơn khi cần audit và debug.

Trong report nhóm, phần so sánh này giúp giải thích vì sao nhóm không chỉ dùng một chatbot trực tiếp.

---

## 3. Cập nhật theo repo hiện tại

Sau khi repo có thêm terminal chat và web UI, evaluation vẫn giữ vai trò quan trọng. Web UI đẹp hơn nhưng không thay thế benchmark. Người dùng có thể nhập nhiều câu khác nhau trên web, còn evaluation đảm bảo các case lõi không bị hỏng khi nhóm chỉnh parser hoặc provider.

Các thay đổi mới liên quan:

- input yêu cầu đủ `student_id`, `name`, `id_card`;
- agent chấp nhận input tiếng Việt linh hoạt;
- web UI gọi `/api/chat`;
- test suite tăng lên `25 passed`;
- report nhóm đổi sang `GROUP_REPORT_NHOM_24.md`.

---

## 4. Debugging case study

### Vấn đề

Khi agent đã có nhiều feature hơn baseline, nếu chỉ nhìn final answer thì khó biết agent đúng vì tool hay đúng vì model đoán may.

### Cách xử lý

Evaluation lưu cả:

```text
expected_tool_result
baseline answer
agent answer
agent trace
success flag
```

Nhờ vậy nhóm có thể kiểm tra:

- baseline có trả đúng category không;
- agent có gọi đúng tool không;
- invalid student có bị bịa dữ liệu không;
- case có môn trượt có được xử lý đúng policy không.

---

## 5. Kết quả kiểm tra

Các file kiểm thử liên quan:

```text
tests/test_chatbot.py
tests/test_evaluation.py
tests/test_agent.py
```

Kết quả hiện tại:

```text
25 passed
```

---

## 6. Nhận xét cá nhân

Qua phần baseline và evaluation, em thấy một hệ thống agent nên có mốc so sánh đơn giản. Nếu không có baseline, nhóm khó chứng minh ReAct Agent cải thiện ở điểm nào. Baseline có thể trả lời đúng ở case đơn giản, nhưng ReAct Agent có giá trị ở traceability, khả năng dùng nhiều tool và khả năng giải thích failure.

---

## 7. Hướng cải thiện

1. Thêm nhiều benchmark hơn cho input tiếng Việt.
2. Thêm case hỏi điểm từng môn, không chỉ học lực.
3. Tách metric precision/recall cho category và not-found.
4. Xuất evaluation summary ra bảng HTML để xem trên web UI.
5. So sánh latency giữa baseline, demo provider và OpenAI provider.
