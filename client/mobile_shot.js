const puppeteer = require('puppeteer');

(async () => {
  try {
    const iPhone = puppeteer.devices['iPhone 12'];
    const browser = await puppeteer.launch({ args: ['--no-sandbox','--disable-setuid-sandbox'] });
    const page = await browser.newPage();
    await page.emulate(iPhone);
    await page.goto('http://127.0.0.1:8081', { waitUntil: 'networkidle2', timeout: 45000 });
    await page.screenshot({ path: '/tmp/mobile_screenshot.png', fullPage: false });
    console.log('Screenshot saved to /tmp/mobile_screenshot.png');
    await browser.close();
  } catch (e) {
    console.error('Error taking screenshot:', e);
    process.exit(1);
  }
})();
