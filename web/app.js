const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-chat");
const copyButton = document.querySelector("#copy-last-answer");
const exportButton = document.querySelector("#export-chat");
const providerInput = document.querySelector("#provider");
const modelInput = document.querySelector("#model");
const maxStepsInput = document.querySelector("#max-steps");
const localModelPathInput = document.querySelector("#local-model-path");
const quickPrompts = document.querySelectorAll("[data-prompt]");
const healthPill = document.querySelector("#health-pill");
const traceList = document.querySelector("#trace-list");
const traceCount = document.querySelector("#trace-count");
const activeProvider = document.querySelector("#active-provider");
const activeModel = document.querySelector("#active-model");
const activeStatus = document.querySelector("#active-status");
const activeSteps = document.querySelector("#active-steps");
const identityStudentId = document.querySelector("#identity-student-id");
const identityName = document.querySelector("#identity-name");
const identityCard = document.querySelector("#identity-card");
const insertMarksPrompt = document.querySelector("#insert-marks-prompt");
const insertPerformancePrompt = document.querySelector("#insert-performance-prompt");

const identityRequiredPrefix = "Vui lòng cung cấp đủ student_id, name và id_card";
const identityOnlyPattern = /^\s*\d{1,6}\s+[^0-9,;]+?\s+\d{1,6}\s*$/;
const transcript = [];
let pendingStudentQuery = null;
let lastAnswer = "";

const providerDefaults = {
  demo: "demo-academic-provider",
  openai: "gpt-4o",
  gemini: "gemini-1.5-flash",
  local: "Phi-3-mini-4k-instruct-q4.gguf",
};

boot();

providerInput.addEventListener("change", () => {
  modelInput.value = providerDefaults[providerInput.value] || "";
  updateStatus({ provider: providerInput.value, model: modelInput.value });
});

quickPrompts.forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    input.focus();
  });
});

insertMarksPrompt.addEventListener("click", () => {
  insertIdentityPrompt("Cho tôi điểm của");
});

insertPerformancePrompt.addEventListener("click", () => {
  insertIdentityPrompt("Cho tôi học lực của");
});

clearButton.addEventListener("click", () => {
  messages.replaceChildren();
  transcript.length = 0;
  pendingStudentQuery = null;
  lastAnswer = "";
  renderTrace([]);
  updateStatus({ status: "ready", steps: 0 });
  appendMessage("agent", "Đã xóa hội thoại trên màn hình.");
});

copyButton.addEventListener("click", async () => {
  if (!lastAnswer) return;
  await navigator.clipboard.writeText(lastAnswer);
  copyButton.textContent = "Copied";
  setTimeout(() => {
    copyButton.textContent = "Copy";
  }, 1100);
});

exportButton.addEventListener("click", () => {
  const body = transcript
    .map((item) => `[${item.role.toUpperCase()}]\n${item.text}`)
    .join("\n\n");
  const blob = new Blob([body || "No transcript."], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "academic-agent-transcript.txt";
  link.click();
  URL.revokeObjectURL(url);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const typedMessage = input.value.trim();
  if (!typedMessage) return;

  appendMessage("user", typedMessage);
  input.value = "";

  let messageForAgent = typedMessage;
  if (pendingStudentQuery && identityOnlyPattern.test(typedMessage)) {
    messageForAgent = `${pendingStudentQuery} ${typedMessage}`;
    pendingStudentQuery = null;
  }

  setBusy(true);
  updateStatus({ status: "thinking", steps: 0 });
  renderTrace([]);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: messageForAgent,
        provider: providerInput.value,
        model: modelInput.value,
        max_steps: Number(maxStepsInput.value || 5),
        local_model_path: localModelPathInput.value,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Request failed.");
    }

    appendMessage("agent", payload.answer);
    renderTrace(payload.history || []);
    updateStatus({
      provider: payload.provider,
      model: payload.model,
      status: payload.status || "completed",
      steps: payload.steps || 0,
    });

    if (payload.answer.startsWith(identityRequiredPrefix)) {
      pendingStudentQuery = typedMessage;
    } else {
      pendingStudentQuery = null;
    }
  } catch (error) {
    appendMessage("error", error.message || String(error));
    updateStatus({ status: "error" });
  } finally {
    setBusy(false);
    input.focus();
  }
});

async function boot() {
  appendMessage(
    "agent",
    "Academic ReAct Agent sẵn sàng. Hãy cung cấp đủ student_id, name và id_card khi hỏi thông tin sinh viên."
  );
  renderTrace([]);
  updateStatus({
    provider: providerInput.value,
    model: modelInput.value,
    status: "ready",
    steps: 0,
  });

  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("health check failed");
    healthPill.textContent = "online";
    healthPill.classList.remove("neutral");
    healthPill.classList.add("ok");
  } catch {
    healthPill.textContent = "offline";
  }
}

function insertIdentityPrompt(prefix) {
  const studentId = identityStudentId.value.trim();
  const name = identityName.value.trim();
  const idCard = identityCard.value.trim();
  input.value = `${prefix} sinh viên ${name}, mã sinh viên ${studentId}, số CCCD ${idCard}`.trim();
  input.focus();
}

function appendMessage(role, text) {
  const item = document.createElement("article");
  item.className = `message ${role}`;

  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = role === "user" ? "You" : role === "error" ? "Error" : "Agent";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;

  item.append(label, bubble);
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;

  transcript.push({ role, text });
  if (role === "agent") {
    lastAnswer = text;
  }
}

function renderTrace(history) {
  traceList.replaceChildren();
  traceCount.textContent = `${history.length} steps`;

  if (!history.length) {
    const empty = document.createElement("div");
    empty.className = "trace-empty";
    empty.textContent = "Trace sẽ xuất hiện sau khi agent gọi tool hoặc yêu cầu bổ sung danh tính.";
    traceList.append(empty);
    return;
  }

  history.forEach((step) => {
    const item = document.createElement("article");
    item.className = "trace-item";

    const title = document.createElement("h3");
    const stepText = document.createElement("span");
    stepText.textContent = `Step ${step.step}`;
    const status = document.createElement("span");
    status.className = "pill";
    status.textContent = step.status || "trace";
    title.append(stepText, status);

    const response = document.createElement("pre");
    response.textContent = step.llm_response || "(no model response)";

    const observation = document.createElement("pre");
    observation.textContent = step.observation || "(no observation)";

    item.append(title, response, observation);
    traceList.append(item);
  });
}

function updateStatus({ provider, model, status, steps } = {}) {
  if (provider) activeProvider.textContent = provider;
  if (model) activeModel.textContent = model;
  if (status) activeStatus.textContent = status;
  if (steps !== undefined) activeSteps.textContent = String(steps);
}

function setBusy(isBusy) {
  sendButton.disabled = isBusy;
  sendButton.textContent = isBusy ? "Thinking" : "Send";
}
