const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

(async () => {
  const OUT_DIR = path.resolve(process.cwd(), 'gh-artifacts');
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  const outPng = path.join(OUT_DIR, 'debug-mobile-screenshot.png');
  const outHtml = path.join(OUT_DIR, 'debug-page-snapshot.html');

  const url = process.env.TARGET_URL || 'http://localhost:5174/';
  console.log('Debug capture opening URL:', url);

  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox','--disable-setuid-sandbox'] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 375, height: 812, deviceScaleFactor: 2 });
    await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1');

    const consoleLogFile = path.join(OUT_DIR, 'debug-console.txt');
    fs.writeFileSync(consoleLogFile, `Debug capture: ${new Date().toISOString()}\n`);

    page.on('console', msg => {
      try {
        const text = msg && msg.text ? msg.text() : String(msg);
        fs.appendFileSync(consoleLogFile, `[console] ${text}\n`);
      } catch (e) {}
    });
    page.on('pageerror', err => {
      try { fs.appendFileSync(consoleLogFile, `[pageerror] ${err && err.message ? err.message : err}\n${err && err.stack ? err.stack : ''}\n`); } catch(e){}
    });
    page.on('response', async resp => {
      try {
        const url = resp.url();
        const status = resp.status();
        fs.appendFileSync(consoleLogFile, `[response] ${status} ${url}\n`);
      } catch(e){}
    });

    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    await page.evaluate(() => window.scrollTo(0, 0));
    // wait briefly for hydration/render
    await new Promise(r => setTimeout(r, 1200));

    const html = await page.content();
    fs.writeFileSync(outHtml, html, 'utf8');
    await page.screenshot({ path: outPng, fullPage: true });

    console.log('Wrote debug files:', outPng, outHtml, consoleLogFile);
  } catch (err) {
    console.error('Debug capture failed:', err);
    process.exitCode = 2;
  } finally {
    await browser.close();
  }
})();
