# Báo cáo cá nhân - Nguyễn Đức Mạnh

- **Họ tên**: Nguyễn Đức Mạnh
- **MSSV**: 2A202600945
- **Nhóm**: 24
- **Lab**: Chatbot vs ReAct Agent

---

## 1. Vai trò trong nhóm

Em phụ trách chính phần **dataset, score tools và policy học lực**. Đây là lớp nền của toàn bộ hệ thống. Nếu phần đọc dữ liệu hoặc tính điểm sai, cả baseline chatbot, ReAct Agent, terminal chat và web UI đều sẽ trả kết quả sai.

Các file liên quan:

```text
Data/database.csv
src/tools/score_tools.py
tests/test_score_tools.py
report/group_report/GROUP_REPORT_NHOM_24.md
```

---

## 2. Công việc đã thực hiện

### 2.1 Chuẩn hóa dataset

Dataset nằm tại:

```text
Data/database.csv
```

Dữ liệu có 100 sinh viên, mỗi dòng gồm:

```text
ID
Name
ID_Card
Computer Science
Microeconomics
Data Structures and Algorithms
Calculus
Linear Algebra
```

Điểm trong CSV dùng dấu phẩy làm phần thập phân:

```text
9,30
8,59
3,16
```

Em xử lý phần này để tool chuyển về float:

```text
9,30 -> 9.30
8,59 -> 8.59
3,16 -> 3.16
```

Nếu không chuẩn hóa bước này, các hàm tính average score sẽ lỗi hoặc sai dữ liệu.

### 2.2 Thiết kế score tools

Các tool chính:

```text
validate_student(student_id, name, id_card)
get_student_marks(identifier)
calculate_average_score(identifier)
grade_policy_lookup()
categorize_academic_performance(identifier)
```

Thiết kế này tách rõ trách nhiệm:

- `validate_student`: xác thực danh tính.
- `get_student_marks`: lấy điểm từng môn.
- `calculate_average_score`: tính trung bình và môn trượt.
- `grade_policy_lookup`: trả policy học lực.
- `categorize_academic_performance`: tổng hợp kết quả cuối.

Cách tách tool giúp ReAct Agent không phải tự tính từ text. Agent chỉ chọn tool, còn tính toán do Python thực hiện deterministic.

### 2.3 Áp dụng policy học lực

Policy hiện tại:

```text
Xuất sắc: average_score >= 9.0
Giỏi: 8.0 <= average_score < 9.0
Khá: 6.5 <= average_score < 8.0
Trung bình: 5.0 <= average_score < 6.5
Yếu: average_score < 5.0
```

Điều kiện qua môn:

```text
score >= 4.0
```

Điều kiện bổ sung:

```text
Muốn được xếp loại Khá trở lên, sinh viên phải qua tất cả các môn.
```

Vì vậy tool cần trả thêm:

```text
failed_courses
passed_all_courses
base_category
category
```

### 2.4 Tool phân tích lớp

Ngoài tool theo sinh viên, em cũng hỗ trợ các tool theo lớp:

```text
list_courses()
get_course_summary(course_name)
get_low_score_students(course_name, threshold)
compare_courses()
```

Các tool này giúp repo có khả năng mở rộng ngoài câu hỏi “điểm của một sinh viên”, ví dụ hỏi môn nào có pass rate thấp hoặc danh sách sinh viên dưới một ngưỡng điểm.

---

## 3. Case kiểm thử tiêu biểu

### Royce Lowe

```text
ID: 30
ID_Card: 822067
Average: 8.39
Category: Giỏi
Failed courses: none
```

### Axl Waters

```text
ID: 10
ID_Card: 876012
Average: 6.31
Failed course: Data Structures and Algorithms (3.16)
Category: Trung bình
```

Case Axl Waters quan trọng vì nó kiểm tra hệ thống không được chỉ nhìn average score. Môn dưới 4.0 phải được ghi nhận trong `failed_courses`.

---

## 4. Debugging case study

### Vấn đề

CSV dùng định dạng số có dấu phẩy:

```text
9,30
```

Trong Python:

```python
float("9,30")
```

sẽ lỗi.

### Cách xử lý

Trước khi ép kiểu, tool chuẩn hóa:

```text
value.strip().replace(",", ".")
```

Sau khi sửa, test xác nhận:

```text
Computer Science của Royce Lowe = 9.30
Linear Algebra của Royce Lowe = 9.85
```

---

## 5. Liên hệ với web UI và agent

Web UI và terminal chat đều gọi agent. Agent lại gọi score tools. Vì vậy phần của em là tầng backend dữ liệu cho cả hai giao diện.

Ví dụ user nhập trong web:

```text
điểm của 38;Jair Ball;505496
```

Luồng xử lý:

```text
Web UI -> /api/chat -> ReAct Agent -> validate_student -> get_student_marks -> Final Answer
```

Nếu `score_tools.py` sai, web UI vẫn hiển thị đẹp nhưng kết quả sai. Vì vậy test cho tool là điều kiện nền trước khi kiểm thử giao diện.

---

## 6. Kết quả kiểm tra

Các test liên quan:

```text
tests/test_score_tools.py
tests/test_agent.py
```

Kết quả hiện tại của toàn repo:

```text
25 passed
```

---

## 7. Nhận xét cá nhân

Qua phần này, em thấy trong hệ thống dùng LLM, phần tính toán nên để tool deterministic xử lý. LLM phù hợp để hiểu yêu cầu và chọn bước tiếp theo, nhưng không nên tự tính điểm hoặc tự phân loại học lực từ text. Việc tách dataset, parser và policy ra thành tool riêng giúp hệ thống dễ kiểm thử, dễ debug và đáng tin hơn.

---

## 8. Hướng cải thiện

Nếu tiếp tục phát triển, phần dataset/tool nên cải thiện:

1. Thêm schema validation cho CSV trước khi chạy agent.
2. Kiểm tra duplicate `ID` hoặc `ID_Card`.
3. Thêm semester/status để hỗ trợ nhiều kỳ học.
4. Thêm export kết quả ra CSV/JSON từ web UI.
5. Thêm test cho các course-level tools với nhiều threshold khác nhau.
