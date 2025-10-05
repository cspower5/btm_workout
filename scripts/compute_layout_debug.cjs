#!/usr/bin/env node
const puppeteer = require('puppeteer');
const url = process.argv[2] || process.env.TARGET_URL || 'http://localhost:5174/btm_workout/';
(async () => {
  const browser = await puppeteer.launch({args: ['--no-sandbox','--disable-setuid-sandbox']});
  const page = await browser.newPage();
  // emulate mobile viewport like other scripts
  await page.setViewport({width: 375, height: 800, isMobile: true, hasTouch: true});
  await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1');
  await page.goto(url, {waitUntil: 'networkidle2'});

  const result = await page.evaluate(() => {
    function short(el) {
      if (!el) return null;
      return {
        tag: el.tagName,
        classes: el.className,
        id: el.id || null,
        text: (el.textContent || '').trim().slice(0,80)
      };
    }

    const doc = document;
    const metaViewport = (() => {
      const m = doc.querySelector('meta[name=viewport]');
      return m ? m.getAttribute('content') : null;
    })();

    const rootClientW = doc.documentElement.clientWidth;
    const innerW = window.innerWidth;
    const dpr = window.devicePixelRatio;

    const grid = doc.querySelector('.features-grid') || doc.querySelector('.home-grid') || doc.querySelector('.feature-list') || doc.querySelector('.features');
    const gridRect = grid ? grid.getBoundingClientRect() : null;
    const gridStyle = grid ? window.getComputedStyle(grid) : null;

    const cards = Array.from(doc.querySelectorAll('.feature-card, .feature-card-link')).slice(0,12);
    const cardDetails = cards.map((c, i) => {
      const rect = c.getBoundingClientRect();
      const cs = window.getComputedStyle(c);
      // try to find direct anchor inside
      const anchor = c.querySelector('a') || (c.tagName === 'A' ? c : null);
      const anchorRect = anchor ? anchor.getBoundingClientRect() : null;
      const anchorStyle = anchor ? window.getComputedStyle(anchor) : null;
      return {
        index: i,
        short: short(c),
        rect: {w: Math.round(rect.width), h: Math.round(rect.height), left: Math.round(rect.left), top: Math.round(rect.top)},
        computed: {
          display: cs.display,
          boxSizing: cs.boxSizing,
          width: cs.width,
          maxWidth: cs.maxWidth,
          minWidth: cs.minWidth,
          flexBasis: cs.flexBasis,
          flexGrow: cs.flexGrow,
          flexShrink: cs.flexShrink,
          gridColumn: cs.gridColumn,
          marginLeft: cs.marginLeft,
          marginRight: cs.marginRight
        },
        anchor: anchor ? {
          short: short(anchor),
          rect: anchorRect ? {w: Math.round(anchorRect.width), left: Math.round(anchorRect.left)} : null,
          computed: anchorStyle ? {
            display: anchorStyle.display,
            width: anchorStyle.width,
            flexBasis: anchorStyle.flexBasis,
            flex: anchorStyle.flex
          } : null
        } : null
      };
    });

    return {
      url: location.href,
      metaViewport,
      rootClientW,
      innerW,
      dpr,
      grid: grid ? {short: short(grid), rect: gridRect ? {w: Math.round(gridRect.width), left: Math.round(gridRect.left)} : null, computed: gridStyle ? {display: gridStyle.display, gridTemplateColumns: gridStyle.gridTemplateColumns, gap: gridStyle.gap, alignItems: gridStyle.alignItems, justifyItems: gridStyle.justifyItems} : null} : null,
      cards: cardDetails
    };
  });

  console.log(JSON.stringify(result, null, 2));
  await browser.close();
})();
