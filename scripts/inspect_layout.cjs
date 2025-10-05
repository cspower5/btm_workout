const puppeteer = require('puppeteer');

(async ()=>{
  const url = process.argv[2] || 'http://localhost:5174/btm_workout/';
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox','--disable-setuid-sandbox'] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 375, height: 812 });
    await page.goto(url, { waitUntil: 'networkidle2' });
    const data = await page.evaluate(()=>{
      const w = window.innerWidth;
      const grid = document.querySelector('.features-grid');
      const gridStyle = grid ? window.getComputedStyle(grid) : null;
      const cols = gridStyle ? gridStyle.gridTemplateColumns : null;
      const cards = Array.from(document.querySelectorAll('.feature-card'));
      const cardWidths = cards.map(c => ({w: c.clientWidth, offsetLeft: c.offsetLeft}));
      return {viewport: w, cols, cardCount: cards.length, cardWidths};
    });
    console.log('Layout inspection for', url, JSON.stringify(data, null, 2));
  }catch(e){ console.error('inspect failed', e); process.exitCode=2; }
  finally{ await browser.close(); }
})();
