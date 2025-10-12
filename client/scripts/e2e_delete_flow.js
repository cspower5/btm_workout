import puppeteer from 'puppeteer';
import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';

async function run() {
  const url = process.env.TEST_URL || 'http://127.0.0.1:5174/btm_workout/';
  const apiBase = process.env.API_BASE || 'http://127.0.0.1:5000';
  const outDir = path.resolve('../../artifacts/e2e_delete');
  fs.mkdirSync(outDir, { recursive: true });

  // Seed a body part and an exercise via API
  await fetch(`${apiBase}/api/v1/add_body_part`, { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify({ name: 'e2e-test-bp' }) });
  await fetch(`${apiBase}/api/v1/insert_exercise`, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ exercise_name: 'E2E Test', body_part: 'e2e-test-bp', equipment: 'none', target: 'test', instructions: 'none' }) });

  const browser = await puppeteer.launch({ args: ['--no-sandbox','--disable-setuid-sandbox','--disable-web-security','--user-data-dir=/tmp/puppeteer_dev_profile'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844 });

  // Log console messages from the page to help debug API endpoint usage
  page.on('console', msg => {
    try {
      const args = msg.args ? msg.args.map(a => a.toString()).join(' ') : msg.text();
      console.log('PAGE_CONSOLE:', args);
    } catch (e) {
      console.log('PAGE_CONSOLE (unserializable)');
    }
  });

  // Log network requests and responses to see what API calls the client makes
  page.on('request', req => {
    if (req.url().includes('/api/v1/')) console.log('REQ ->', req.method(), req.url());
  });
  page.on('response', async res => {
    try {
      if (res.url().includes('/api/v1/')) {
        const status = res.status();
        let text = '';
        try { text = await res.text(); } catch (e) { text = '<no-body>'; }
        console.log('RESP <-', res.status(), res.url(), text.slice(0,200));
      }
    } catch (e) {
      console.warn('Error logging response', e);
    }
  });

  // Inject a small override so the client picks the test API during bootstrap.
  // This sets window.__TEST_API_BASE__ and also overrides location.hostname check
  // by providing a small stub before the app's scripts run.
  await page.goto('about:blank');
  await page.evaluateOnNewDocument((base) => {
    try {
      Object.defineProperty(window, '__TEST_API_BASE__', { value: base, writable: false });
      // For code that reads window.location.hostname, nothing to change here.
      // But expose a global var the app could use if present.
    } catch (e) {
      // ignore
    }
  }, apiBase);

  await page.goto(url, { waitUntil: 'networkidle2' });

  // Navigate to Manage Body Parts via hash route directly
  await page.goto(url + '#/manage-body-parts', { waitUntil: 'networkidle2' });
  // Wait for the manage container or item list to appear
  await page.waitForSelector('.manage-container, .item-list', { timeout: 5000 }).catch(() => {});
  // Dump page HTML for debugging
  const pageHtml = await page.content();
  fs.writeFileSync(path.join(outDir, 'before_delete.html'), pageHtml, 'utf8');
  // Capture screenshot
  await page.screenshot({ path: path.join(outDir, 'before_delete.png'), fullPage: true });

  // Save visible item texts for debugging
  const itemTexts = await page.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.item-list-item'));
    return nodes.map(n => {
      const span = n.querySelector('span');
      const btn = n.querySelector('button');
      return `${span ? span.textContent.trim() : '<no-span>'}||${btn ? 'HAS_BUTTON' : 'NO_BUTTON'}`;
    });
  });
  fs.writeFileSync(path.join(outDir, 'items.txt'), itemTexts.join('\n'), 'utf8');

  // Find the list items and look for the one that contains our body part name.
  const items = await page.$$('.item-list-item');
  let found = false;
  for (const item of items) {
    try {
      const span = await item.$('span');
      const text = await page.evaluate((s) => s && s.textContent && s.textContent.trim(), span);
      if (text === 'e2e-test-bp') {
        const btn = await item.$('button');
        if (btn) {
          page.on('dialog', async dialog => { await dialog.accept(); });
          try {
            await btn.click({ delay: 50 });
          } catch (clickErr) {
            console.warn('click failed, trying evaluate click', clickErr);
            await page.evaluate((el) => el && el.click(), btn).catch(() => {});
          }
          await page.waitForTimeout ? await page.waitForTimeout(800) : await page.waitForFunction('true', { timeout: 800 }).catch(() => {});
          await page.screenshot({ path: path.join(outDir, 'after_delete.png'), fullPage: true });
          found = true;
          break;
        }
      }
    } catch (e) {
      // ignore per-item errors and continue
      console.warn('item check error', e);
    }
  }
  if (!found) console.log('Delete button not found on page');

  await browser.close();
  console.log('E2E flow done; artifacts in', outDir);
}

run().catch(e => { console.error(e); process.exit(1); });
