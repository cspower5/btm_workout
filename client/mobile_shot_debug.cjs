const puppeteer = require('puppeteer');

(async () => {
  try {
    const out = '/tmp/mobile_debug_screenshot.png';
    const browser = await puppeteer.launch({ args: ['--no-sandbox','--disable-setuid-sandbox'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
    await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1');

    page.on('console', msg => {
      try { console.log('PAGE CONSOLE:', msg.type(), msg.text()); } catch(e){ console.log('PAGE CONSOLE ERR', e); }
    });
    page.on('pageerror', err => console.log('PAGE ERROR:', err && err.message));
    page.on('requestfailed', req => console.log('REQUEST FAILED:', req.url(), req.failure && req.failure().errorText));
    page.on('response', res => {
      const status = res.status();
      const url = res.url();
      const ct = res.headers()['content-type'] || '';
      if (status >= 400) console.log('BAD RESPONSE:', status, url);
      // also log if JS/CSS are unexpectedly HTML (like 200 but content-type text/html)
      if ((/\.js$|assets\//.test(url)) && ct.includes('text/html')) console.log('SUSPECT HTML RESPONSE FOR ASSET:', url, 'content-type', ct);
    });

    await page.goto('http://127.0.0.1:8081/btm_workout/', { waitUntil: 'networkidle2', timeout: 45000 });
    await page.screenshot({ path: out, fullPage: false });
    console.log('Saved debug screenshot to', out);
    await browser.close();
  } catch (e) {
    console.error('Error in debug shot:', e);
    process.exit(1);
  }
})();
