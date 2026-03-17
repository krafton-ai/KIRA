export function byId(id) {
  return document.getElementById(id);
}

export function setText(element, value) {
  if (element) {
    element.textContent = value;
  }
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function createEyeToggleMarkup() {
  return `
    <svg class="eye-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
    </svg>
    <svg class="eye-slash-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" style="display: none;">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
    </svg>
  `;
}

export function initializePasswordToggles() {
  const passwordInputs = document.querySelectorAll('input[type="password"][data-secret="true"]');

  for (const input of passwordInputs) {
    if (input.parentElement && input.parentElement.classList.contains("input-with-toggle")) {
      continue;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "input-with-toggle";
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const toggleButton = document.createElement("button");
    toggleButton.type = "button";
    toggleButton.className = "toggle-visibility";
    toggleButton.setAttribute("aria-label", "Toggle secret visibility");
    toggleButton.innerHTML = createEyeToggleMarkup();

    toggleButton.addEventListener("click", () => {
      const reveal = input.type === "password";
      input.type = reveal ? "text" : "password";

      const eye = toggleButton.querySelector(".eye-icon");
      const eyeSlash = toggleButton.querySelector(".eye-slash-icon");
      if (eye && eyeSlash) {
        eye.style.display = reveal ? "none" : "block";
        eyeSlash.style.display = reveal ? "block" : "none";
      }
    });

    wrapper.appendChild(toggleButton);
  }
}
