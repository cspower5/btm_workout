import puppeteer from 'puppeteer';

(async ()=>{
  const browser = await puppeteer.launch({headless: true, args:['--no-sandbox','--disable-setuid-sandbox']});
  const page = await browser.newPage();
  page.on('request', req => console.log('REQ:', req.method(), req.url()));
  page.on('response', async res => {
    try{
      const url = res.url();
      const status = res.status();
      const ct = res.headers()['content-type'] || '';
      console.log('RESP:', status, ct, url);
    }catch(e){console.log('RESP ERR', e.message)}
  });
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  const BASE = process.env.TEST_BASE || 'http://127.0.0.1:5174/btm_workout';
  console.log('Navigating to', BASE+'/#/workout');
  await page.goto(BASE+'/#/workout', {waitUntil: 'networkidle0'});
  const html = await page.content();
  console.log('PAGE HTML START\n', html.slice(0,1000), '\nPAGE HTML END');
  await browser.close();
})();
