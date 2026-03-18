const fs = require("fs");

function parseConfigFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const config = {};
  const content = fs.readFileSync(filePath, "utf8");
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) {
      continue;
    }

    const [key, ...valueParts] = line.split("=");
    let value = valueParts.join("=").trim();
    if (value.length >= 2 && value[0] === value[value.length - 1] && (value[0] === '"' || value[0] === "'")) {
      value = value.slice(1, -1);
    }

    value = value.replace(/\\\\/g, "\\");
    value = value.replace(/\\"/g, "\"");
    value = value.replace(/\\'/g, "'");
    value = value.replace(/\\n/g, "\n");
    config[key.trim()] = value;
  }

  return config;
}

function escapeEnvValue(value) {
  return String(value ?? "")
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n");
}

function createConfigStore({ configDir, configFile }) {
  const KIRACLAW_MARKER = "# ============== KiraClaw ==============";

  function ensureDirectory() {
    fs.mkdirSync(configDir, { recursive: true });
  }

  function read() {
    return parseConfigFile(configFile);
  }

  function write(updates) {
    ensureDirectory();

    const existingText = fs.existsSync(configFile) ? fs.readFileSync(configFile, "utf8") : "";
    const lines = existingText ? existingText.split(/\r?\n/) : [];
    const consumed = new Set();

    const updatedLines = lines.map((line) => {
      const match = line.match(/^\s*([A-Za-z0-9_]+)=/);
      if (!match) {
        return line;
      }

      const key = match[1];
      if (!(key in updates)) {
        return line;
      }

      consumed.add(key);
      return `${key}="${escapeEnvValue(updates[key])}"`;
    });

    const pendingKeys = Object.keys(updates).filter((key) => !consumed.has(key));
    if (pendingKeys.length > 0) {
      if (updatedLines.length > 0 && updatedLines[updatedLines.length - 1].trim() !== "") {
        updatedLines.push("");
      }
      const hasMarker = updatedLines.some((line) => line.trim() === KIRACLAW_MARKER);
      if (!hasMarker) {
        updatedLines.push(KIRACLAW_MARKER);
      }
      for (const key of pendingKeys) {
        updatedLines.push(`${key}="${escapeEnvValue(updates[key])}"`);
      }
    }

    const normalized = `${updatedLines.join("\n").replace(/\n+$/, "")}\n`;
    fs.writeFileSync(configFile, normalized, "utf8");
  }

  return {
    configDir,
    configFile,
    ensureDirectory,
    read,
    write,
  };
}

module.exports = {
  createConfigStore,
};
