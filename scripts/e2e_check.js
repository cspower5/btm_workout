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
      // Prefer full puppeteer (bundled Chromium) so an executable is available;
      // fall back to puppeteer-core only if full puppeteer isn't installed.
      let puppeteer = null;
      if (await (async ()=>{ try{ await import('puppeteer'); return true; }catch(e){ return false; } })()) {
        puppeteer = await loadModule('puppeteer');
        console.log('Using full puppeteer');
      } else if (await (async ()=>{ try{ await import('puppeteer-core'); return true; }catch(e){ return false; } })()) {
        puppeteer = await loadModule('puppeteer-core');
        console.log('Using puppeteer-core');
      } else {
        throw new Error('Neither puppeteer nor puppeteer-core is installed');
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
    // Ensure any early in-page requests (fetch/XHR) that target the production
    // API host are rewritten to point at the configured TEST API. Some apps
    // issue requests as soon as the JS bundle is parsed; rewriting at
    // evaluateOnNewDocument guarantees those early requests go to the mock
    // (or TEST_API) and avoids CORS failures.
    try {
      // Injected before any page script runs. Log so we can detect the injection
      // in client console logs produced during CI runs.
      await page.evaluateOnNewDocument((testApi) => {
        try {
          console.log('E2E injection active (rewriting early fetch/XHR to test API):', testApi);
        } catch (e) { /* ignore logging errors */ }

        try {
          // Rewrite window.fetch (handle string, Request, and RequestInfo forms)
          const _origFetch = window.fetch;
          window.fetch = function(resource, init) {
            try {
              let urlStr;
              if (typeof resource === 'string') urlStr = resource;
              else if (resource && typeof resource === 'object' && resource.url) urlStr = resource.url;
              else urlStr = String(resource);
              if (!urlStr) return _origFetch.call(this, resource, init);
              const u = new URL(urlStr, location.href);
              if (u.hostname === 'btm-workout.onrender.com') {
                const newUrl = testApi + u.pathname + u.search;
                if (typeof resource === 'string') resource = newUrl;
                else if (resource && resource.url) resource = new Request(newUrl, resource);
                else resource = newUrl;
              }
            } catch (e) { /* best-effort: fall back to original */ }
            return _origFetch.call(this, resource, init);
          };

          // Override XMLHttpRequest.open at the prototype level so early XHRs are rewritten
          try {
            const origOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url) {
              try {
                const u = new URL(url, location.href);
                if (u.hostname === 'btm-workout.onrender.com') {
                  url = testApi + u.pathname + u.search;
                }
              } catch (e) { /* ignore */ }
              return origOpen.apply(this, arguments);
            };
          } catch (xhrErr) {
            /* ignore */
          }
        } catch (e) { /* ignore injection errors */ }
      }, API);
    } catch (e) {
      console.log('evaluateOnNewDocument injection failed:', e && e.message ? e.message : e);
    }
    page.setDefaultTimeout(30000);
    // Attach console/response/requestfailed handlers immediately so we capture
    // any runtime errors during the initial page load (module execution), not
    // just after navigation.
    try {
      const _fs = require('fs');
      page.on('console', msg => {
        try {
          const text = typeof msg === 'string' ? msg : (msg && typeof msg.text === 'function' ? msg.text() : String(msg));
          const entry = { time: new Date().toISOString(), type: 'page-console', text };
          try { _fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch (e) {}
          console.log('PAGE LOG:', text);
        } catch (e) { console.log('PAGE LOG handler error:', e && e.message ? e.message : e); }
      });
      page.on('pageerror', err => {
        try {
          const msg = err && err.message ? err.message : String(err);
          const entry = { time: new Date().toISOString(), type: 'page-error', message: msg, stack: err && err.stack ? err.stack : null };
          try { _fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch (e) {}
          console.log('PAGE ERROR:', msg);
        } catch (e) { console.log('PAGE ERROR handler error:', e && e.message ? e.message : e); }
      });
      page.on('requestfailed', req => {
        try {
          const failure = req.failure();
          const entry = { time: new Date().toISOString(), type: 'request-failed', url: req.url(), method: req.method(), failure: failure ? failure.errorText || failure : null };
          try { _fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch (e) {}
          console.log('REQUEST FAILED:', req.url(), failure && failure.errorText ? failure.errorText : failure);
        } catch (e) { console.log('requestfailed handler error:', e && e.message ? e.message : e); }
      });
      page.on('response', async resp => {
        try {
          const url = resp.url();
          const req = resp.request();
          const rtype = req.resourceType();
          if (url.includes('/assets/') || rtype === 'script' || url.includes('/api/')) {
            const status = resp.status();
            const headers = resp.headers ? resp.headers : {};
            let bodySnippet = null;
            try {
              const ct = headers['content-type'] || headers['Content-Type'] || '';
              if (ct.includes('application/json') || ct.includes('application/javascript') || ct.includes('text/') || ct.includes('css')) {
                const text = await resp.text();
                bodySnippet = text && text.length > 2000 ? text.slice(0, 2000) : text;
              }
            } catch (e) {}
            const entry = { time: new Date().toISOString(), type: 'response', url, resourceType: rtype, status, headers, bodySnippet };
            try { _fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch (e) {}
            console.log('RESPONSE:', status, url, rtype);
          }
        } catch (e) { console.log('response handler error:', e && e.message ? e.message : e); }
      });
    } catch (logErr) {
      console.log('Failed to attach early page log handlers:', logErr && logErr.message ? logErr.message : logErr);
    }
    // Rewrite requests that start with /btm_workout to remove the base prefix so
    // the built assets (which are referenced with an absolute '/btm_workout/...'
    // path) resolve when we serve the dist folder at the server root.
    try {
      await page.setRequestInterception(true);
      page.on('request', async req => {
        try {
          const reqUrl = new URL(req.url());

          // If the page requests any /api/* path, proxy it via axios so the browser
          // doesn't run into CORS issues. The built frontend may call an external
          // host (for example https://btm-workout.onrender.com); proxying here
          // allows the E2E runner to forward that request to the configured
          // TEST_API (often a local mock) and return the response to the page.
          if (reqUrl.pathname.startsWith('/api/')) {
            try {
              const method = req.method();
              const headers = req.headers();
              const postData = req.postData();
              // Handle CORS preflight directly
              if (method === 'OPTIONS') {
                const preHeaders = {
                  'access-control-allow-origin': '*',
                  'access-control-allow-methods': 'GET,POST,PUT,DELETE,OPTIONS',
                  'access-control-allow-headers': headers && headers['access-control-request-headers'] ? headers['access-control-request-headers'] : '*',
                };
                return req.respond({ status: 204, headers: preHeaders, body: '' });
              }
                // Build the proxied URL against the configured API base so any
                // original host in the frontend code is ignored and the mock/local
                // API is always used in CI/local runs.
                const proxiedUrl = `${API}${reqUrl.pathname}${reqUrl.search}`;
                const axiosOpts = { method, url: proxiedUrl, headers: headers || {}, data: postData || undefined, timeout: 10000 };
                // Write an immediate, synchronous log entry so we always record the
                // proxied target even if axios throws or async logging fails.
                try {
                  const fs = require('fs');
                  const preEntry = { time: new Date().toISOString(), type: 'api-proxy-pre', method, requestedUrl: req.url(), proxiedUrl, requestHeaders: headers || {}, requestBody: postData || null };
                  try { fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(preEntry) + '\n'); } catch(e){}
                } catch(e) { /* ignore */ }

                let proxied;
                try {
                  proxied = await axios(axiosOpts);
                } catch (axiosErr) {
                  // log detailed error synchronously for CI artifact capture
                  try {
                    const fs = require('fs');
                    const errEntry = { time: new Date().toISOString(), type: 'api-proxy-error', method, requestedUrl: req.url(), proxiedUrl, message: axiosErr && axiosErr.message ? axiosErr.message : String(axiosErr), status: axiosErr && axiosErr.response ? axiosErr.response.status : null, data: axiosErr && axiosErr.response ? axiosErr.response.data : null };
                    try { fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(errEntry) + '\n'); } catch(e){}
                  } catch(e){}
                  console.log('API proxy error for', req.url(), axiosErr && axiosErr.message ? axiosErr.message : axiosErr);
                  // If the upstream returned a response (like 404), forward that
                  // status/body back to the browser with permissive CORS headers so
                  // the SPA can handle the error (and avoid opaque network failures).
                  try {
                    const resp = axiosErr && axiosErr.response ? axiosErr.response : null;
                    const fs = require('fs');
                    const status = resp && resp.status ? resp.status : 502;
                    const data = resp && resp.data ? resp.data : { error: axiosErr && axiosErr.message ? axiosErr.message : 'Upstream error' };
                    const body = typeof data === 'string' ? data : JSON.stringify(data);
                    const respHeaders = Object.assign({}, resp && resp.headers ? resp.headers : {});
                    if (!respHeaders['content-type']) respHeaders['content-type'] = 'application/json';
                    respHeaders['access-control-allow-origin'] = '*';
                    respHeaders['access-control-expose-headers'] = '*';
                    respHeaders['access-control-allow-credentials'] = 'true';
                    return req.respond({ status, headers: respHeaders, body });
                  } catch (respErr) {
                    // if responding fails, abort to avoid hanging
                    return req.abort();
                  }
                }

                const body = typeof proxied.data === 'string' ? proxied.data : JSON.stringify(proxied.data);
                const respHeaders = Object.assign({}, proxied.headers || {});
                // Write a compact proxy log entry to /tmp/e2e_console_log.txt for CI artifact debugging
                try {
                  const fs = require('fs');
                  const entry = {
                      time: new Date().toISOString(),
                      type: 'api-proxy',
                      method,
                      // log the original requested URL and the proxied target
                      requestedUrl: req.url(),
                      proxiedUrl,
                      requestHeaders: headers || {},
                      requestBody: postData || null,
                      responseStatus: proxied.status || 200,
                      responseHeaders: proxied.headers || {},
                      responseBody: proxied.data || null
                    };
                  try { fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch(e){ /* best-effort logging */ }
                } catch(e) {
                  // ignore logging errors
                }
              // Ensure content-type is JSON when appropriate
              if (!respHeaders['content-type']) respHeaders['content-type'] = 'application/json';
              // Add permissive CORS headers so the page can read the response in CI
              respHeaders['access-control-allow-origin'] = '*';
              respHeaders['access-control-expose-headers'] = '*';
              respHeaders['access-control-allow-credentials'] = 'true';
              return req.respond({ status: proxied.status || 200, headers: respHeaders, body });
            } catch (proxyErr) {
              console.log('API proxy error for', req.url(), proxyErr && proxyErr.message ? proxyErr.message : proxyErr);
              return req.abort();
            }
          }

          // Rewrite asset requests that include the /btm_workout prefix so the
          // server (which is serving the dist folder at root) can still serve
          // the absolute asset URLs emitted by the build.
          if (reqUrl.pathname.startsWith('/btm_workout/')) {
            const newPath = reqUrl.pathname.replace('/btm_workout', '');
            const newUrl = `${reqUrl.protocol}//${reqUrl.host}${newPath}${reqUrl.search}`;
            return req.continue({ url: newUrl });
          }
        } catch (e) {
          // If URL parsing or other handling fails, continue the request unchanged
          console.log('request interception error:', e && e.message ? e.message : e);
        }
        return req.continue();
      });
    } catch (interceptErr) {
      // Some browser/platform combinations may not support interception; ignore
      // and proceed (assets may 404 in that case).
      console.log('Request interception not available:', interceptErr && interceptErr.message ? interceptErr.message : interceptErr);
    }
    // Navigate to the base page and then click the internal hash link for
    // the workout route. Some HTTP servers/proxies may mis-handle URLs that
    // include fragments when sent by certain tooling, so drive the app via
    // user-like interactions instead of navigating with a URL fragment.
    await page.goto(BASE, { waitUntil: 'networkidle0' });
    // Click the 'Generate Workout' nav link which uses '#/workout'
    try {
      await page.waitForSelector('a[href="#/workout"]', { timeout: 10000 });
      await page.click('a[href="#/workout"]');
    } catch (navErr) {
      // If nav link isn't present, set the hash directly as a fallback
      await page.evaluate(() => { location.hash = '#/workout'; });
    }
  // Allow SPA to render
  await new Promise((resolve) => setTimeout(resolve, 1000));

    // Attach console and error listeners to capture client-side errors for debugging
    // These handlers write compact JSON-line entries to /tmp/e2e_console_log.txt
    // so CI artifact uploads include useful runtime diagnostics.
    try {
      const _fs = require('fs');
      page.on('console', msg => {
        try {
          const text = typeof msg === 'string' ? msg : (msg && typeof msg.text === 'function' ? msg.text() : String(msg));
          const entry = { time: new Date().toISOString(), type: 'page-console', text };
          try { _fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch (e) {}
          console.log('PAGE LOG:', text);
        } catch (e) {
          console.log('PAGE LOG handler error:', e && e.message ? e.message : e);
        }
      });
      page.on('pageerror', err => {
        try {
          const msg = err && err.message ? err.message : String(err);
          const entry = { time: new Date().toISOString(), type: 'page-error', message: msg, stack: err && err.stack ? err.stack : null };
          try { _fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch (e) {}
          console.log('PAGE ERROR:', msg);
        } catch (e) {
          console.log('PAGE ERROR handler error:', e && e.message ? e.message : e);
        }
      });

      // Capture failed network requests (failed to load scripts/assets or network errors)
      page.on('requestfailed', req => {
        try {
          const failure = req.failure();
          const entry = { time: new Date().toISOString(), type: 'request-failed', url: req.url(), method: req.method(), failure: failure ? failure.errorText || failure : null };
          try { _fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch (e) {}
          console.log('REQUEST FAILED:', req.url(), failure && failure.errorText ? failure.errorText : failure);
        } catch (e) {
          console.log('requestfailed handler error:', e && e.message ? e.message : e);
        }
      });

      // Log responses for assets, scripts, and API endpoints so we can see status codes
      page.on('response', async resp => {
        try {
          const url = resp.url();
          const req = resp.request();
          const rtype = req.resourceType();
          if (url.includes('/assets/') || rtype === 'script' || url.includes('/api/')) {
            const status = resp.status();
            const headers = resp.headers ? resp.headers : {};
            let bodySnippet = null;
            try {
              // only attempt text for JSON or JS/CSS small files
              const ct = headers['content-type'] || headers['Content-Type'] || '';
              if (ct.includes('application/json') || ct.includes('application/javascript') || ct.includes('text/') || ct.includes('css')) {
                const text = await resp.text();
                bodySnippet = text && text.length > 2000 ? text.slice(0, 2000) : text;
              }
            } catch (e) {
              // ignore body read errors
            }
            const entry = { time: new Date().toISOString(), type: 'response', url, resourceType: rtype, status, headers, bodySnippet };
            try { _fs.appendFileSync('/tmp/e2e_console_log.txt', JSON.stringify(entry) + '\n'); } catch (e) {}
            console.log('RESPONSE:', status, url, rtype);
          }
        } catch (e) {
          console.log('response handler error:', e && e.message ? e.message : e);
        }
      });
    } catch (logErr) {
      // If require('fs') fails for some reason, still attach minimal handlers
      page.on('console', msg => console.log('PAGE LOG:', typeof msg === 'string' ? msg : (msg && msg.text ? msg.text() : msg)));
      page.on('pageerror', err => console.log('PAGE ERROR:', err && err.message ? err.message : err));
      page.on('requestfailed', req => console.log('REQUEST FAILED:', req.url(), req.failure && req.failure() && req.failure().errorText));
    }

    // Take a snapshot of the current HTML and a screenshot to help debug hydration issues
    // and persist them to /tmp so the workflow can upload them as artifacts.
    const htmlSnapshot = await page.content();
    try {
      // write HTML snapshot and prepare a console-log file to /tmp so they can be uploaded
      const fs = await loadModule('fs');
      try { fs.writeFileSync('/tmp/e2e_page_snapshot.html', htmlSnapshot, 'utf8'); } catch(e){ console.log('Failed to write HTML snapshot:', e && e.message ? e.message : e); }
      try {
        // Only create an empty console log file if it doesn't already exist so
        // earlier proxy logs (written during page load) are preserved.
        if (!fs.existsSync('/tmp/e2e_console_log.txt')) {
          fs.writeFileSync('/tmp/e2e_console_log.txt', '', 'utf8');
        }
      } catch(e){ /* best-effort */ }
    } catch(e) {
      console.log('Snapshot write preparation failed:', e && e.message ? e.message : e);
    }
    try {
      await page.screenshot({ path: '/tmp/e2e_page_snapshot.png', fullPage: true });
      console.log('Saved page snapshot and screenshot to /tmp');
    } catch (screenshotErr) {
      console.log('Screenshot failed:', screenshotErr && screenshotErr.message ? screenshotErr.message : screenshotErr);
    }

    // 3) Select the requested body part in the dropdown and click Generate
    // Wait longer for the SPA to hydrate and render the select dropdown
    try {
      // Wait for the select to exist and have at least one option. This avoids
      // races where the SPA has mounted but data hasn't populated the select.
      await page.waitForSelector('select', { timeout: 20000 });
      // wait until the select has at least one non-empty option
      await page.waitForFunction(() => {
        const sel = document.querySelector('select');
        return sel && sel.options && sel.options.length > 0 && Array.from(sel.options).some(o => o.value && o.value.trim().length>0);
      }, { timeout: 20000 });
    } catch (waitErr) {
      console.log('Selector wait failed; dumping HTML snapshot for debugging:\n', (htmlSnapshot || '').slice(0, 2000));
      // persist the page HTML again for artifact capture
      try { const fs = await loadModule('fs'); fs.appendFileSync('/tmp/e2e_console_log.txt', '\nSelector wait failed\n', 'utf8'); } catch(e){}
      throw waitErr;
    }
    // Robustly select the option by matching value or visible text case-insensitively
    await page.evaluate((bp) => {
      const sel = document.querySelector('select');
      if (!sel) return;
      const target = bp ? bp.toString().toLowerCase() : '';
      const options = Array.from(sel.options);
      const match = options.find(o => (o.value && o.value.toLowerCase() === target) || (o.text && o.text.toLowerCase() === target));
      if (match) {
        sel.value = match.value;
        sel.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }, BODY_PART);

    // Set number input to 3
    await page.evaluate(() => {
      const n = document.querySelector('input[type=number]');
      if (n) n.value = 3;
    });

    // Click Generate Workout button
    await page.click('button');

  // Wait for results to appear; cards have .exercise-card. Increase timeout
  // to be more tolerant on busy CI runners.
  await page.waitForSelector('.exercise-card', { timeout: 10000 });

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
    try { const fs = await loadModule('fs'); fs.appendFileSync('/tmp/e2e_console_log.txt', 'E2E check passed.\n', 'utf8'); } catch(e){}
    await browser.close();
    process.exit(0);
  } catch (err) {
    // Capture page HTML and console logs if possible to /tmp for artifact upload
    try {
      const fs = await loadModule('fs');
      try { const htmlNow = await page.content(); fs.writeFileSync('/tmp/e2e_page_snapshot_error.html', htmlNow, 'utf8'); } catch(e){}
      try { fs.appendFileSync('/tmp/e2e_console_log.txt', `E2E check failed: ${err && err.message ? err.message : err}\n`, 'utf8'); } catch(e){}
    } catch(e){ /* ignore write errors */ }
    console.error('E2E check failed:', err && err.message ? err.message : err);
    process.exit(2);
  }
})();
