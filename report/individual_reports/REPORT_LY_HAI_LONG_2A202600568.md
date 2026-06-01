# Báo cáo cá nhân - Lý Hải Long

- **Họ tên**: Lý Hải Long
- **MSSV**: 2A202600568
- **Nhóm**: 24
- **Lab**: Chatbot vs ReAct Agent

---

## I. Phần việc phụ trách

Trong phần chia việc của nhóm, em phụ trách chính phần **Tạo data, logging, demo offline, test và tài liệu chạy thử, làm UI**. Mục tiêu là để người chấm có thể chạy lại hệ thống mà không cần API key và vẫn thấy được trace của agent.

Các file liên quan:

```text
src/demo_provider.py
src/telemetry/logger.py
src/telemetry/metrics.py
scripts/run_demo_agent.py
scripts/run_evaluation.py
tests/test_agent.py
tests/test_chatbot.py
tests/test_evaluation.py
README.md
```

### 1. Demo provider để chạy offline

Repo có provider cho OpenAI và Gemini, nhưng khi demo lab, API key có thể hết hạn, sai cấu hình hoặc không có mạng. Vì vậy nhóm dùng thêm `DemoAcademicProvider`.

Provider này không gọi API thật. Nó sinh output theo format ReAct:

```text
Thought: ...
Action: validate_student(...)
```

Sau khi agent nhận Observation, provider tiếp tục sinh action kế tiếp hoặc final answer.

Lợi ích chính:

```text
kết quả chạy ổn định
không tốn API cost
không phụ thuộc credential
phù hợp chấm bài offline
```

Điểm quan trọng là demo provider không bỏ qua ReAct loop. Agent vẫn parse action, gọi tool và nhận observation như khi dùng LLM provider thật.

### 2. Logging và telemetry

Phần logging giúp theo dõi agent chạy qua những bước nào. Các event chính:

```text
AGENT_START
LLM_METRIC
LLM_RESPONSE
TOOL_CALL
FINAL_ANSWER
AGENT_END
```

Ví dụ trong demo:

```text
LLM_RESPONSE -> Action: validate_student(30, 'Royce Lowe', '822067')
TOOL_CALL -> found = true
LLM_RESPONSE -> Action: categorize_academic_performance(822067)
TOOL_CALL -> average_score = 8.39, category = Giỏi
FINAL_ANSWER -> Royce Lowe ... category: Giỏi
```

Nhờ log này, nhóm có thể giải thích agent đã làm gì thay vì chỉ đưa câu trả lời cuối.

### 3. Script chạy thử

Các script chính:

```text
scripts/run_baseline.py
scripts/run_demo_agent.py
scripts/run_evaluation.py
```

Luồng demo đề xuất:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_baseline.py
.venv/bin/python scripts/run_demo_agent.py
.venv/bin/python scripts/run_evaluation.py
```

Lệnh này cho thấy đủ ba phần:

```text
test suite
baseline answer
ReAct trace
evaluation summary
```

### 4. Test và tài liệu chạy lại

Em hỗ trợ phần test để đảm bảo demo không chỉ chạy một case thủ công.

Các nhóm test chính:

```text
tests/test_agent.py
tests/test_chatbot.py
tests/test_evaluation.py
```

README cũng ghi lại cách chạy test, baseline, ReAct demo và evaluation để người khác reproduce kết quả.

---

## II. Debugging case study

### Vấn đề gặp phải

Demo bằng API thật không ổn định nếu key không hợp lệ. Khi kiểm tra, OpenAI key có thể rỗng hoặc Gemini key có thể invalid. Nếu phụ thuộc hoàn toàn vào API thật, buổi demo có thể fail dù code ReAct và tool vẫn đúng.

### Nguyên nhân

Root cause không nằm ở ReAct loop, mà nằm ở external dependency:

```text
API key
network
model availability
provider quota
package version
```

Đây là loại lỗi không nên làm hỏng phần chấm core logic của lab.

### Cách xử lý

Nhóm tách demo thành hai hướng:

```text
1. Offline demo: dùng DemoAcademicProvider, luôn chạy được.
2. API path: giữ OpenAIProvider/GeminiProvider cho trường hợp có key hợp lệ.
```

Trong README và report, nhóm ghi rõ bản demo chính dùng deterministic provider. Cách này trung thực hơn so với nói rằng API thật đã chạy nếu credential chưa hợp lệ.

---

## III. Nhận xét cá nhân về Chatbot và ReAct Agent

Điểm em học được là demo agent không chỉ cần code đúng. Demo còn cần reproducible. Nếu hệ thống chỉ chạy khi API key đúng, mạng ổn và quota còn, người chấm khó kiểm tra lại.

Với ReAct Agent, log và script chạy thử rất quan trọng. Trace giúp chứng minh agent thật sự gọi tool, còn evaluation giúp chứng minh agent không chỉ pass một ví dụ đẹp.

Baseline chatbot dễ demo hơn vì output ngắn. ReAct Agent cần nhiều log hơn, nhưng log đó lại là bằng chứng cho quá trình suy luận.

---

## IV. Hướng cải thiện

Nếu phát triển tiếp, em muốn thêm một script API chính thức:

```text
scripts/run_api_agent.py
```

Script này có thể đọc `.env` và chọn provider:

```text
DEFAULT_PROVIDER=openai | gemini | demo
DEFAULT_MODEL=...
```

Ngoài ra nên chuẩn hóa final answer tiếng Việt để khi demo trước lớp, output dễ đọc hơn.

---

## V. Kết quả kiểm tra phần liên quan

Các lệnh kiểm tra:

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

Phần của em hoàn thành khi người khác có thể clone repo, chạy lệnh demo và thấy được trace/evaluation mà không cần API key.
