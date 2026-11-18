document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-calculator]");
  if (!form) return;

  const result = document.querySelector("[data-result]");
  const submit = form.querySelector('button[type="submit"]');

  function showMessage(title, message, isError = false) {
    result.replaceChildren();
    result.classList.toggle("result-error", isError);
    const heading = document.createElement("h2");
    heading.textContent = title;
    const detail = document.createElement("p");
    detail.textContent = message;
    result.append(heading, detail);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    submit.textContent = "Calculating…";
    showMessage("Working it out…", "Your result will be ready in a moment.");

    try {
      const response = await fetch(form.dataset.endpoint, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          "X-CSRFToken": form.elements.csrf_token.value,
          "Accept": "application/json",
        },
        body: new URLSearchParams(new FormData(form)),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Please check the values and try again.");

      result.replaceChildren();
      result.classList.remove("result-error");
      if (form.dataset.calculator === "attendance") {
        const heading = document.createElement("h2");
        heading.textContent = "Subject by subject.";
        const list = document.createElement("ul");
        list.className = "result-list";
        data.results.forEach((item) => {
          const row = document.createElement("li");
          row.className = Number(item.attendance_percentage) < 75 ? "attendance-low" : "attendance-good";
          row.setAttribute("aria-label", `${item.subject}: ${item.attendance_percentage} percent, ${item.status}`);
          const label = document.createElement("span");
          label.textContent = item.subject;
          const value = document.createElement("strong");
          value.textContent = `${item.attendance_percentage}%`;
          const status = document.createElement("small");
          status.textContent = item.status;
          row.append(label, value, status);
          list.append(row);
        });
        result.append(heading, list);
      } else {
        const heading = document.createElement("span");
        heading.className = "result-number";
        heading.textContent = Number(data.cgpa).toFixed(2);
        const scale = document.createElement("span");
        scale.className = "result-scale";
        scale.textContent = `out of ${Number(data.scale).toFixed(1)}`;
        const note = document.createElement("p");
        note.textContent = "Credit-weighted estimate";
        result.append(heading, scale, note);
      }
    } catch (error) {
      showMessage("Couldn't calculate that yet.", error.message, true);
    } finally {
      submit.disabled = false;
      submit.innerHTML = 'Calculate <span aria-hidden="true">→</span>';
    }
  });
});
