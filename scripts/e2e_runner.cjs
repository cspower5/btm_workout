const path = require('path');
const url = require('url');
(async () => {
  try {
    const scriptPath = path.resolve(__dirname, 'e2e_check.js');
    const scriptUrl = url.pathToFileURL(scriptPath).href;
    await import(scriptUrl);
  } catch (e) {
    console.error('e2e_runner import failed:', e && e.stack ? e.stack : e);
    process.exit(1);
  }
})();
