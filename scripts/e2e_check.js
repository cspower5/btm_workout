import { createRequire } from 'module';

// Load a module dynamically with fallbacks so the script works whether it's
// executed from the repo root or from the `client/` working directory in CI.
const require = createRequire(import.meta.url);
async function loadModule(name) {
  // Try dynamic ESM import first (works when package is resolvable normally)
  try {
    const mod = await import(name);
    return mod && (mod.default ?? mod);
  } catch (err) {
    // Fall back to requiring from client/node_modules (common CI layout)
    try {
      return require(`./client/node_modules/${name}`);
    } catch (err2) {
      // As a last resort, try a plain require (may work if installed at root)
      try {
        return require(name);
      } catch (err3) {
        // propagate the original error for clearer diagnostics
        throw err;
      }
    }
  }
}

const BASE = process.env.TEST_BASE || 'http://localhost:5174/btm_workout';
const API = process.env.TEST_API || 'https://btm-workout.onrender.com';
const BODY_PART = process.env.BODY_PART || process.env.TARGET_BODY_PART || 'legs';
const NUM_EX = parseInt(process.env.NUM_EXERCISES || process.env.NUM_EX || '3', 10) || 3;

// Convert the original top-level logic to a function so we can load modules
// at runtime and provide robust fallbacks.
(async () => {
  try {
      // Prefer puppeteer-core to avoid bringing Chromium; fall back to puppeteer.
      let puppeteer = null;
      if (await (async ()=>{ try{ await import('puppeteer-core'); return true; }catch(e){ return false; } })()) {
        puppeteer = await loadModule('puppeteer-core');
        console.log('Using puppeteer-core');
      } else {
        puppeteer = await loadModule('puppeteer');
        console.log('Using full puppeteer');
      }
      const axios = await loadModule('axios');

    console.log(`Running E2E check for body part='${BODY_PART}', num_exercises=${NUM_EX}, base=${BASE}`);
    // 1) Call the API to get a sample workout for the requested body part
    const apiResp = await axios.post(`${API}/api/v1/get_random_exercises`, { bodyPart: BODY_PART, num_exercises: NUM_EX }, { timeout: 10000 });
    console.log('API returned', apiResp.data.length, 'items');

    // Inspect whether any returned doc includes reps or sets
    const anyReps = apiResp.data.some(d => d.reps != null);
    const anySets = apiResp.data.some(d => d.sets != null);
    console.log('API has reps?', anyReps, 'sets?', anySets);

    // 2) Launch Puppeteer and load the GH Pages site
    // If Playwright has installed Chromium, use its executable to avoid a separate
    // Puppeteer Chromium download. Playwright stores browsers under ~/.cache/ms-playwright.
    let launchOpts = { args: ['--no-sandbox','--disable-setuid-sandbox'], headless: true };
    try {
      // try to find Playwright chromium
      const pwCache = process.env.HOME ? `${process.env.HOME}/.cache/ms-playwright` : null;
      if (pwCache) {
        // Look for chromium installation directory via Node FS only if exists
        const fs = await loadModule('fs');
        const chromiumDir = pwCache + '/chromium-1193';
        if (fs && fs.existsSync && fs.existsSync(chromiumDir)) {
          // find the executable inside the chromium dir
          const exe = require('path').join(chromiumDir, 'chrome-linux', 'chrome');
          launchOpts.executablePath = exe;
          console.log('Using Playwright Chromium at', exe);
        }
      }
    } catch (pwErr) {
      // ignore; fallback to puppeteer's own download
      console.log('Playwright chromium not used:', pwErr && pwErr.message ? pwErr.message : pwErr);
    }

    const browser = await puppeteer.launch(launchOpts);
    const page = await browser.newPage();
    page.setDefaultTimeout(30000);
    // Navigate directly to the workout route (HashRouter uses #/workout)
    await page.goto(BASE + '/#/workout', { waitUntil: 'networkidle0' });

    // Attach console and error listeners to capture client-side errors for debugging
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err && err.message ? err.message : err));

    // Take a snapshot of the current HTML and a screenshot to help debug hydration issues
    const htmlSnapshot = await page.content();
    try {
      await page.screenshot({ path: '/tmp/e2e_page_snapshot.png', fullPage: true });
      console.log('Saved page snapshot and screenshot to /tmp');
    } catch (screenshotErr) {
      console.log('Screenshot failed:', screenshotErr && screenshotErr.message ? screenshotErr.message : screenshotErr);
    }

    // 3) Select 'legs' in the body part dropdown and click Generate
    // Wait longer for the SPA to hydrate and render the select dropdown
    try {
      await page.waitForSelector('select', { timeout: 15000 });
    } catch (waitErr) {
      console.log('Selector wait failed; dumping HTML snapshot for debugging:\n', htmlSnapshot.slice(0, 2000));
      throw waitErr;
    }
    await page.select('select', 'legs');

    // Set number input to 3
    await page.evaluate(() => {
      const n = document.querySelector('input[type=number]');
      if (n) n.value = 3;
    });

    // Click Generate Workout button
    await page.click('button');

    // Wait for results to appear; cards have .exercise-card
    await page.waitForSelector('.exercise-card', { timeout: 5000 });

    // 4) Inspect the first card for Reps/Sets nodes
    const cardInfo = await page.evaluate(() => {
      const card = document.querySelector('.exercise-card');
      if (!card) return { found: false };
      const name = card.querySelector('h3')?.textContent || null;
      const repsNode = Array.from(card.querySelectorAll('p')).find(p => p.textContent.trim().startsWith('Reps:'));
      const setsNode = Array.from(card.querySelectorAll('p')).find(p => p.textContent.trim().startsWith('Sets:'));
      return { found: true, name, hasReps: !!repsNode, hasSets: !!setsNode };
    });

    console.log('Rendered card info:', cardInfo);

    // 5) Assert: if API had no reps/sets, the rendered card should not have them
    if (!anyReps && cardInfo.hasReps) {
      throw new Error('UI rendered Reps but API returned no reps');
    }
    if (!anySets && cardInfo.hasSets) {
      throw new Error('UI rendered Sets but API returned no sets');
    }

    console.log('E2E check passed.');
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('E2E check failed:', err && err.message ? err.message : err);
    process.exit(2);
  }
})();
