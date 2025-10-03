import { createRequire } from 'module';
const require = createRequire(import.meta.url);

async function loadModule(name) {
  try {
    const mod = await import(name);
    return mod && (mod.default ?? mod);
  } catch (err) {
    try { return require(name); } catch (e) { throw err; }
  }
}

const puppeteer = await (async ()=>{ try{ await import('puppeteer'); return await loadModule('puppeteer'); }catch(e){ return await loadModule('puppeteer-core'); } })();
const BASE = process.env.TEST_BASE || 'https://cspower5.github.io/btm_workout';

(async ()=>{
  const browser = await puppeteer.launch({ args: ['--no-sandbox','--disable-setuid-sandbox'], headless: true });
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err && err.message));

  // capture failed requests
  await page.setRequestInterception(true);
  page.on('request', req => req.continue());
  page.on('requestfailed', r => console.log('REQUEST FAILED:', r.url(), r.failure()?.errorText));

  // Load page and navigate to hash route
  await page.goto(BASE, { waitUntil: 'networkidle2' });
  // Navigate to add-exercise
  try {
    await page.click('a[href="#/add-exercise"]');
  } catch (e) {
    await page.evaluate(() => { location.hash = '#/add-exercise'; });
  }
  await new Promise(r => setTimeout(r, 1200));

  // Save snapshot
  const html = await page.content();
  await page.screenshot({ path: '/tmp/add_exercise_snapshot.png', fullPage: true });
  require('fs').writeFileSync('/tmp/add_exercise_snapshot.html', html, 'utf8');
  console.log('Saved /tmp/add_exercise_snapshot.*');

  // Inspect selects
  const selectInfo = await page.evaluate(() => {
    const selects = Array.from(document.querySelectorAll('select'));
    return selects.map(s => ({ name: s.name||s.id||null, options: Array.from(s.options).map(o=>({value:o.value, text:o.text})) }));
  });
  console.log('Selects on page:', JSON.stringify(selectInfo, null, 2));

  await browser.close();
  process.exit(0);
})().catch(err => { console.error('E2E add-ex error', err && err.message); process.exit(2); });
