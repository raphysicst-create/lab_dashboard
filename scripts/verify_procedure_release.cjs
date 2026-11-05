const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { createHash } = require('node:crypto');

const root = path.resolve(__dirname, '..');
const site = path.join(root, 'site/dist');
const base = process.env.LAB_DASHBOARD_TEST_BASE_URL || 'https://raphysicst-create.github.io/lab_dashboard/';
const output = process.env.LAB_DASHBOARD_TEST_OUTPUT || path.join(root, 'output/validation/independent-20261105/public');
const report = {
  status: 'in_progress', base, started_at: new Date().toISOString(),
  files: [], activities: [], image_checks: [], responsive_checks: [],
  page_errors: [], failed_requests: [], http_errors: [],
};
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
let currentActivity = null;

async function saveReport() {
  await fs.writeFile(path.join(output, 'public-release-report.json'), JSON.stringify(report, null, 2) + '\n');
}

async function publicFiles(directory, prefix = '') {
  const files = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const name = prefix + entry.name;
    if (entry.isDirectory()) files.push(...await publicFiles(path.join(directory, entry.name), name + '/'));
    else if (entry.isFile() && !/^test-.*\.html$/.test(entry.name)) files.push(name);
  }
  return files.sort();
}

async function comparePublishedFiles(context) {
  const names = await publicFiles(site);
  for (let start = 0; start < names.length; start += 6) {
    const batch = await Promise.allSettled(names.slice(start, start + 6).map(async name => {
      const url = new URL(name, base).href;
      const response = await context.request.get(url, { timeout: 30000 });
      const actual = await response.body();
      const expected = await fs.readFile(path.join(site, name));
      const check = { name, url, status: response.status(), expected_sha256: digest(expected), public_sha256: digest(actual), bytes: actual.length };
      report.files.push(check);
      assert.equal(response.status(), 200, `${name}: HTTP ${response.status()}`);
      assert.equal(check.public_sha256, check.expected_sha256, `${name}: deployed bytes differ`);
    }));
    const failures = batch.filter(result => result.status === 'rejected');
    if (failures.length) throw new AggregateError(failures.map(result => result.reason), 'Public file verification failed');
  }
  report.files.sort((a, b) => a.name.localeCompare(b.name));
  console.log(`PASS public file hashes: ${report.files.length}`);
}

async function openActivity(page, activity) {
  currentActivity = activity.id;
  await page.locator('#search').fill(activity.title);
  const card = page.locator(`[data-activity-id="${activity.id}"]`);
  while (!await card.count()) {
    const more = page.locator('#load-more');
    assert.ok(await more.isVisible(), `${activity.id}: search did not find its card`);
    await more.click();
  }
  await card.locator('.card-actions button').click();
  await page.locator('#activity-dialog').waitFor({ state: 'visible' });
  assert.equal(await page.locator('#dialog-title').textContent(), activity.title);
  await page.locator('.procedure-section > div[aria-busy="false"]').waitFor();
}

async function readProcedure(page, activity, groups) {
  const section = page.locator('.procedure-section');
  if (groups === null) {
    assert.equal(await section.locator('ol').count(), 0, activity.id);
    assert.equal(await section.locator('> div').innerText(), '미확인', activity.id);
  } else {
    const lists = section.locator('ol');
    assert.equal(await lists.count(), groups.length, activity.id);
    assert.deepEqual(await section.locator('h4').allTextContents(), groups.map(group => group.heading).filter(Boolean), activity.id);
    for (const [index, group] of groups.entries()) {
      assert.deepEqual(await lists.nth(index).locator('li').allTextContents(), group.steps, activity.id);
    }
  }
  const expected = (groups || []).flatMap(group => group.figures || []);
  const figures = section.locator('figure');
  assert.equal(await figures.count(), expected.length, activity.id);
  for (const [index, item] of expected.entries()) {
    const figure = figures.nth(index);
    const image = figure.locator('img');
    await image.scrollIntoViewIfNeeded();
    const decoded = await image.evaluate(async element => {
      await element.decode();
      const rect = element.getBoundingClientRect();
      return { url: element.currentSrc, width: element.naturalWidth, height: element.naturalHeight, rendered_width: rect.width, rendered_height: rect.height };
    });
    assert.ok(decoded.width > 0 && decoded.height > 0, item.file);
    assert.ok(decoded.rendered_width >= 100 && decoded.rendered_height >= 60, `${item.file}: collapsed image`);
    assert.equal(decoded.url, new URL('procedure-figures/' + item.file, base).href);
    assert.equal(await image.getAttribute('alt'), item.alt);
    assert.ok((await figure.locator('figcaption').innerText()).startsWith(item.caption), item.file);
    const enlarge = figure.getByRole('link', { name: /크게 보기/ });
    assert.equal(await enlarge.getAttribute('href'), decoded.url);
    assert.equal(await enlarge.getAttribute('target'), '_blank');
    report.image_checks.push({ activity: activity.id, file: item.file, ...decoded });
  }
  report.activities.push({ id: activity.id, groups: groups?.length || 0, steps: groups?.reduce((sum, group) => sum + group.steps.length, 0) || 0, figures: expected.length, held: groups === null });
}

async function responsiveProof(page, activity, label) {
  await openActivity(page, activity);
  const section = page.locator('.procedure-section');
  const figures = section.locator('figure');
  for (const [width, height] of [[1440, 1000], [390, 844], [320, 700]]) {
    await page.setViewportSize({ width, height });
    const anchor = activity.id === 'activity_0210' ? section.locator('h4').last() : section.locator('h3');
    await anchor.evaluate(element => element.scrollIntoView({ block: 'start' }));
    const fits = await page.locator('#activity-dialog').evaluate(dialog => {
      const rect = dialog.getBoundingClientRect();
      return dialog.scrollWidth <= dialog.clientWidth && rect.left >= 0 && rect.right <= innerWidth;
    });
    assert.ok(fits, `${activity.id}: horizontal overflow at ${width}px`);
    for (let index = 0; index < await figures.count(); index++) {
      const img = figures.nth(index).locator('img');
      await img.scrollIntoViewIfNeeded();
      await img.evaluate(element => element.decode());
      assert.ok(await img.evaluate(element => {
        const rect = element.getBoundingClientRect();
        return rect.width >= 100 && rect.height >= 60 && rect.left >= 0 && rect.right <= innerWidth;
      }), `${activity.id}: image outside viewport at ${width}px`);
    }
    await anchor.evaluate(element => element.scrollIntoView({ block: 'start' }));
    const filename = `${label}-${width}.png`;
    await page.screenshot({ path: path.join(output, filename) });
    report.responsive_checks.push({ id: activity.id, width, height, screenshot: filename });
    if (activity.id === 'activity_0210' && width === 1440) {
      const top = await anchor.boundingBox();
      const bottom = await figures.last().boundingBox();
      await page.screenshot({ path: path.join(output, 'desktop-refraction-detail.png'), clip: {
        x: top.x - 8, y: top.y - 8, width: top.width + 16,
        height: bottom.y + bottom.height - top.y + 16,
      } });
    }
  }
  if (activity.id === 'activity_0210') {
    const [popup] = await Promise.all([
      page.waitForEvent('popup'),
      figures.last().getByRole('link', { name: /크게 보기/ }).click(),
    ]);
    await popup.locator('svg').waitFor({ state: 'visible' });
    report.enlarged_image_url = popup.url();
    assert.ok(popup.url().endsWith('/activity_0210-original-02.svg'));
    await popup.close();
  }
  await page.locator('#close-dialog').click();
  await page.setViewportSize({ width: 1440, height: 1000 });
}

(async () => {
  await fs.mkdir(output, { recursive: true });
  const activities = JSON.parse(await fs.readFile(path.join(site, 'data/activities.json'), 'utf8'));
  const procedures = JSON.parse(await fs.readFile(path.join(site, 'data/procedures.json'), 'utf8'));
  const browser = await chromium.launch({ headless: true, channel: process.env.LAB_DASHBOARD_BROWSER_CHANNEL || 'msedge' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  page.on('pageerror', error => report.page_errors.push({ activity: currentActivity, error: String(error) }));
  page.on('requestfailed', request => report.failed_requests.push({ activity: currentActivity, url: request.url(), failure: request.failure() }));
  page.on('response', response => {
    if (response.status() >= 400 && response.url().startsWith(base) && !response.url().endsWith('/favicon.ico')) {
      report.http_errors.push({ activity: currentActivity, url: response.url(), status: response.status() });
    }
  });
  try {
    await comparePublishedFiles(context);
    await page.goto(base, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.getByRole('heading', { name: '탐구활동 1,276건', exact: true }).waitFor();
    for (const [index, activity] of activities.entries()) {
      await openActivity(page, activity);
      await readProcedure(page, activity, procedures[activity.id]);
      await page.locator('#close-dialog').click();
      if ((index + 1) % 100 === 0) {
        console.log(`PASS live activity details: ${index + 1}/${activities.length}`);
        await saveReport();
      }
    }
    assert.equal(report.activities.length, 1276);
    const expectedImages = Object.values(procedures).flatMap(groups => (groups || []).flatMap(group => group.figures || [])).length;
    assert.equal(report.image_checks.length, expectedImages);
    assert.equal(new Set(report.image_checks.map(item => item.file)).size, expectedImages);
    for (const [id, label] of [['activity_0210', 'refraction'], ['ybm_k8_0008', 'ybm-properties'], ['donga_IS2_005', 'donga-biodiversity']]) {
      await responsiveProof(page, activities.find(activity => activity.id === id), label);
    }
    assert.deepEqual(report.page_errors, []);
    assert.deepEqual(report.http_errors, []);
    assert.deepEqual(report.failed_requests, []);
    report.status = 'passed';
    report.counts = {
      files: report.files.length, activity_details: report.activities.length,
      held: report.activities.filter(item => item.held).length, decoded_images: report.image_checks.length,
      responsive_cases: report.responsive_checks.length,
    };
    console.log(JSON.stringify({ status: report.status, counts: report.counts, output }, null, 2));
  } catch (error) {
    report.status = 'failed';
    report.failure = { activity: currentActivity, url: page.url(), error: String(error), stack: error.stack };
    if (error instanceof AggregateError) report.failure.errors = error.errors.map(item => String(item));
    await page.screenshot({ path: path.join(output, 'failure.png') }).catch(() => {});
    throw error;
  } finally {
    report.finished_at = new Date().toISOString();
    await saveReport();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
