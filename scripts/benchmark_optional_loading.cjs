// Compare immutable Git snapshots without modifying or publishing the website.
const { chromium } = require('playwright');
const { execFileSync } = require('node:child_process');
const { createServer } = require('node:http');
const { gzipSync } = require('node:zlib');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const output = process.env.LAB_DASHBOARD_BENCH_OUTPUT || path.join(root, 'output/validation/optional-performance-20260923');
const repetitions = Number(process.env.LAB_DASHBOARD_BENCH_RUNS || 10);
const revisions = { before: 'ce243d3', after: '1f7c071' };
const profiles = [
  { id: 'local', label: '로컬·속도 제한 없음', latency: 0, mbps: null, cpu: 1 },
  { id: 'broadband', label: '10 Mbps·지연 40 ms', latency: 40, mbps: 10, cpu: 1 },
  { id: 'limited', label: '1.6 Mbps·지연 100 ms·CPU 4배 제한', latency: 100, mbps: 1.6, cpu: 4 },
];
const git = (...args) => execFileSync('git', args, { cwd: root, maxBuffer: 30 * 1024 * 1024 });
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json' };
const snapshots = {};
for (const [version, revision] of Object.entries(revisions)) {
  const names = git('ls-tree', '-r', '--name-only', revision, 'site/dist').toString('utf8').trim().split(/\r?\n/);
  snapshots[version] = new Map(names.map(name => {
    const body = git('show', `${revision}:${name}`);
    return [name.slice('site/dist/'.length), { body, gzip: gzipSync(body, { level: 6 }), type: types[path.extname(name)] }];
  }));
}
for (const [name, record] of snapshots.before) {
  if (name.startsWith('data/')) assert.ok(record.body.equals(snapshots.after.get(name).body), `${name}: data differs`);
}

function instrument() {
  const result = window.__loadingBenchmark = { core: null, catalog: [] };
  let corePending = false;
  let activeCatalog = null;
  function inspect() {
    if (!result.core && !corePending
      && document.getElementById('load-status')?.hidden
      && document.getElementById('result-count')?.textContent === '탐구활동 1,276건'
      && document.querySelector('#results .activity-card')) {
      corePending = true;
      const domMs = performance.now();
      requestAnimationFrame(() => requestAnimationFrame(() => {
        result.core = { domMs, frameReadyMs: performance.now() };
      }));
    }
    if (activeCatalog && !activeCatalog.pending && document.getElementById('chemical-dialog')?.open
      && document.getElementById('chemical-count')?.textContent === '약품 177건') {
      const current = activeCatalog;
      current.pending = true;
      current.domMs = performance.now() - current.started;
      requestAnimationFrame(() => requestAnimationFrame(() => {
        current.frameReadyMs = performance.now() - current.started;
      }));
    }
  }
  new MutationObserver(inspect).observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
  document.addEventListener('click', event => {
    if (event.target.closest?.('#open-chemicals')) {
      activeCatalog = { started: performance.now(), pending: false };
      result.catalog.push(activeCatalog);
    }
  }, true);
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}
function stats(values) {
  return { median: median(values), min: Math.min(...values), max: Math.max(...values),
    q1: median([...values].sort((a, b) => a - b).slice(0, Math.floor(values.length / 2))),
    q3: median([...values].sort((a, b) => a - b).slice(Math.ceil(values.length / 2))) };
}

(async () => {
  await fs.mkdir(output, { recursive: true });
  const server = createServer((request, response) => {
    const [, version, ...parts] = new URL(request.url, 'http://localhost').pathname.split('/');
    const name = parts.join('/') || 'index.html';
    const record = snapshots[version]?.get(name);
    if (!record) { response.writeHead(404).end(); return; }
    // Pre-compression excludes server compression CPU time from the comparison.
    const compressed = /\bgzip\b/.test(request.headers['accept-encoding'] || '') && !!record.type;
    const body = compressed ? record.gzip : record.body;
    response.writeHead(200, { 'Content-Type': record.type ? `${record.type}; charset=utf-8` : 'application/octet-stream',
      'Content-Length': body.length, 'Cache-Control': 'no-store',
      ...(compressed ? { 'Content-Encoding': 'gzip', Vary: 'Accept-Encoding' } : {}) });
    response.end(body);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ headless: true, channel: process.env.LAB_DASHBOARD_BROWSER_CHANNEL || 'msedge' });
  const runs = [];
  const metadata = { measuredAt: new Date().toISOString(), browser: browser.version(), repetitions,
    revisions: Object.fromEntries(Object.entries(revisions).map(([k, v]) => [k, git('rev-parse', v).toString('utf8').trim()])),
    profiles, transport: 'Same local HTTP/1.1 server; pre-gzip level 6; cold cache and fresh context per navigation',
    endpoint: 'DOM ready and two requestAnimationFrame callbacks; proxy for frame readiness, not physical display paint or LCP',
    ordering: 'Alternate before/after within each paired repetition, one page at a time',
    scope: 'Controlled local comparison. Not production field measurements. No deployment performed.' };

  async function run(version, profile, pair, measured) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, serviceWorkers: 'block' });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.addInitScript(instrument);
    const cdp = await context.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
    await cdp.send('Network.emulateNetworkConditions', {
      offline: false, latency: profile.latency,
      downloadThroughput: profile.mbps == null ? -1 : profile.mbps * 1000000 / 8,
      uploadThroughput: profile.mbps == null ? -1 : profile.mbps * 1000000 / 8,
    });
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: profile.cpu });
    async function resources() {
      return page.evaluate(() => {
        const entries = [...performance.getEntriesByType('navigation'), ...performance.getEntriesByType('resource')]
          .filter(entry => new URL(entry.name).pathname.split('/').pop() !== 'favicon.ico');
        return entries.map(entry => ({ file: new URL(entry.name).pathname.split('/').pop() || 'index.html',
          url: entry.name, type: entry.initiatorType, encodedBytes: entry.encodedBodySize,
          decodedBytes: entry.decodedBodySize, transferBytes: entry.transferSize,
          startMs: entry.startTime, endMs: entry.responseEnd }));
      });
    }
    try {
      await page.goto(`${origin}/${version}/`, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => !!window.__loadingBenchmark.core);
      // Settle all initial transfers before counting bytes; never click optional UI yet.
      await page.waitForLoadState('networkidle');
      const initial = await resources();
      const initialJson = initial.filter(entry => entry.file.endsWith('.json')).map(entry => entry.file).sort();
      assert.deepEqual(initialJson, version === 'before'
        ? ['achievements.json', 'activities.json', 'chemicals.json', 'materials.json']
        : ['achievements.json', 'activities.json']);
      await page.locator('#open-chemicals').click();
      await page.waitForFunction(() => window.__loadingBenchmark.catalog[0]?.frameReadyMs != null);
      await page.waitForLoadState('networkidle');
      const afterCatalog = await resources();
      await page.locator('#chemical-close').click();
      await page.locator('#open-chemicals').click();
      await page.waitForFunction(() => window.__loadingBenchmark.catalog[1]?.frameReadyMs != null);
      const marks = await page.evaluate(() => window.__loadingBenchmark);
      assert.deepEqual(errors, []);
      const sum = (entries, field) => entries.reduce((n, entry) => n + entry[field], 0);
      const result = { version, profile: profile.id, pair, core: marks.core,
        firstChemicalMs: marks.catalog[0].frameReadyMs, secondChemicalMs: marks.catalog[1].frameReadyMs,
        firstChemicalDomMs: marks.catalog[0].domMs,
        initialRequests: initial.length, initialJsonRequests: initialJson.length,
        initialEncodedBytes: sum(initial, 'encodedBytes'), initialDecodedBytes: sum(initial, 'decodedBytes'),
        afterChemicalEncodedBytes: sum(afterCatalog, 'encodedBytes'),
        initialResources: initial, afterChemicalResources: afterCatalog, errors };
      if (measured) {
        runs.push(result);
        await fs.writeFile(path.join(output, 'raw-runs.json'), JSON.stringify({ metadata, runs }, null, 2));
        console.log(JSON.stringify({ profile: profile.id, pair, version,
          coreMs: Math.round(marks.core.frameReadyMs), firstChemicalMs: Math.round(result.firstChemicalMs),
          initialGzipBytes: result.initialEncodedBytes }));
      }
    } finally { await context.close(); }
  }

  try {
    // Warm the browser process/JIT; discard these runs and still use cold page caches.
    await run('before', profiles[0], -1, false);
    await run('after', profiles[0], -1, false);
    for (const profile of profiles) {
      for (let pair = 0; pair < repetitions; pair++) {
        const order = pair % 2 ? ['after', 'before'] : ['before', 'after'];
        for (const version of order) await run(version, profile, pair, true);
      }
    }
    const summary = profiles.map(profile => {
      const before = runs.filter(r => r.profile === profile.id && r.version === 'before');
      const after = runs.filter(r => r.profile === profile.id && r.version === 'after');
      const describe = rows => ({ coreMs: stats(rows.map(r => r.core.frameReadyMs)),
        firstChemicalMs: stats(rows.map(r => r.firstChemicalMs)), secondChemicalMs: stats(rows.map(r => r.secondChemicalMs)),
        initialRequests: stats(rows.map(r => r.initialRequests)), initialJsonRequests: stats(rows.map(r => r.initialJsonRequests)),
        initialEncodedBytes: stats(rows.map(r => r.initialEncodedBytes)), initialDecodedBytes: stats(rows.map(r => r.initialDecodedBytes)),
        afterChemicalEncodedBytes: stats(rows.map(r => r.afterChemicalEncodedBytes)) });
      const left = describe(before), right = describe(after);
      const deltas = before.map(r => r.core.frameReadyMs - after.find(a => a.pair === r.pair).core.frameReadyMs);
      return { profile, before: left, after: right, pairedCoreSavingsMs: stats(deltas),
        pairsFaster: deltas.filter(n => n > 0).length,
        coreMedianReductionPercent: 100 * (1 - right.coreMs.median / left.coreMs.median),
        initialEncodedReductionPercent: 100 * (1 - right.initialEncodedBytes.median / left.initialEncodedBytes.median) };
    });
    await fs.writeFile(path.join(output, 'summary.json'), JSON.stringify({ metadata, summary }, null, 2));
    console.log(JSON.stringify({ status: 'passed', runs: runs.length, output, summary }, null, 2));
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
