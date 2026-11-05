const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const assert = require('node:assert/strict');

(async () => {
  const root = path.resolve(__dirname, '..');
  const folder = path.join(root, 'site/dist/procedure-figures');
  const output = process.env.LAB_DASHBOARD_TEST_OUTPUT || path.join(root, 'scratchpad/independent-release/figure-check');
  await fs.mkdir(output, { recursive: true });
  const names = (await fs.readdir(folder)).filter(name => name.endsWith('.svg')).sort();
  assert.ok(names.length > 0);
  const browser = await chromium.launch({ headless: true, channel: process.env.LAB_DASHBOARD_BROWSER_CHANNEL || 'msedge' });
  const page = await browser.newPage();
  const report = [];
  for (const name of names) {
    await page.goto(pathToFileURL(path.join(folder, name)).href);
    await page.evaluate(() => document.fonts.ready);
    const info = await page.locator('svg').evaluate(svg => {
      const box = svg.viewBox.baseVal;
      const texts = [...svg.querySelectorAll('text')].map(element => {
        const rect = element.getBBox();
        return { text: element.textContent, x: rect.x, y: rect.y, width: rect.width, height: rect.height };
      });
      const outside = texts.filter(t => t.x < box.x - 2 || t.y < box.y - 2
        || t.x + t.width > box.x + box.width + 2 || t.y + t.height > box.y + box.height + 2);
      const overlaps = [];
      for (let a = 0; a < texts.length; a++) {
        for (let b = a + 1; b < texts.length; b++) {
          const l = texts[a], r = texts[b];
          const x = Math.min(l.x + l.width, r.x + r.width) - Math.max(l.x, r.x);
          const y = Math.min(l.y + l.height, r.y + r.height) - Math.max(l.y, r.y);
          if (x > 3 && y > 3) overlaps.push([l.text, r.text]);
        }
      }
      return { width: box.width, height: box.height, text_count: texts.length, outside, overlaps };
    });
    assert.ok(info.width > 0 && info.height > 0, name);
    await page.setViewportSize({ width: Math.ceil(info.width), height: Math.ceil(info.height) });
    await page.locator('svg').screenshot({ path: path.join(output, name.replace('.svg', '.png')) });
    report.push({ name, ...info });
  }
  await browser.close();
  const issues = report.filter(item => item.outside.length || item.overlaps.length);
  await fs.writeFile(path.join(output, 'figure-layout-report.json'), JSON.stringify({ figures: report.length, issues, all: report }, null, 2) + '\n');
  console.log(JSON.stringify({ figures: report.length, issue_count: issues.length, issues: issues.map(item => ({ name: item.name, outside: item.outside, overlaps: item.overlaps })) }, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
