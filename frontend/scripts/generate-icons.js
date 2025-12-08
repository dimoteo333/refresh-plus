#!/usr/bin/env node

/**
 * PWA Icon Generator
 *
 * Generates all required icon sizes from the SVG template
 *
 * Usage:
 *   npm run generate-icons
 *
 * Or manually:
 *   node scripts/generate-icons.js
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

// Icon sizes to generate
const ICON_SIZES = [
  { size: 72, filename: 'icon-72x72.png' },
  { size: 96, filename: 'icon-96x96.png' },
  { size: 128, filename: 'icon-128x128.png' },
  { size: 144, filename: 'icon-144x144.png' },
  { size: 152, filename: 'icon-152x152.png' },
  { size: 192, filename: 'icon-192x192.png' },
  { size: 384, filename: 'icon-384x384.png' },
  { size: 512, filename: 'icon-512x512.png' },
];

// Badge icon (notification badge)
const BADGE_SIZE = { size: 72, filename: 'badge-72x72.png' };

// Paths
const PUBLIC_DIR = path.join(__dirname, '..', 'public');
const SVG_TEMPLATE = path.join(PUBLIC_DIR, 'icon-template.svg');
const OUTPUT_DIR = PUBLIC_DIR;

async function generateIcons() {
  console.log('🎨 Generating PWA icons...\n');

  // Check if SVG template exists
  if (!fs.existsSync(SVG_TEMPLATE)) {
    console.error('❌ Error: icon-template.svg not found in public/');
    console.error('   Please create the SVG template first.');
    process.exit(1);
  }

  // Read SVG template
  const svgBuffer = fs.readFileSync(SVG_TEMPLATE);

  try {
    // Generate all icon sizes
    for (const { size, filename } of ICON_SIZES) {
      const outputPath = path.join(OUTPUT_DIR, filename);

      await sharp(svgBuffer)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 }
        })
        .png()
        .toFile(outputPath);

      console.log(`✓ Generated ${filename} (${size}x${size})`);
    }

    // Generate badge icon (simplified version for notifications)
    const badgeOutputPath = path.join(OUTPUT_DIR, BADGE_SIZE.filename);
    await sharp(svgBuffer)
      .resize(BADGE_SIZE.size, BADGE_SIZE.size, {
        fit: 'contain',
        background: { r: 0, g: 0, b: 0, alpha: 0 }
      })
      .png()
      .toFile(badgeOutputPath);

    console.log(`✓ Generated ${BADGE_SIZE.filename} (${BADGE_SIZE.size}x${BADGE_SIZE.size})`);

    console.log('\n✅ All icons generated successfully!');
    console.log(`   Location: ${OUTPUT_DIR}`);
    console.log('\n📱 Next steps:');
    console.log('   1. Verify the icons look correct');
    console.log('   2. Run npm run dev to test');
    console.log('   3. Deploy to production');

  } catch (error) {
    console.error('❌ Error generating icons:', error);
    process.exit(1);
  }
}

// Run generator
generateIcons();
