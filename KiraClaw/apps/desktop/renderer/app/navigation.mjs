export function setActiveView(viewName) {
  for (const button of document.querySelectorAll(".nav-item")) {
    button.classList.toggle("active", button.dataset.view === viewName);
  }

  for (const view of document.querySelectorAll(".view")) {
    view.classList.toggle("active", view.id === `view-${viewName}`);
  }
}

export function bindNavigation({ onViewChange } = {}) {
  for (const button of document.querySelectorAll(".nav-item")) {
    button.addEventListener("click", () => {
      const viewName = button.dataset.view;
      setActiveView(viewName);
      onViewChange?.(viewName);
    });
  }
}
