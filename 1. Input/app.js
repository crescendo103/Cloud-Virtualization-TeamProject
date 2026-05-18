const form = document.querySelector("#job-form");
const result = document.querySelector("#result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  result.textContent = "작업을 제출하는 중입니다...";

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      body: new FormData(form),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "작업 제출에 실패했습니다.");
    }

    result.textContent = `작업이 큐에 등록되었습니다.\n\nJob ID: ${payload.job_id}\nStatus: ${payload.status}`;
    window.setTimeout(() => {
      window.location.href = `/dashboard/?job=${encodeURIComponent(payload.job_id)}`;
    }, 700);
  } catch (error) {
    result.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
