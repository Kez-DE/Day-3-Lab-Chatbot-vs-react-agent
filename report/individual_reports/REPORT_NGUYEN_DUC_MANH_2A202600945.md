# Báo cáo cá nhân - Nguyễn Đức Mạnh

- **Họ tên**: Nguyễn Đức Mạnh
- **MSSV**: 2A202600945
- **Nhóm**: 24
- **Lab**: Chatbot vs ReAct Agent

---

## I. Phần việc phụ trách

Trong phần chia việc của nhóm, em phụ trách chính phần **xử lý dữ liệu điểm và thiết kế score tools**. Đây là lớp nền để baseline chatbot và ReAct Agent có thể trả lời bằng dữ liệu thật từ file CSV, thay vì tự sinh câu trả lời.

Các file liên quan:

```text
Data/database.csv
src/tools/score_tools.py
tests/test_score_tools.py
report/group_report/GROUP_REPORT_NHOM_24.md
```

### 1. Đọc và chuẩn hóa dữ liệu điểm

Dataset của lab nằm trong:

```text
Data/database.csv
```

Các cột chính:

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

Một điểm cần xử lý là điểm trong CSV dùng dấu phẩy cho số thập phân:

```text
9,30
8,59
3,16
```

Nếu đưa trực tiếp vào `float()`, Python sẽ lỗi. Vì vậy phần tool cần chuyển:

```text
9,30 -> 9.30
8,59 -> 8.59
3,16 -> 3.16
```

Sau bước này, hệ thống mới tính được average score chính xác.

### 2. Thiết kế score tools

Các tool chính trong `src/tools/score_tools.py`:

```text
validate_student(student_id, name, id_card)
get_student_marks(identifier)
calculate_average_score(identifier)
grade_policy_lookup()
categorize_academic_performance(identifier)
```

Các tool này được tách nhỏ để agent gọi từng bước rõ ràng. Ví dụ, thay vì tạo một tool chung kiểu `query_database(question)`, nhóm dùng tool có input/output cụ thể.

Cách tách này giúp giảm hallucination. Agent không cần tự hiểu toàn bộ CSV. Nó chỉ cần chọn đúng tool và dùng kết quả trả về.

### 3. Áp dụng policy phân loại học lực

Policy trong lab dùng thang điểm 10:

```text
Xuất sắc: average_score >= 9.0
Giỏi: 8.0 <= average_score < 9.0
Khá: 6.5 <= average_score < 8.0
Trung bình: 5.0 <= average_score < 6.5
Yếu: average_score < 5.0
```

Ngoài average score, tool còn kiểm tra môn trượt:

```text
course score < 4.0
```

Case Axl Waters là ví dụ quan trọng:

```text
ID card: 876012
Average score: 6.31
Failed course: Data Structures and Algorithms (3.16)
Category: Trung bình
```

Nếu chỉ nhìn average, có thể kết luận thiếu thông tin. Vì vậy output tool phải trả cả `failed_courses` và `passed_all_courses`.

### 4. Tool mở rộng cho phân tích lớp

Ngoài student-level tools, nhóm còn có tool mở rộng:

```text
list_courses()
get_course_summary(course_name)
get_low_score_students(course_name, threshold)
compare_courses()
```

Các tool này giúp report có thể phân tích thêm theo môn học nếu cần. Trong bản evaluation chính, nhóm tập trung vào student-level evaluation để đúng phạm vi lab.

---

## II. Debugging case study

### Vấn đề gặp phải

Lỗi dễ gặp nhất là parse điểm sai do CSV dùng dấu phẩy. Nếu không chuẩn hóa, các phép tính average sẽ không chạy hoặc trả kết quả sai.

Ví dụ dữ liệu:

```text
Computer Science = 9,30
Microeconomics = 8,59
```

Python cần dữ liệu dạng:

```text
9.30
8.59
```

### Nguyên nhân

Root cause là format dữ liệu trong CSV không giống format số mặc định của Python. Đây là lỗi thường gặp trong data engineering: dữ liệu nhìn đúng với người đọc, nhưng chưa đúng với parser.

### Cách xử lý

Tool xử lý score cần làm sạch dữ liệu trước khi tính toán:

```text
replace comma decimal
convert to float
skip non-score columns
round average score
return structured dict
```

Sau khi xử lý, test được viết để kiểm tra case Royce Lowe:

```text
Average score: 8.39
Category: Giỏi
```

Kết quả test hiện tại:

```text
16 passed
```

---

## III. Nhận xét cá nhân về Chatbot và ReAct Agent

Từ góc nhìn data, agent chỉ tốt khi tool trả dữ liệu đúng. Nếu tool parse sai điểm hoặc policy sai, ReAct trace vẫn có vẻ hợp lý nhưng kết luận cuối vẫn sai.

Vì vậy phần quan trọng nhất không phải chỉ là prompt. Với bài toán này, lớp tool mới là nơi đảm bảo correctness.

ReAct Agent có lợi thế là nó để lộ quá trình dùng tool. Khi thấy trace:

```text
Action: categorize_academic_performance(876012)
Observation: failed_courses = Data Structures and Algorithms (3.16)
```

người đọc biết kết luận “Trung bình” không phải do model tự đoán. Nó đến từ dữ liệu và policy.

---

## IV. Hướng cải thiện

Nếu phát triển tiếp, em muốn thêm kiểm tra dữ liệu đầu vào:

```text
phát hiện score bị thiếu
phát hiện score ngoài khoảng 0-10
phát hiện duplicate ID_Card
phát hiện tên trùng nhưng ID khác nhau
```

Các kiểm tra này phù hợp với hướng data engineering hơn. Trước khi agent chạy, pipeline nên validate dataset để tránh lỗi lan sang phần trả lời.

---

## V. Kết quả kiểm tra phần liên quan

Các lệnh kiểm tra:

```bash
.venv/bin/python -m pytest tests/test_score_tools.py -q
.venv/bin/python -m pytest -q
```

Kết quả mới nhất:

```text
16 passed
```

Phần của em hoàn thành khi score tools đọc đúng CSV, tính đúng average score, trả đúng category và xử lý được case môn trượt.
