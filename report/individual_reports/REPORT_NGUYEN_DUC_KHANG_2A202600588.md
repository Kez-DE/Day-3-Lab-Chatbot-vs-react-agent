# Báo cáo cá nhân - Nguyễn Đức Khang

- **Họ tên**: Nguyễn Đức Khang
- **MSSV**: 2A202600588
- **Nhóm**: 24
- **Lab**: Chatbot vs ReAct Agent

---

## 1. Vai trò trong nhóm

Em phụ trách chính phần **ReAct Agent**, bao gồm vòng lặp `Thought -> Action -> Observation -> Final Answer`, tool registry, action parser, guardrail về định danh sinh viên và kiểm thử luồng agent.

Các file liên quan:

```text
src/agent/agent.py
src/demo_provider.py
src/tools/score_tools.py
tests/test_agent.py
scripts/run_demo_agent.py
scripts/chat_agent.py
scripts/run_web_ui.py
```

---

## 2. Công việc đã thực hiện

### 2.1 Hoàn thiện ReAct loop

Agent cần thực hiện được vòng lặp:

```text
Thought -> Action -> Observation -> Final Answer
```

Trong `src/agent/agent.py`, agent xử lý:

1. nhận câu hỏi của user;
2. gửi prompt cho provider;
3. parse `Action: tool_name(args)`;
4. tìm tool trong registry;
5. gọi function Python tương ứng;
6. serialize kết quả thành JSON observation;
7. đưa observation vào prompt kế tiếp;
8. dừng khi có final answer.

Điểm quan trọng là agent không tự bịa điểm. Mỗi câu trả lời về điểm hoặc học lực phải dựa trên observation từ tool.

### 2.2 Tool registry

Agent không hard-code từng function. Các tool được đăng ký qua registry:

```text
validate_student
get_student_marks
calculate_average_score
grade_policy_lookup
categorize_academic_performance
list_courses
get_course_summary
get_low_score_students
compare_courses
```

Cách này giúp agent dễ mở rộng. Khi thêm tool mới, chỉ cần thêm vào registry, không phải viết lại loop.

### 2.3 Guardrail định danh sinh viên

Yêu cầu hiện tại là với thông tin sinh viên, user phải cung cấp đủ:

```text
student_id
name
id_card
```

Em cải thiện parser để chấp nhận nhiều cách nhập:

```text
student_id 30 name Royce Lowe id_card 822067
30 Royce Lowe 822067
38;Jair Ball;505496
Cho tôi điểm của sinh viên Royce Lowe, mã sinh viên 30, số CCCD 822067
```

Nếu thiếu một trong ba trường, agent dừng sớm và yêu cầu bổ sung. Nhờ đó hệ thống không trả điểm khi chưa xác thực đủ danh tính.

### 2.4 Xử lý lỗi parser và max steps

Một lỗi thực tế khi dùng OpenAI/Gemini là model đôi khi trả lời tự nhiên thay vì format:

```text
Action: tool_name(args)
```

Nếu không xử lý, agent sẽ lặp đến `max_steps` và tốn token. Bản hiện tại ghi `PARSER_ERROR` và có nhánh trả lời trực tiếp khi model đang hỏi lại user, tránh vòng lặp vô ích.

---

## 3. Debugging case study

### Vấn đề

Khi user nhập:

```text
điểm của 822067
```

Model có thể cố gọi:

```text
validate_student(student_id=822067, name=None, id_card=None)
```

Lệnh này sai vì thiếu `name` và `id_card`.

### Cách xử lý

Thay vì chỉ nhắc trong prompt, em thêm guard ở code:

```text
Nếu câu hỏi liên quan thông tin sinh viên
và thiếu student_id/name/id_card
thì không gọi LLM/tool
và trả lời yêu cầu bổ sung đủ định danh.
```

Guard này nằm trước vòng gọi provider, nên tiết kiệm token và tránh action sai.

### Case khác

User nhập:

```text
31 Abby Pruitt 432848
```

Trong dataset, Abby Pruitt có `ID=35`. Agent/tool trả mismatch cụ thể:

```text
student_id: provided 31, dataset has 35
```

Kết quả này đúng hơn so với tự sửa thành 35, vì hệ thống học vụ không nên tự đoán danh tính.

---

## 4. Liên hệ với terminal chat và web UI

Terminal chat và web UI đều đi qua `ReActAgent`. Vì vậy các cải tiến trong agent parser và identity guard được dùng lại ở cả hai giao diện.

Ví dụ trên web UI:

```text
Cho tôi điểm của sinh viên Royce Lowe, mã sinh viên 30, số CCCD 822067
```

Agent parse được:

```text
student_id = 30
name = Royce Lowe
id_card = 822067
```

Sau đó mới gọi:

```text
validate_student(30, "Royce Lowe", "822067")
get_student_marks("822067")
```

---

## 5. Kết quả kiểm tra

Các test liên quan:

```text
tests/test_agent.py
tests/test_evaluation.py
```

Những nhóm test chính:

- agent gọi tool và trả final answer;
- unknown tool không crash;
- max steps hoạt động;
- thiếu định danh thì không gọi provider;
- input tiếng Việt có nhãn ở nhiều thứ tự;
- input dạng `ID;Name;ID_Card`;
- mismatch message rõ ràng.

Kết quả hiện tại:

```text
25 passed
```

---

## 6. Nhận xét cá nhân

Phần khó nhất không phải gọi LLM, mà là giữ hợp đồng giữa LLM output và Python tool. Nếu action parser lỏng quá, agent dễ gọi sai tool. Nếu parser chặt quá, trải nghiệm user kém. Bản hiện tại chọn hướng trung gian: yêu cầu đủ định danh để an toàn, nhưng cho phép nhiều cách nhập tự nhiên để dễ dùng.

---

## 7. Hướng cải thiện

1. Thay regex action parser bằng structured tool calling hoặc JSON schema.
2. Tách identity parser thành module riêng để test độc lập hơn.
3. Thêm lịch sử hội thoại nhiều lượt trong web UI thay vì chỉ một lượt bổ sung định danh.
4. Chuẩn hóa final answer tiếng Việt cho cả demo provider và provider thật.
5. Thêm test cho các câu hỏi course-level.
