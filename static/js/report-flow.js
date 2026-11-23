(() => {
  const form = document.getElementById("report-form");
  if (!form) return;

  const steps = [...form.querySelectorAll(".report-step")];
  const labels = [...form.querySelectorAll("[data-step-label]")];
  const controls = document.getElementById("report-controls");
  const back = document.getElementById("report-back");
  const next = document.getElementById("report-next");
  const photoInput = document.getElementById("id_photo");
  const preview = document.getElementById("photo-preview");
  const photoError = document.getElementById("photo-error");
  const review = document.getElementById("report-review");
  const submit = document.getElementById("report-submit");
  const submitStatus = document.getElementById("report-submit-status");
  let current = 0;
  let submitting = false;
  const maxBytes = Number(form.dataset.maxFileBytes) || 8 * 1024 * 1024;

  // Keep the plain HTML form usable; JavaScript only enhances it into guided steps.
  controls.hidden = false;
  function showStep(index, focus = true) {
    current = Math.max(0, Math.min(index, steps.length - 1));
    steps.forEach((step, i) => { step.hidden = i !== current; });
    labels.forEach((label, i) => {
      label.setAttribute("aria-current", i === current ? "step" : "false");
    });
    back.hidden = current === 0;
    next.hidden = current === steps.length - 1;
    submit.hidden = current !== steps.length - 1;
    window.dispatchEvent(new CustomEvent("report-step-shown", { detail: { step: current } }));
    if (current === steps.length - 1) updateReview();
    if (focus) steps[current].querySelector("h2")?.focus();
  }

  function firstInvalid(step) {
    return [...steps[step].querySelectorAll("input, select, textarea")].find((field) => !field.checkValidity());
  }

  function updateReview() {
    const category = document.getElementById("id_category");
    const selectedCategory = category?.selectedOptions[0]?.textContent.trim() || "Not selected";
    const files = [...(photoInput?.files || [])].map((file) => file.name);
    const lat = document.getElementById("id_latitude")?.value || "Not selected";
    const lon = document.getElementById("id_longitude")?.value || "Not selected";
    const description = document.getElementById("id_description")?.value.trim() || "No description";
    const landmark = document.getElementById("id_landmark")?.value.trim();
    review.replaceChildren();
    [
      `Category: ${selectedCategory}`,
      `Photos: ${files.length ? files.join(", ") : "None selected"}`,
      `Coordinates: ${lat}, ${lon}`,
      `Description: ${description}`,
      `Nearby landmark: ${landmark || "Not provided"}`,
      `Privacy consent: ${document.getElementById("id_consent")?.checked ? "Confirmed" : "Not confirmed"}`,
      `Location pin: ${document.getElementById("id_pin_confirmed")?.checked ? "Confirmed" : "Not confirmed"}`,
    ].forEach((line) => {
      const item = document.createElement("p");
      item.textContent = line;
      review.append(item);
    });
  }

  function validatePhotos() {
    const oversized = [...(photoInput?.files || [])].find((file) => file.size > maxBytes);
    photoInput.setCustomValidity(oversized ? `${oversized.name} is larger than 8 MB. Choose a smaller photo.` : "");
    photoError.hidden = !oversized;
    photoError.textContent = oversized ? `${oversized.name} is larger than 8 MB. Choose a smaller photo.` : "";
    return !oversized;
  }

  photoInput?.addEventListener("change", () => {
    validatePhotos();
    preview.replaceChildren();
    for (const file of photoInput.files || []) {
      const item = document.createElement("li");
      item.textContent = `${file.name} (${Math.ceil(file.size / 1024)} KB)`;
      if (file.type.startsWith("image/")) {
        const image = document.createElement("img");
        image.alt = "Selected photo preview";
        image.src = URL.createObjectURL(file);
        image.onload = () => URL.revokeObjectURL(image.src);
        item.append(image);
      }
      preview.append(item);
    }
  });

  next.addEventListener("click", () => {
    if (!validatePhotos()) {
      showStep(1, false);
      photoInput.reportValidity();
      return;
    }
    const invalid = firstInvalid(current);
    if (invalid) {
      invalid.reportValidity();
      invalid.focus();
      return;
    }
    showStep(current + 1);
  });
  back.addEventListener("click", () => showStep(current - 1));

  form.addEventListener("submit", (event) => {
    validatePhotos();
    for (let index = 0; index < steps.length; index += 1) {
      const invalid = firstInvalid(index);
      if (invalid) {
        event.preventDefault();
        showStep(index);
        invalid.reportValidity();
        invalid.focus();
        return;
      }
    }
    if (submitting) {
      event.preventDefault();
      return;
    }
    submitting = true;
    submit.disabled = true;
    submitStatus.textContent = "Sending your report…";
  });

  showStep(current, false);
  const summary = document.getElementById("report-error-summary");
  if (summary) {
    const firstErrorLink = summary.querySelector("a[href^='#id_']");
    const target = firstErrorLink?.getAttribute("href");
    const field = target ? document.querySelector(target) : null;
    const step = field?.closest(".report-step");
    if (step) showStep(Number(step.dataset.step), false);
    summary.focus();
  }
})();
