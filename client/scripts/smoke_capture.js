import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';

(async function(){
  const ts = new Date().toISOString().replace(/[:.]/g,'-');
  const outDir = path.resolve('../../artifacts/smoke_' + ts);
  fs.mkdirSync(outDir, { recursive: true });

  const url = process.env.TEST_URL || 'http://127.0.0.1:5174/btm_workout/';

  const browser = await puppeteer.launch({ args: ['--no-sandbox','--disable-setuid-sandbox'] });
  const page = await browser.newPage();

  async function capture(viewport, name){
    await page.setViewport(viewport);
    const consoleLog = [];
    page.on('console', msg => consoleLog.push({type: msg.type(), text: msg.text()}));
    await page.goto(url, { waitUntil: 'networkidle2' });
  // small delay to allow any dynamic content to settle
  await new Promise((res) => setTimeout(res, 500));
  const html = await page.content();
  fs.writeFileSync(path.join(outDir, `${name}.html`), html);
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: true });
  fs.writeFileSync(path.join(outDir, `${name}.console.json`), JSON.stringify(consoleLog, null, 2));
  // remove the specific console listener we added
  page.off('console', (msg) => consoleLog.push({type: msg.type(), text: msg.text()}));
  }

  try{
    await capture({ width: 390, height: 844, isMobile: true, hasTouch: true }, 'mobile-portrait');
    await capture({ width: 844, height: 390, isMobile: true, hasTouch: true }, 'mobile-landscape');
    await capture({ width: 1024, height: 768 }, 'tablet');
    await capture({ width: 1366, height: 768 }, 'desktop');
    console.log('Artifacts written to', outDir);
  }catch(err){
    console.error('Smoke capture failed', err);
    process.exitCode = 2;
  }finally{
    await browser.close();
  }
})();
