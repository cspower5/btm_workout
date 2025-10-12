const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const url = process.env.TEST_URL || 'http://192.168.40.88:5174/btm_workout/';
  const outDir = path.resolve('../../artifacts/e2e_smoke_prod');
  fs.mkdirSync(outDir, { recursive: true });
  try {
    const browser = await puppeteer.launch({ args: ['--no-sandbox','--disable-setuid-sandbox'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 390, height: 844 });
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    const html = await page.content();
    fs.writeFileSync(path.join(outDir, 'page.html'), html, 'utf8');
    await page.screenshot({ path: path.join(outDir, 'page.png'), fullPage: true });
    console.log('Saved artifacts to', outDir);
    await browser.close();
  } catch (e) {
    console.error('Smoke e2e failed:', e);
    process.exit(2);
  }
})();
