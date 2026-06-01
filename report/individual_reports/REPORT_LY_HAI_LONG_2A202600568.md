# Báo cáo cá nhân - Lý Hải Long

- **Họ tên**: Lý Hải Long
- **MSSV**: 2A202600568
- **Nhóm**: 24
- **Lab**: Chatbot vs ReAct Agent

---

## 1. Vai trò trong nhóm

Em phụ trách chính phần **demo offline, logging/telemetry, terminal chat, web UI và tài liệu chạy thử**. Mục tiêu là biến phần agent/tool thành một hệ thống có thể thao tác được, không chỉ là code chạy trong test.

Các file liên quan:

```text
src/demo_provider.py
src/telemetry/logger.py
src/telemetry/metrics.py
scripts/chat_agent.py
scripts/run_web_ui.py
web/index.html
web/styles.css
web/app.js
README.md
```

---

## 2. Công việc đã thực hiện

### 2.1 Demo provider offline

`DemoAcademicProvider` giúp hệ thống chạy ổn định khi không có API key. Provider này vẫn sinh output theo format ReAct:

```text
Thought: ...
Action: validate_student(...)
```

Điểm quan trọng là demo provider không bỏ qua agent loop. Agent vẫn phải parse action, gọi tool và nhận observation. Vì vậy demo offline vẫn kiểm tra được luồng ReAct thật.

### 2.2 Logging và telemetry

Hệ thống ghi log JSON vào:

```text
logs/YYYY-MM-DD.log
```

Các event chính:

```text
AGENT_START
IDENTITY_REQUIRED
LLM_METRIC
LLM_RESPONSE
TOOL_CALL
PARSER_ERROR
FINAL_ANSWER
AGENT_END
```

Log giúp nhóm debug nhanh khi:

- provider trả sai format;
- agent gọi sai tool;
- thiếu danh tính sinh viên;
- tool trả mismatch;
- agent vượt max steps.

### 2.3 Terminal chat

Script:

```text
scripts/chat_agent.py
```

Chạy:

```bash
.venv/bin/python scripts/chat_agent.py --provider demo
```

Terminal chat hỗ trợ:

- chọn provider;
- nhập nhiều lượt;
- ẩn log JSON khỏi console để chat dễ đọc;
- `--show-logs` khi cần debug;
- nhớ câu hỏi trước một lượt nếu user cần bổ sung danh tính.

Ví dụ:

```text
You> đưa ra điểm
Agent> Vui lòng cung cấp đủ student_id, name và id_card...
You> 10 Axl Waters 876012
Agent> Axl Waters ... has these marks ...
```

### 2.4 Web UI

Repo hiện có web UI local:

```text
scripts/run_web_ui.py
web/index.html
web/styles.css
web/app.js
```

Chạy:

```bash
.venv/bin/python scripts/run_web_ui.py
```

Mở:

```text
http://127.0.0.1:8000
```

Web UI hỗ trợ:

- chọn provider: demo, OpenAI, Gemini, local;
- nhập model;
- nhập max steps;
- nhập local model path;
- quick prompts;
- gọi API `/api/chat`;
- health check `/api/health`;
- tự chuyển port nếu `8000` đang bận.

### 2.5 Tài liệu chạy thử

README được cập nhật để người khác có thể chạy:

```text
test
baseline
demo agent
terminal chat
web UI
evaluation
```

Tài liệu này quan trọng vì lab không chỉ cần code đúng, mà cần người chấm chạy lại được.

---

## 3. Debugging case study

### Vấn đề 1: Port 8000 bị chiếm

Khi web server đang chạy, chạy thêm lần nữa sẽ lỗi:

```text
OSError: Address already in use
```

### Cách xử lý

`scripts/run_web_ui.py` được cập nhật để thử các port tiếp theo:

```text
8000 -> 8001 -> 8002 -> ...
```

Server in URL thực tế để user mở đúng trang.

### Vấn đề 2: Log JSON làm rối terminal chat

Agent logger mặc định ghi cả console và file. Khi chat terminal, JSON log chen vào giữa câu trả lời.

### Cách xử lý

CLI mặc định tắt console log, nhưng vẫn ghi log file. Khi cần debug có thể chạy:

```bash
.venv/bin/python scripts/chat_agent.py --provider demo --show-logs
```

---

## 4. Liên hệ với dataset và agent

Web UI không tự tính điểm. Nó chỉ là giao diện gửi request đến API local:

```text
Browser -> /api/chat -> ReActAgent -> score tools -> Data/database.csv
```

Vì vậy web UI dùng lại toàn bộ logic validation, parser và tool hiện có. Cách này tránh việc terminal và web trả kết quả khác nhau.

---

## 5. Kết quả kiểm tra

Các phần liên quan được kiểm tra bằng:

```text
tests/test_agent.py
manual API check /api/health
manual API check /api/chat
```

Kết quả hiện tại:

```text
25 passed
```

Ví dụ API đã kiểm tra:

```text
POST /api/chat
message: điểm của 38;Jair Ball;505496
```

Kết quả trả đúng điểm của Jair Ball.

---

## 6. Nhận xét cá nhân

Phần giao diện làm rõ một vấn đề: agent tốt nhưng nếu chỉ chạy bằng script cứng thì khó dùng. Terminal chat giúp test nhanh; web UI giúp người chấm thao tác trực quan hơn. Tuy nhiên UI không nên chứa logic nghiệp vụ. Logic vẫn phải nằm ở agent và tool để dễ test.

---

## 7. Hướng cải thiện

1. Hiển thị trace `Thought/Action/Observation` trong web UI bằng panel riêng.
2. Thêm nút tải log hiện tại.
3. Thêm bảng xem dataset mẫu trong web UI.
4. Thêm endpoint `/api/evaluation` để chạy benchmark từ web.
5. Tách server web sang FastAPI nếu cần deploy.
