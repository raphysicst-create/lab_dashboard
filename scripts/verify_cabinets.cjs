const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const base = process.env.LAB_DASHBOARD_TEST_BASE_URL || 'http://127.0.0.1:4173/';
const output = process.env.LAB_DASHBOARD_TEST_OUTPUT || 'scratch/cabinets-verification';

(async () => {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, ...(process.env.LAB_DASHBOARD_BROWSER_CHANNEL ? { channel: process.env.LAB_DASHBOARD_BROWSER_CHANNEL } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.goto(base);
    await page.locator('#open-chemicals').click();
    const chemicals = await (await page.request.get(new URL('data/chemicals.json', base).href)).json();
    const expectedGroups = {
      acid: ['산'], base: ['염기'], inorganic: ['위험이 높은 무기 화합물'], metal: ['금속'],
      solid: ['위험성이 낮은 고체 약품', '위험성이 낮은 무기·유기 고체 약품'],
      flammable: ['인화성·휘발성 물질', '인화성·휘발성 물질 및 혼합 금지 물질'],
    };
    let known = 0;
    for (const chemical of chemicals) {
      await page.locator('#chemical-search').fill(chemical.name);
      await page.locator('#chemical-results').getByRole('button', { name: chemical.name, exact: true }).click();
      const map = page.locator('#chemical-content .cabinet-map');
      assert.equal(await map.locator('.compartment').count(), 6, chemical.name);
      const expected = Object.entries(expectedGroups).filter(([, categories]) => chemical.cabinets.some(record => categories.includes(record.category))).map(([key]) => key).sort();
      const actual = await map.locator('.compartment:not(.inactive)').evaluateAll(nodes => nodes.map(node => node.dataset.category).sort());
      assert.deepEqual(actual, expected, chemical.name);
      assert.equal(await map.locator('.current').count(), expected.length, chemical.name);
      if (expected.length) {
        known++;
        assert.equal(await map.evaluate(node => node.previousElementSibling?.tagName), 'H3', chemical.name);
        assert.equal(await map.evaluate(node => node.previousElementSibling?.textContent), '보관장 분류', chemical.name);
      } else {
        assert.match(await page.locator('#chemical-content').innerText(), /보관장 분류\s+미확인/, chemical.name);
        assert.equal(await map.evaluate(node => node.previousElementSibling?.textContent), '미확인', chemical.name);
      }
      await page.locator('#chemical-back').click();
    }
    assert.equal(chemicals.length, 177);
    assert.equal(known, 48);
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.locator('#chemical-search').fill('염산');
      await page.locator('#chemical-results').getByRole('button', { name: '염산', exact: true }).click();
      assert.equal(await page.locator('#chemical-dialog').evaluate(node => node.scrollWidth <= node.clientWidth), true);
      await page.screenshot({ path: path.join(output, `acid-${width}.png`) });
      await page.locator('#chemical-back').click();
      await page.getByRole('button', { name: '공통 관리 안내', exact: true }).click();
      assert.equal(await page.locator('.cabinet-map .compartment:not(.inactive)').count(), 6);
      assert.equal(await page.locator('#chemical-dialog').evaluate(node => node.scrollWidth <= node.clientWidth), true);
      await page.locator('.waste-flow').scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(output, `waste-${width}.png`) });
      await page.locator('#chemical-back').click();
    }
    assert.deepEqual(errors, []);
    const report = { status: 'passed', total: chemicals.length, highlighted: known, unknown: chemicals.length - known, widths: [1440,390,320], pageErrors: errors };
    await fs.writeFile(path.join(output, 'cabinets-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
