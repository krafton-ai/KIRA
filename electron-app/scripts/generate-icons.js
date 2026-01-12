/**
 * Icon Generation Script for KIRA
 *
 * Generates Windows .ico and Linux .png icons from source PNG
 * Uses sharp library for image processing
 *
 * Usage: node scripts/generate-icons.js
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const SOURCE_PNG = path.join(__dirname, '..', 'kira-icon.png');
const ICONS_DIR = path.join(__dirname, '..', 'icons');

// Icon sizes for Windows ICO (multi-resolution)
const ICO_SIZES = [16, 24, 32, 48, 64, 128, 256];

async function generateIcons() {
  console.log('Generating icons from:', SOURCE_PNG);

  // Ensure icons directory exists
  if (!fs.existsSync(ICONS_DIR)) {
    fs.mkdirSync(ICONS_DIR, { recursive: true });
  }

  // Check if source PNG exists
  if (!fs.existsSync(SOURCE_PNG)) {
    console.error('Source PNG not found:', SOURCE_PNG);
    console.error('Please ensure kira-icon.png exists in the electron-app directory');
    process.exit(1);
  }

  try {
    // Generate Linux icon (512x512 PNG)
    const linuxIconPath = path.join(ICONS_DIR, 'icon.png');
    await sharp(SOURCE_PNG)
      .resize(512, 512)
      .png()
      .toFile(linuxIconPath);
    console.log('Generated Linux icon:', linuxIconPath);

    // Generate Windows icon sizes (for manual ICO creation or electron-builder)
    // Note: electron-builder can auto-convert PNG to ICO if you provide icon.png
    // But for better control, we generate multiple sizes

    // Generate 256x256 PNG for Windows (electron-builder can convert this to ICO)
    const win256Path = path.join(ICONS_DIR, 'icon-256.png');
    await sharp(SOURCE_PNG)
      .resize(256, 256)
      .png()
      .toFile(win256Path);
    console.log('Generated Windows 256x256:', win256Path);

    // For proper ICO file, you may need to use a tool like png-to-ico
    // For now, electron-builder will auto-convert if we rename icon-256.png to icon.ico
    // or use an online converter

    console.log('\n=== Icon Generation Complete ===');
    console.log('For Windows ICO file, you have two options:');
    console.log('1. Use an online PNG to ICO converter with icon-256.png');
    console.log('2. Install png-to-ico: npm install -g png-to-ico');
    console.log('   Then run: png-to-ico icons/icon-256.png > icons/icon.ico');
    console.log('3. electron-builder may auto-convert PNG to ICO during build');

  } catch (error) {
    console.error('Error generating icons:', error);
    process.exit(1);
  }
}

generateIcons();
