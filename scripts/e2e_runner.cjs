const path = require('path');
const url = require('url');
(async () => {
  try {
    // Accept a script path as an argument (passed from run_e2e_with_fallbacks.mjs)
    // so the runner can import the correct ESM file regardless of CWD.
    const argPath = process.argv[2];
    const scriptPath = argPath ? path.resolve(argPath) : path.resolve(__dirname, 'e2e_check.js');
    const scriptUrl = url.pathToFileURL(scriptPath).href;
    await import(scriptUrl);
  } catch (e) {
    console.error('e2e_runner import failed:', e && e.stack ? e.stack : e);
    process.exit(1);
  }
})();
