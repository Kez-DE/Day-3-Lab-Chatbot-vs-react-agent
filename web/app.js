const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-chat");
const providerInput = document.querySelector("#provider");
const modelInput = document.querySelector("#model");
const maxStepsInput = document.querySelector("#max-steps");
const localModelPathInput = document.querySelector("#local-model-path");
const quickPrompts = document.querySelectorAll("[data-prompt]");

const identityRequiredPrefix = "Vui lòng cung cấp đủ student_id, name và id_card";
const identityOnlyPattern = /^\s*\d{1,6}\s+[^0-9,;]+?\s+\d{1,6}\s*$/;
let pendingStudentQuery = null;

const providerDefaults = {
  demo: "demo-academic-provider",
  openai: "gpt-4o",
  gemini: "gemini-1.5-flash",
  local: "Phi-3-mini-4k-instruct-q4.gguf",
};

appendMessage(
  "agent",
  "Nhập câu hỏi về điểm hoặc học lực. Với thông tin sinh viên, hãy cung cấp đủ student_id, name và id_card."
);

providerInput.addEventListener("change", () => {
  modelInput.value = providerDefaults[providerInput.value] || "";
});

quickPrompts.forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    input.focus();
  });
});

clearButton.addEventListener("click", () => {
  messages.replaceChildren();
  pendingStudentQuery = null;
  appendMessage("agent", "Đã xóa hội thoại trên màn hình.");
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
    if (payload.answer.startsWith(identityRequiredPrefix)) {
      pendingStudentQuery = typedMessage;
    } else {
      pendingStudentQuery = null;
    }
  } catch (error) {
    appendMessage("error", error.message || String(error));
  } finally {
    setBusy(false);
    input.focus();
  }
});

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
}

function setBusy(isBusy) {
  sendButton.disabled = isBusy;
  sendButton.textContent = isBusy ? "Thinking" : "Send";
}
