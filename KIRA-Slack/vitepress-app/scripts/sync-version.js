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
  {
    regex: /https:\/\/kira\.krafton-ai\.com\/(?:download\/KIRA-\d+\.\d+\.\d+-(?:universal|arm64)\.dmg|download\/KiraClaw-\d+\.\d+\.\d+-arm64\.dmg|download\/kiraclaw\/KiraClaw-\d+\.\d+\.\d+-arm64\.dmg|kiraclaw-download\/KiraClaw-\d+\.\d+\.\d+-arm64\.dmg)/g,
    replace: `https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-${version}-arm64.dmg`
  },
  {
    regex: /https:\/\/kira\.krafton-ai\.com\/(?:download\/KIRA(?:%20| )Setup(?:%20| )\d+\.\d+\.\d+\.exe|download\/KiraClaw-\d+\.\d+\.\d+-x64\.exe|download\/kiraclaw\/KiraClaw-\d+\.\d+\.\d+-x64\.exe|kiraclaw-download\/KiraClaw-\d+\.\d+\.\d+-x64\.exe)/g,
    replace: `https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-${version}-x64.exe`
  }
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
