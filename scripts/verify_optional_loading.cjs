const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

const base = process.env.LAB_DASHBOARD_TEST_BASE_URL || 'http://127.0.0.1:4173/';
const output = process.env.LAB_DASHBOARD_TEST_OUTPUT
  || path.resolve(__dirname, '../output/validation/optional-loading-20260923/local');
const loadingText = '약품 정보를 불러오는 중입니다.';
const failedText = '약품 정보를 불러오지 못했습니다.';
const unusedData = ['materials.json', 'chemical_guidelines.json', 'quantities.json'];
const optionalNames = ['chemicals.json', ...unusedData, 'chemical-ui.js', 'chemical-diagrams.js'];
const filename = url => new URL(url).pathname.split('/').pop();
const displayItems = items => items == null ? '미확인' : items.length ? items.join(', ') : '해당 항목 없음';

(async () => {
  await fs.mkdir(output, { recursive: true });
  // Read fixtures from disk so verification itself cannot pollute browser request counts.
  const activities = JSON.parse(await fs.readFile(path.resolve(__dirname, '../site/dist/data/activities.json'), 'utf8'));
  const chemicals = JSON.parse(await fs.readFile(path.resolve(__dirname, '../site/dist/data/chemicals.json'), 'utf8'));
  const procedures = JSON.parse(await fs.readFile(path.resolve(__dirname, '../site/dist/data/procedures.json'), 'utf8'));
  const measured = activities.find(activity => activity.id === 'ybm_k8_0002');
  const survey = activities.find(activity => activity.id === 'miraen_IS1_001');
  const procedureSection = '.procedure-section';
  assert.equal(activities.length, 1276);
  const linked = activities.find(activity => activity.id === 'activity_0001');
  const otherLinked = activities.find(activity => activity.chemical_ids?.length
    && !activity.chemical_ids.some(id => linked.chemical_ids.includes(id)));
  const unlinked = activities.find(activity => !activity.chemical_ids?.length && activity.equipment?.length);
  assert.ok(linked?.chemical_ids?.length && otherLinked && unlinked);
  const namesFor = activity => activity.chemical_ids.map(id => chemicals.find(chemical => chemical.id === id).name);
  const results = [];
  const browser = await chromium.launch({ headless: true,
    ...(process.env.LAB_DASHBOARD_BROWSER_CHANNEL ? { channel: process.env.LAB_DASHBOARD_BROWSER_CHANNEL } : {}) });

  async function scenario(name, run) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    page.setDefaultTimeout(10000);
    const requests = [];
    const pageErrors = [];
    const cleanup = [];
    page.on('request', request => requests.push({ file: filename(request.url()), url: request.url() }));
    page.on('pageerror', error => pageErrors.push(String(error)));
    const count = file => requests.filter(request => request.file === file).length;
    const noUnused = () => assert.deepEqual(requests.filter(request => unusedData.includes(request.file)), [], name);
    try {
      await run({ context, page, requests, count, cleanup });
      noUnused();
      assert.deepEqual(pageErrors, [], `${name}: unhandled page errors`);
      results.push({ name, status: 'passed', requestCounts: Object.fromEntries([...new Set(requests.map(request => request.file))]
        .map(file => [file, count(file)])), pageErrors });
      console.log(`PASS ${name}`);
    } catch (error) {
      await page.screenshot({ path: path.join(output, `failure-${name}.png`), fullPage: true }).catch(() => {});
      results.push({ name, status: 'failed', error: String(error), requests, pageErrors });
      throw error;
    } finally {
      for (const release of cleanup) release();
      await fs.writeFile(path.join(output, 'optional-loading-report.json'), JSON.stringify({
        status: results.some(result => result.status === 'failed') ? 'failed' : 'in_progress', base, results,
      }, null, 2));
      await context.close();
    }
  }

  async function boot(page) {
    await page.goto(base);
    await page.getByRole('heading', { name: '탐구활동 1,276건', exact: true }).waitFor();
    assert.equal(await page.locator('#open-chemicals').isEnabled(), true);
  }

  async function openActivity(page, activity) {
    await page.locator('#search').fill(activity.title);
    await page.locator(`[data-activity-id="${activity.id}"] .card-actions button`).click();
    assert.equal(await page.locator('#activity-dialog').isVisible(), true);
    assert.equal(await page.locator('#dialog-title').innerText(), activity.title);
    assert.deepEqual(await page.locator('#dialog-content .raw-materials').allTextContents(),
      [displayItems(activity.equipment), displayItems(activity.supplies)]);
  }

  async function readyCatalog(page) {
    await page.locator('#chemical-search').waitFor();
    assert.equal(await page.locator('#chemical-count').innerText(), '약품 177건');
  }

  async function readyActivity(page, activity) {
    for (const name of namesFor(activity)) {
      await page.locator('#activity-dialog').getByRole('button', { name, exact: true }).waitFor();
    }
    assert.deepEqual(await page.locator('#activity-dialog .chemical-links button').allTextContents(), namesFor(activity));
  }

  async function checkCoreStillWorks(page) {
    await page.locator('#reset-filters').click();
    await page.locator('#search').fill('염산');
    const acidCount = activities.filter(activity => [activity.title, activity.materials_raw,
      activity.achievement_raw, activity.unit, activity.publisher_raw].some(value => String(value ?? '').includes('염산'))).length;
    assert.equal(await page.locator('#result-count').innerText(), `탐구활동 ${acidCount.toLocaleString('ko')}건`);
    await page.locator('#reset-filters').click();
    await page.locator('#grade-filter').selectOption('high-1');
    assert.equal(await page.locator('#result-count').innerText(), '탐구활동 414건');
    await page.locator('#reset-filters').click();
    assert.equal(await page.locator('#result-count').innerText(), '탐구활동 1,276건');
  }

  async function holdChemicals(scope, firstOnly = false) {
    let release;
    const gate = new Promise(resolve => { release = resolve; });
    let hits = 0;
    scope.cleanup.push(release);
    await scope.context.route('**/data/chemicals.json*', async route => {
      hits++;
      if (!firstOnly || hits === 1) await gate;
      await route.continue().catch(error => {
        if (!/Target.*closed|Route is already handled|Invalid InterceptionId/.test(String(error))) throw error;
      });
    });
    return release;
  }

  try {
    await scenario('initial-core-only-and-unlinked-detail', async ({ page, requests, count }) => {
      await boot(page);
      await page.waitForLoadState('networkidle');
      assert.deepEqual(requests.filter(request => request.file.endsWith('.json')).map(request => request.file).sort(),
        ['achievements.json', 'activities.json']);
      assert.equal(requests.filter(request => request.file.endsWith('.svg')).length, 0);
      assert.equal(count('activities.json'), 1);
      assert.equal(count('achievements.json'), 1);
      assert.deepEqual(requests.filter(request => optionalNames.includes(request.file)), []);
      await checkCoreStillWorks(page);
      await openActivity(page, unlinked);
      assert.ok((await page.locator('#dialog-content').innerText()).includes('연결된 약품 정보: 미확인'));
      await page.waitForLoadState('networkidle');
      assert.deepEqual(requests.filter(request => optionalNames.includes(request.file)), []);
      await page.screenshot({ path: path.join(output, 'unlinked-detail-no-optional-requests.png') });
    });

    await scenario('procedure-steps-and-dialog-switch', async ({ context, page, count, cleanup }) => {
      let release;
      const gate = new Promise(resolve => { release = resolve; });
      cleanup.push(release);
      await context.route('**/data/procedures.json*', async route => { await gate; await route.continue(); });
      await page.setViewportSize({ width: 390, height: 844 });
      await boot(page);
      assert.equal(count('procedures.json'), 0);
      await openActivity(page, measured);
      await page.locator(procedureSection).getByText('탐구 과정을 불러오는 중입니다.').waitFor();
      await page.locator('#close-dialog').click();
      await openActivity(page, survey);
      release();
      await page.locator(procedureSection + ' li').first().waitFor();
      assert.deepEqual(await page.locator(procedureSection + ' li').allTextContents(), procedures[survey.id].flatMap(g => g.steps));
      assert.equal(await page.locator('#dialog-title').innerText(), survey.title);
      await page.locator('#close-dialog').click();
      await openActivity(page, measured);
      await page.locator(procedureSection + ' li').first().waitFor();
      assert.deepEqual(await page.locator(procedureSection + ' li').allTextContents(), procedures[measured.id].flatMap(g => g.steps));
      assert.equal(count('procedures.json'), 1);
      assert.equal(await page.locator('#activity-dialog').evaluate(dialog => dialog.scrollWidth <= dialog.clientWidth), true);
      await page.locator(procedureSection).scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(output, 'mobile-procedure.png') });
    });

    await scenario('procedure-error-retry-and-null', async ({ context, page, count }) => {
      let fail = true;
      await context.route('**/data/procedures.json*', route => route.fulfill(fail
        ? { status: 503, body: 'unavailable' }
        : { json: { ...procedures, [linked.id]: null } }));
      await boot(page);
      await openActivity(page, linked);
      await readyActivity(page, linked);
      await page.locator(procedureSection).getByText('탐구 과정을 불러오지 못했습니다.').waitFor();
      fail = false;
      await page.getByRole('button', { name: '과정 다시 시도' }).click();
      await page.locator(procedureSection).getByText('미확인', { exact: true }).waitFor();
      assert.equal(count('procedures.json'), 2);
      assert.equal(await page.locator(procedureSection + ' ol').count(), 0);
      await readyActivity(page, linked);
    });

    await scenario('procedure-groups-single-step-and-unconfirmed', async ({ page, count }) => {
      await boot(page);
      const unconfirmed = activities.find(row => procedures[row.id] === null);
      for (const id of ['activity_0210', 'activity_0202', ...(unconfirmed ? [unconfirmed.id] : [])]) {
        const activity = activities.find(row => row.id === id);
        const groups = procedures[id];
        await openActivity(page, activity);
        const section = page.locator(procedureSection);
        if (groups === null) {
          await section.getByText('미확인', { exact: true }).waitFor();
        } else {
          const lists = section.locator('ol');
          await lists.first().waitFor();
          assert.equal(await lists.count(), id === 'activity_0210' ? 2 : 1);
          if (id === 'activity_0202') assert.equal(await lists.locator('li').count(), 1);
          assert.deepEqual(await section.locator('h4').allTextContents(), groups.map(g => g.heading).filter(Boolean));
          for (const [i, group] of groups.entries()) {
            assert.deepEqual(await lists.nth(i).locator('li').allTextContents(), group.steps);
          }
          if (id === 'activity_0210') {
            const figures = section.locator('figure');
            assert.equal(await figures.count(), 2);
            for (const [i, group] of groups.entries()) {
              const figure = figures.nth(i);
              const img = figure.locator('img');
              await img.scrollIntoViewIfNeeded();
              await img.evaluate(image => image.decode());
              assert.equal(await img.getAttribute('alt'), group.figures[0].alt);
              assert.ok(await img.evaluate(image => image.naturalWidth > 0));
              const link = figure.getByRole('link', { name: /크게 보기/ });
              assert.equal(await link.getAttribute('href'), await img.getAttribute('src'));
              assert.equal(await link.getAttribute('target'), '_blank');
            }
            const directions = await lists.nth(1).innerText();
            assert.match(directions, /기준선.*60°/s);
            assert.match(directions, /30°/);
            assert.doesNotMatch(directions, /[①②]에서/);
            const [enlarged] = await Promise.all([
              page.waitForEvent('popup'),
              figures.last().getByRole('link', { name: /크게 보기/ }).click(),
            ]);
            await enlarged.locator('svg').waitFor({ state: 'visible' });
            assert.ok(enlarged.url().endsWith('/' + groups[1].figures[0].file));
            await enlarged.close();
            const heading = section.locator('h4').last();
            for (const [width, height] of [[1440, 1000], [390, 844], [320, 700]]) {
              await page.setViewportSize({ width, height });
              await heading.evaluate(el => el.scrollIntoView({ block: 'start' }));
              const fits = await page.locator('#activity-dialog').evaluate(dialog =>
                dialog.scrollWidth <= dialog.clientWidth && dialog.getBoundingClientRect().right <= innerWidth);
              assert.ok(fits, `procedure overflow at ${width}px`);
              if (width !== 320) {
                const filename = width === 1440 ? 'desktop-refraction.png' : 'mobile-refraction.png';
                await page.screenshot({ path: path.join(output, filename) });
                if (width === 1440) {
                  const top = await heading.boundingBox();
                  const bottom = await figures.last().boundingBox();
                  await page.screenshot({ path: path.join(output, 'desktop-refraction-detail.png'), clip: {
                    x: top.x - 8, y: top.y - 8, width: top.width + 16,
                    height: bottom.y + bottom.height - top.y + 16,
                  } });
                }
              }
            }
            await page.setViewportSize({ width: 1440, height: 1000 });
          }
        }
        await page.locator('#close-dialog').click();
      }
      assert.equal(count('procedures.json'), 1);
    });

    await scenario('catalog-trigger-and-success-cache', async ({ page, count }) => {
      await boot(page);
      await page.locator('#open-chemicals').click();
      await readyCatalog(page);
      for (const file of ['chemicals.json', 'chemical-ui.js', 'chemical-diagrams.js']) assert.equal(count(file), 1, file);
      await page.getByRole('button', { name: '공통 관리 안내', exact: true }).click();
      assert.equal(await page.locator('.cabinet-map .compartment:not(.inactive)').count(), 6);
      assert.equal(await page.locator('.waste-flow .waste-result').count(), 4);
      await page.locator('#chemical-close').click();
      await openActivity(page, linked);
      await readyActivity(page, linked);
      await page.locator('#close-dialog').click();
      await page.locator('#open-chemicals').click();
      await readyCatalog(page);
      for (const file of ['chemicals.json', 'chemical-ui.js', 'chemical-diagrams.js']) assert.equal(count(file), 1, file);
    });

    await scenario('linked-detail-immediate-during-loading', async scope => {
      const { page, count } = scope;
      const release = await holdChemicals(scope);
      await boot(page);
      await openActivity(page, linked);
      await page.locator('#activity-dialog').getByText(loadingText, { exact: true }).waitFor();
      assert.equal(await page.locator('#activity-dialog .chemical-links').count(), 0);
      await page.screenshot({ path: path.join(output, 'linked-detail-loading.png') });
      release();
      await readyActivity(page, linked);
      assert.equal(count('chemicals.json'), 1);
      await page.locator('#activity-dialog').getByRole('button', { name: namesFor(linked)[0], exact: true }).click();
      assert.equal(await page.locator('#chemical-title').innerText(), namesFor(linked)[0]);
    });

    for (const [failure, response] of [
      ['404', { status: 404, body: 'not found' }],
      ['invalid-json', { status: 200, contentType: 'application/json', body: '{invalid' }],
      ['invalid-shape', { status: 200, contentType: 'application/json', body: '{"chemicals":[]}' }],
      ['invalid-record', { status: 200, contentType: 'application/json', body: '[null]' }],
    ]) {
      await scenario(`chemicals-${failure}-isolation-and-retry`, async ({ context, page, count }) => {
        let fail = true;
        await context.route('**/data/chemicals.json*', route => fail ? route.fulfill(response) : route.continue());
        await boot(page);
        await page.locator('#open-chemicals').click();
        await page.locator('#chemical-dialog').getByText(failedText, { exact: true }).waitFor();
        assert.equal(await page.locator('#load-status').isVisible(), false);
        await page.locator('#chemical-close').click();
        await checkCoreStillWorks(page);
        await page.locator('#open-chemicals').click();
        await page.locator('#chemical-dialog').getByRole('button', { name: '다시 시도', exact: true }).waitFor();
        fail = false;
        await page.locator('#chemical-dialog').getByRole('button', { name: '다시 시도', exact: true }).click();
        await readyCatalog(page);
        assert.ok(count('chemicals.json') >= 2);
      });
    }

    await scenario('activity-failure-and-inline-retry', async ({ context, page }) => {
      let fail = true;
      await context.route('**/data/chemicals.json*', route => fail
        ? route.fulfill({ status: 404, body: 'not found' }) : route.continue());
      await boot(page);
      await openActivity(page, linked);
      await page.locator('#activity-dialog').getByText(failedText, { exact: true }).waitFor();
      assert.equal(await page.locator('#dialog-title').innerText(), linked.title);
      await page.screenshot({ path: path.join(output, 'linked-detail-retry.png') });
      fail = false;
      await page.locator('#activity-dialog').getByRole('button', { name: '다시 시도', exact: true }).click();
      await readyActivity(page, linked);
    });

    for (const file of ['chemical-ui.js', 'chemical-diagrams.js']) {
      await scenario(`${file.replace('.js', '')}-404-and-module-retry`, async ({ context, page, requests, count }) => {
        let fail = true;
        await context.route(`**/${file}*`, route => fail
          ? route.fulfill({ status: 404, contentType: 'text/javascript', body: 'not found' }) : route.continue());
        await boot(page);
        await page.locator('#open-chemicals').click();
        await page.locator('#chemical-dialog').getByText(failedText, { exact: true }).waitFor();
        await page.locator('#chemical-close').click();
        await checkCoreStillWorks(page);
        await page.locator('#open-chemicals').click();
        await page.locator('#chemical-dialog').getByRole('button', { name: '다시 시도', exact: true }).waitFor();
        fail = false;
        await page.locator('#chemical-dialog').getByRole('button', { name: '다시 시도', exact: true }).click();
        await readyCatalog(page);
        assert.ok(count(file) >= 2, `${file} must be fetched again after failed ES module import`);
        assert.ok(new Set(requests.filter(request => request.file === file).map(request => request.url)).size >= 2,
          `${file} retry must use a fresh module URL`);
      });
    }

    await scenario('closed-activity-not-reopened-after-response', async scope => {
      const { page } = scope;
      const release = await holdChemicals(scope);
      await boot(page);
      await openActivity(page, linked);
      await page.locator('#activity-dialog').getByText(loadingText, { exact: true }).waitFor();
      await page.keyboard.press('Escape');
      release();
      await page.waitForLoadState('networkidle');
      assert.equal(await page.locator('#activity-dialog').isVisible(), false);
      assert.equal(await page.locator('#chemical-dialog').isVisible(), false);
      await checkCoreStillWorks(page);
    });

    await scenario('closed-catalog-not-reopened-after-response', async scope => {
      const { page } = scope;
      const release = await holdChemicals(scope);
      await boot(page);
      await page.locator('#open-chemicals').click();
      await page.locator('#chemical-dialog').getByText(loadingText, { exact: true }).waitFor();
      await page.locator('#chemical-close').click();
      release();
      await page.waitForLoadState('networkidle');
      assert.equal(await page.locator('#chemical-dialog').isVisible(), false);
      assert.equal(await page.locator('#activity-dialog').isVisible(), false);
      await openActivity(page, linked);
      await readyActivity(page, linked);
      await page.locator('#activity-dialog').getByRole('button', { name: namesFor(linked)[0], exact: true }).click();
      assert.equal(await page.locator('#chemical-title').innerText(), namesFor(linked)[0]);
      assert.equal(await page.locator('#chemical-content').getAttribute('aria-busy'), 'false');
    });

    for (const next of [unlinked, otherLinked]) {
      await scenario(`pending-response-switch-to-${next === unlinked ? 'unlinked' : 'other-linked'}-activity`, async scope => {
        const { page, count } = scope;
        const release = await holdChemicals(scope);
        await boot(page);
        await openActivity(page, linked);
        await page.locator('#activity-dialog').getByText(loadingText, { exact: true }).waitFor();
        await page.locator('#close-dialog').click();
        await openActivity(page, next);
        release();
        await page.waitForLoadState('networkidle');
        assert.equal(await page.locator('#dialog-title').innerText(), next.title);
        assert.deepEqual(await page.locator('#dialog-content .raw-materials').allTextContents(),
          [displayItems(next.equipment), displayItems(next.supplies)]);
        if (next === unlinked) {
          assert.ok((await page.locator('#dialog-content').innerText()).includes('연결된 약품 정보: 미확인'));
          assert.equal(await page.locator('#activity-dialog .chemical-links').count(), 0);
        } else await readyActivity(page, next);
        assert.equal(count('chemicals.json'), 1, 'overlapping activity opens share the pending request');
        assert.equal(await page.locator('#chemical-dialog').isVisible(), false);
      });
    }

    await scenario('catalog-activity-concurrent-request-reuse', async scope => {
      const { page, count } = scope;
      const release = await holdChemicals(scope);
      await boot(page);
      await page.locator('#open-chemicals').click();
      await page.locator('#chemical-dialog').getByText(loadingText, { exact: true }).waitFor();
      await page.locator('#chemical-close').click();
      await openActivity(page, linked);
      await page.locator('#activity-dialog').getByText(loadingText, { exact: true }).waitFor();
      await page.locator('#close-dialog').click();
      await page.locator('#open-chemicals').click();
      release();
      await readyCatalog(page);
      for (const file of ['chemicals.json', 'chemical-ui.js', 'chemical-diagrams.js']) assert.equal(count(file), 1, file);
      assert.equal(await page.locator('#activity-dialog').isVisible(), false);
    });

    await scenario('chemical-timeout-and-retry', async scope => {
      const { page, count } = scope;
      const release = await holdChemicals(scope, true);
      await boot(page);
      await page.clock.install();
      await page.locator('#open-chemicals').click();
      await page.locator('#chemical-dialog').getByText(loadingText, { exact: true }).waitFor();
      await page.clock.fastForward(16000);
      await page.locator('#chemical-dialog').getByText(failedText, { exact: true }).waitFor();
      release();
      await page.locator('#chemical-dialog').getByRole('button', { name: '다시 시도', exact: true }).click();
      await readyCatalog(page);
      assert.equal(count('chemicals.json'), 2);
    });

    for (const file of ['activities.json', 'achievements.json']) {
      await scenario(`core-${file.replace('.json', '')}-404-remains-fatal`, async ({ context, page, requests }) => {
        let fail = true;
        await context.route(`**/data/${file}*`, route => fail
          ? route.fulfill({ status: 404, body: 'not found' }) : route.continue());
        await page.goto(base);
        await page.getByRole('button', { name: '다시 불러오기', exact: true }).waitFor();
        assert.equal(await page.locator('#activities-view').isVisible(), false);
        assert.deepEqual(requests.filter(request => optionalNames.includes(request.file)), []);
        fail = false;
        await page.getByRole('button', { name: '다시 불러오기', exact: true }).click();
        await page.getByRole('heading', { name: '탐구활동 1,276건', exact: true }).waitFor();
      });
    }

    const report = { status: 'passed', base, activityRows: activities.length, chemicalRows: chemicals.length,
      scenarioCount: results.length, results };
    await fs.writeFile(path.join(output, 'optional-loading-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ status: report.status, scenarioCount: results.length, output }, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
