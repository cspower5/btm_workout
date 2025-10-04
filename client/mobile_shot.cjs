const puppeteer = require('puppeteer');

(async () => {
  try {
    const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const page = await browser.newPage();

    // Emulate iPhone 12 viewport and a mobile-like user agent
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
    await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1');

    await page.goto('http://127.0.0.1:8081', { waitUntil: 'networkidle2', timeout: 45000 });
    await page.screenshot({ path: '/tmp/mobile_screenshot.png', fullPage: false });
    console.log('Screenshot saved to /tmp/mobile_screenshot.png');
    await browser.close();
  } catch (e) {
    console.error('Error taking screenshot:', e);
    process.exit(1);
  }
})();
