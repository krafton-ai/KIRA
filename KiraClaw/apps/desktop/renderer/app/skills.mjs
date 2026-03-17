import { byId, escapeHtml, setText } from "./dom.mjs";

function skillCard(skill) {
  return `
    <article class="skill-card">
      <div class="skill-card-head">
        <div>
          <strong>${escapeHtml(skill.name || skill.id || "Skill")}</strong>
          <p class="skill-card-meta">${escapeHtml(skill.source || "unknown")}</p>
        </div>
        <button class="ghost" data-skill-open="${escapeHtml(skill.path)}">Open Folder</button>
      </div>
      <p class="section-copy">${escapeHtml(skill.description || "No description.")}</p>
      <p class="skill-card-path">${escapeHtml(skill.path || "")}</p>
    </article>
  `;
}

export function renderSkillsState(state) {
  const list = byId("skills-list");
  if (!list) {
    return;
  }

  const skills = state.skills?.skills || [];
  if (!skills.length) {
    list.innerHTML = `
      <article class="skill-card skill-card-empty">
        <strong>No skills found</strong>
        <p class="section-copy">Put skill folders under the workspace or global skills directory.</p>
      </article>
    `;
    setText(byId("skills-status"), "No skills are currently available.");
    return;
  }

  list.innerHTML = skills.map(skillCard).join("");
  setText(byId("skills-status"), `${skills.length} skill${skills.length === 1 ? "" : "s"} available.`);
}

export function bindSkillsActions({ state, onReload, onOpenPath }) {
  byId("reload-skills")?.addEventListener("click", onReload);
  byId("open-workspace-skills")?.addEventListener("click", () => {
    onOpenPath(state.skills?.workspace_skill_dir);
  });
  byId("skills-list")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-skill-open]");
    if (!button) {
      return;
    }
    onOpenPath(button.dataset.skillOpen);
  });
}
