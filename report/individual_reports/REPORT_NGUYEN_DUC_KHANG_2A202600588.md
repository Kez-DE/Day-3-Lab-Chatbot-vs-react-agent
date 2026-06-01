# Báo cáo cá nhân - Nguyễn Đức Khang

- **Họ tên**: Nguyễn Đức Khang
- **MSSV**: 2A202600588
- **Nhóm**: F2
- **Lab**: Chatbot vs ReAct Agent

---

## I. Phần việc phụ trách

Trong phần báo cáo cá nhân này, em không nhận toàn bộ công việc của nhóm. Phần đóng góp của em tập trung vào **luồng ReAct Agent**, tích hợp tool registry và kiểm tra cuối để hệ thống chạy được từ đầu đến cuối.

Các file liên quan trực tiếp:

```text
src/agent/agent.py
src/tools/score_tools.py
src/demo_provider.py
scripts/run_demo_agent.py
tests/test_agent.py
evaluation/results.json
evaluation/summary.md
```

### 1. Hoàn thiện ReAct loop

Em phụ trách phần agent chạy theo format:

```text
Thought -> Action -> Observation -> Final Answer
```

Trong `src/agent/agent.py`, agent cần làm được các bước sau:

```text
1. Nhận câu hỏi từ user.
2. Gửi prompt cho LLM provider.
3. Parse Action từ output của model.
4. Gọi đúng tool trong registry.
5. Đưa Observation quay lại prompt.
6. Dừng khi model trả Final Answer.
```

Điểm quan trọng của phần này là agent không được trả lời trực tiếp bằng phỏng đoán. Mỗi kết luận về điểm, average score hoặc học lực phải đi qua tool.

### 2. Tích hợp tool registry vào agent

Agent không gọi function Python trực tiếp theo tên hardcode. Thay vào đó, các tool được đăng ký trong registry:

```text
validate_student(student_id, name, id_card)
categorize_academic_performance(identifier)
get_student_marks(identifier)
calculate_average_score(identifier)
grade_policy_lookup()
```

Cách này giúp agent dễ mở rộng. Nếu nhóm thêm tool mới như `get_course_summary()` hoặc `compare_courses()`, agent vẫn dùng cùng cơ chế `Action: tool_name(args)`.

### 3. Cập nhật validation đủ 3 trường

Ban đầu nhóm dùng ý tưởng:

```python
validate_student(identifier)
```

Sau khi xem lại yêu cầu, cách này chưa đủ chặt. Em tham gia chỉnh luồng để `validate_student` cần đủ 3 giá trị:

```python
validate_student(student_id, name, id_card)
```

Ví dụ case Royce Lowe:

```python
validate_student(30, "Royce Lowe", "822067")
```

Việc này làm trace rõ hơn. Nếu chỉ có ID card, hệ thống có thể tìm ra điểm, nhưng bước xác thực danh tính chưa đủ chắc. Với 3 trường, tool chỉ pass khi internal ID, họ tên và ID card cùng khớp một record.

### 4. Kiểm tra luồng demo agent

Em phụ trách kiểm tra lệnh demo:

```bash
.venv/bin/python scripts/run_demo_agent.py
```

Output chính cần có:

```text
Action: validate_student(30, 'Royce Lowe', '822067')
Observation: found = true
Action: categorize_academic_performance(822067)
Final Answer: Royce Lowe ... Academic category: Giỏi
```

Demo này dùng `DemoAcademicProvider` để chạy ổn định, không phụ thuộc API key. Repo vẫn có `OpenAIProvider` và `GeminiProvider`, nhưng bản demo nộp ưu tiên reproducible result.

---

## II. Debugging case study

### Vấn đề gặp phải

Sau khi đổi `validate_student` từ một tham số sang ba tham số, các phần liên quan bị lệch contract. Nếu chỉ sửa function body mà không sửa agent trace, demo provider và test, agent sẽ gọi sai dạng:

```text
Action: validate_student(822067)
```

Trong khi tool mới yêu cầu:

```text
Action: validate_student(30, "Royce Lowe", "822067")
```

### Nguyên nhân

Đây không phải lỗi cú pháp đơn thuần. Root cause là **API contract thay đổi** nhưng chưa cập nhật toàn bộ bề mặt sử dụng.

Các nơi bị ảnh hưởng:

```text
src/tools/score_tools.py
tests/test_score_tools.py
tests/test_agent.py
src/demo_provider.py
README.md
report/group_report/GROUP_REPORT_NHOM_F2.md
report/individual_reports/*.md
```

### Cách xử lý

Em kiểm tra theo hướng contract-first:

```text
1. Xác định chữ ký mới của tool.
2. Sửa test để bắt buộc đủ 3 tham số.
3. Sửa demo provider để sinh Action đúng.
4. Sửa trace trong report và README.
5. Chạy lại test suite.
```

Kết quả kiểm tra:

```text
16 passed
```

Case này giúp em hiểu rằng khi đổi interface của một tool trong agent system, không chỉ code tool bị ảnh hưởng. Prompt, trace, test và documentation cũng là một phần của contract.

---

## III. Nhận xét cá nhân về Chatbot và ReAct Agent

Baseline chatbot trả lời nhanh hơn vì nó gọi function trực tiếp. Với query đơn giản như `822067`, baseline có thể trả về học lực ngay.

Điểm yếu của baseline là thiếu trace. Nếu kết quả sai, khó biết lỗi nằm ở bước parse query, lấy điểm, tính average hay phân loại học lực.

ReAct Agent chậm hơn vì phải đi qua nhiều bước:

```text
Thought
Action
Observation
Thought
Action
Observation
Final Answer
```

Nhưng bù lại, ReAct Agent dễ kiểm tra hơn. Trong lab này, trace cho thấy rõ agent đã validate sinh viên trước rồi mới phân loại học lực. Đây là điểm quan trọng nếu hệ thống dùng cho dữ liệu học vụ.

Bài học chính của em là: agent không nên được đánh giá chỉ bằng câu trả lời cuối. Với bài toán có dữ liệu thật, cần xem cả đường đi từ câu hỏi đến kết luận.

---

## IV. Hướng cải thiện

Nếu phát triển tiếp, phần em muốn cải thiện là cho user chỉ nhập ID card nhưng hệ thống vẫn validate đủ 3 trường bằng một bước lookup trung gian:

```text
lookup_student_by_id_card(id_card)
-> validate_student(student_id, name, id_card)
-> categorize_academic_performance(id_card)
```

Hiện demo provider đang chuẩn bị sẵn mapping cho vài case benchmark. Nếu chuyển sang API thật, nên thêm tool lookup để LLM không phải tự đoán tên hoặc internal ID.

Một cải tiến khác là chuẩn hóa output tiếng Việt cho final answer. Hiện agent answer vẫn dùng tiếng Anh trong một số script vì demo provider trả câu trả lời theo template English. Khi demo trước lớp, output tiếng Việt sẽ dễ theo dõi hơn.

---

## V. Kết quả kiểm tra phần liên quan

Các lệnh đã dùng để xác nhận phần agent chạy đúng:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_demo_agent.py
.venv/bin/python scripts/run_evaluation.py
```

Kết quả mới nhất:

```text
16 passed
Baseline success: 4/4
Agent success: 4/4
```

Phần của em hoàn thành khi agent chạy được trace đầy đủ, tool được gọi đúng chữ ký mới và evaluation vẫn pass sau khi đổi validation contract.
