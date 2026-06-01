# Báo cáo cá nhân - Lê Quốc Anh

- **Họ tên**: Lê Quốc Anh
- **MSSV**: 2A202600824
- **Nhóm**: 24
- **Lab**: Chatbot vs ReAct Agent

---

## I. Phần việc phụ trách

Trong phần chia việc của nhóm, em phụ trách chính phần **baseline chatbot** và phần so sánh giữa baseline với ReAct Agent. Mục tiêu là tạo một hệ thống đơn giản, không dùng ReAct loop, để nhóm có điểm mốc khi đánh giá agent.

Các file liên quan:

```text
src/chatbot.py
scripts/run_baseline.py
scripts/run_evaluation.py
evaluation/results.json
evaluation/summary.md
report/group_report/GROUP_REPORT_NHOM_F2.md
```

### 1. Xây dựng baseline chatbot

Baseline chatbot được giữ đơn giản. Nó nhận query của user, trích xuất ID card, sau đó gọi function phân loại học lực để trả lời.

Ví dụ query:

```text
Evaluate academic performance for student ID card 822067.
```

Output baseline:

```text
Royce Lowe has an average score of 8.39 and is categorized as Giỏi.
```

Baseline không có `Thought`, `Action`, `Observation`. Đây là điểm khác biệt chính so với ReAct Agent.

### 2. Làm rõ vai trò của baseline trong lab

Baseline không được thiết kế để tốt hơn agent. Nó dùng để trả lời câu hỏi:

```text
Nếu không dùng ReAct, hệ thống có trả lời được không?
Nếu trả lời được, ReAct khác gì?
```

Từ kết quả benchmark, baseline vẫn pass 4/4 case vì bài toán hiện tại có dữ liệu rõ và query đơn giản. Tuy nhiên baseline không cho thấy quá trình suy luận. Khi gặp lỗi, baseline khó debug hơn vì không có trace từng bước.

### 3. Hỗ trợ phần evaluation

Em tham gia chuẩn bị các case so sánh giữa baseline và agent:

```text
Royce Lowe / 822067 -> Giỏi
Emmanuel Myers / 107226 -> Khá
Axl Waters / 876012 -> Trung bình, có môn trượt
Invalid ID / 999999 -> not found
```

Các case này kiểm tra bốn tình huống khác nhau:

```text
1. Sinh viên học lực Giỏi.
2. Sinh viên học lực Khá.
3. Sinh viên có môn trượt.
4. ID card không tồn tại.
```

Việc có case invalid student giúp nhóm kiểm tra agent không hallucinate sinh viên không có trong dataset.

---

## II. Debugging case study

### Vấn đề gặp phải

Baseline ban đầu dễ bị hiểu nhầm là “đơn giản nên không cần kiểm tra nhiều”. Nhưng khi so sánh với ReAct Agent, baseline vẫn phải xử lý đúng các case dữ liệu.

Ví dụ case invalid:

```text
Evaluate academic performance for student ID card 999999.
```

Nếu baseline không kiểm tra `found`, nó có thể trả lời sai hoặc tạo câu trả lời không rõ ràng.

### Nguyên nhân

Root cause nằm ở việc baseline không có nhiều bước reasoning như agent. Vì vậy mọi logic kiểm tra phải nằm trong function xử lý trực tiếp.

Các điểm cần chú ý:

```text
trích xuất đúng ID card từ query
không trả lời nếu không tìm thấy sinh viên
không tự tạo thông tin sinh viên
trả output đủ rõ để evaluation kiểm tra được
```

### Cách xử lý

Baseline được kiểm tra bằng test và evaluation script:

```bash
.venv/bin/python scripts/run_baseline.py
.venv/bin/python scripts/run_evaluation.py
```

Kết quả hiện tại:

```text
Baseline success: 4/4
```

Điều này cho thấy baseline đủ tốt cho vai trò so sánh, nhưng không thay thế được ReAct trace.

---

## III. Nhận xét cá nhân về Chatbot và ReAct Agent

Điểm em rút ra là baseline chatbot có ưu thế về sự đơn giản. Với bài toán nhỏ, baseline dễ viết, dễ chạy và ít phụ thuộc vào LLM.

Nhưng khi cần giải thích vì sao hệ thống đưa ra kết luận, baseline yếu hơn. Nó chỉ đưa câu trả lời cuối, không cho thấy bước validate sinh viên, bước lấy điểm, hay bước áp dụng policy.

ReAct Agent phù hợp hơn khi bài toán cần minh bạch. Trace của agent giúp người đọc thấy rõ:

```text
validate_student(...)
categorize_academic_performance(...)
Final Answer
```

Trong môi trường học vụ, trace quan trọng vì câu trả lời liên quan đến dữ liệu cá nhân và kết quả học tập.

---

## IV. Hướng cải thiện

Nếu tiếp tục phát triển baseline, em muốn thêm hai cải tiến:

```text
1. Cho baseline trả thêm metadata về các bước đã gọi.
2. Chuẩn hóa output tiếng Việt để dễ so sánh với report.
```

Tuy nhiên không nên biến baseline thành một agent thứ hai. Baseline cần giữ đơn giản để vai trò so sánh rõ ràng.

---

## V. Kết quả kiểm tra phần liên quan

Lệnh kiểm tra:

```bash
.venv/bin/python scripts/run_baseline.py
.venv/bin/python scripts/run_evaluation.py
.venv/bin/python -m pytest -q
```

Kết quả mới nhất:

```text
16 passed
Baseline success: 4/4
Agent success: 4/4
```

Phần của em hoàn thành khi baseline chạy được, evaluation có số liệu so sánh và report nhóm giải thích rõ baseline khác ReAct Agent ở đâu.
