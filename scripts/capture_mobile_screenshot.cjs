// scripts/capture_mobile_screenshot.cjs - CommonJS copy for environments where
// project package.json has "type": "module".
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

(async () => {
  const OUT_DIR = path.resolve(process.cwd(), 'gh-artifacts');
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  const outFile = path.join(OUT_DIR, 'mobile-screenshot.png');

  // Target: local server or GH Pages deploy
  const url = process.env.TARGET_URL || 'https://cspower5.github.io/btm_workout/';

  console.log('Opening URL:', url);
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // iPhone X-like viewport
    await page.setViewport({ width: 375, height: 812, deviceScaleFactor: 2 });

    // Mobile UA
    await page.setUserAgent(
      'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) ' +
      'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1'
    );

    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise((r) => setTimeout(r, 800));
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: outFile, fullPage: true });
    console.log('Saved mobile screenshot to', outFile);
  } catch (err) {
    console.error('Error capturing screenshot:', err);
    process.exitCode = 2;
  } finally {
    await browser.close();
  }
})();
