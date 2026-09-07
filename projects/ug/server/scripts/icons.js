// Renders the app icon SVG to PNGs for the manifest (192, 512, maskable) with the bundled Chromium.
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const svg = readFileSync(join(root, 'brand', 'app-icon.svg'), 'utf8');
const out = join(root, 'site', 'icons'); mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
for (const size of [192, 512]) {
  const page = await browser.newPage({ viewport: { width: size, height: size } });
  await page.setContent(`<body style="margin:0;background:#0F0C0A">${svg.replace('width="128" height="128"', `width="${size}" height="${size}"`)}</body>`);
  writeFileSync(join(out, `icon-${size}.png`), await page.screenshot({ type: 'png' }));
  await page.close();
}
await browser.close();
console.log('icons written to site/icons');
