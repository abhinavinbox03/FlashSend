const form = document.getElementById("send-form");
const emailInput = document.getElementById("email");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");

function showStatus(message, type) {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.hidden = false;
}

function clearStatus() {
  statusEl.hidden = true;
  statusEl.textContent = "";
  statusEl.className = "status";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearStatus();

  const email = emailInput.value.trim();
  if (!email) {
    showStatus("Please enter an email address.", "error");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Sending...";

  try {
    const response = await fetch(`${API_BASE_URL}/api/send-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const detail = data.detail || "Something went wrong. Please try again.";
      const message = typeof detail === "string" ? detail : JSON.stringify(detail);
      showStatus(message, "error");
      return;
    }

    showStatus(data.message || "Email sent successfully.", "success");
    form.reset();
  } catch {
    showStatus("Could not reach the server. Is the backend running?", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Send Email";
  }
});
