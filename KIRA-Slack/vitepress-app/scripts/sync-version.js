const fs = require('fs');
const path = require('path');

// Get version from command line argument or environment variable or package.json
let version = process.argv[2] || process.env.VERSION;

if (!version) {
  // Fallback: Read version from electron-app/package.json
  const electronPkgPath = path.join(__dirname, '../../electron-app/package.json');
  const electronPkg = JSON.parse(fs.readFileSync(electronPkgPath, 'utf8'));
  version = electronPkg.version;
}

console.log(`Syncing version: ${version}`);

// Files to update
const files = [
  'index.md',
  'ko/index.md',
  'ko/getting-started.md',
  'getting-started.md'
];

// Regex to match version patterns
const patterns = [
  { regex: /KIRA-\d+\.\d+\.\d+-(universal|arm64)\.dmg/g, replace: `KIRA-${version}-arm64.dmg` },
  { regex: /KIRA[- ]Setup[- ]\d+\.\d+\.\d+\.exe/g, replace: `KIRA Setup ${version}.exe` }
];

let updated = 0;

files.forEach(file => {
  const filePath = path.join(__dirname, '..', file);
  if (!fs.existsSync(filePath)) return;

  let content = fs.readFileSync(filePath, 'utf8');
  let changed = false;

  patterns.forEach(({ regex, replace }) => {
    const newContent = content.replace(regex, replace);
    if (newContent !== content) {
      content = newContent;
      changed = true;
    }
  });

  if (changed) {
    fs.writeFileSync(filePath, content);
    console.log(`  Updated: ${file}`);
    updated++;
  }
});

console.log(`Done. ${updated} file(s) updated.`);
