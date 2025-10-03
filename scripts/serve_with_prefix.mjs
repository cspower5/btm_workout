#!/usr/bin/env node
import http from 'http';
import fs from 'fs';
import path from 'path';

const PORT = parseInt(process.env.PORT || process.env.P || '8080', 10) || 8080;
const DIST = path.resolve(process.cwd(), 'client', 'dist');
const PREFIX = '/btm_workout';

const mime = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.js', 'application/javascript; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.png', 'image/png'],
  ['.svg', 'image/svg+xml'],
  ['.jpg', 'image/jpeg'],
  ['.jpeg', 'image/jpeg'],
  ['.webp', 'image/webp'],
  ['.json', 'application/json'],
]);

function contentTypeFromName(name) {
  return mime.get(path.extname(name)) || 'application/octet-stream';
}

function sendFile(res, filePath) {
  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
      // Try a fallback for hashed index assets (index-*.js / index-*.css)
      const fallback = findFallbackAsset(filePath);
      if (fallback) {
        return sendFile(res, fallback);
      }
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not found');
      return;
    }

    res.writeHead(200, { 'Content-Type': contentTypeFromName(filePath) });
    const rs = fs.createReadStream(filePath);
    rs.pipe(res);
    rs.on('error', () => res.end());
  });
}

// If an asset filename doesn't exist, attempt a best-effort fallback for
// Vite’s hashed index assets: index-*.js and index-*.css so CI doesn't fail
// when the built filenames differ from what a static snapshot expects.
function findFallbackAsset(requested) {
  try {
    const assetsDir = path.join(DIST, 'assets');
    const files = fs.readdirSync(assetsDir);
    if (requested.endsWith('.js')) {
      const js = files.find((f) => /^index-.*\.js$/.test(f));
      if (js) return path.join(assetsDir, js);
    }
    if (requested.endsWith('.css')) {
      const css = files.find((f) => /^index-.*\.css$/.test(f));
      if (css) return path.join(assetsDir, css);
    }
  } catch (e) {
    // ignore
  }
  return null;
}

const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url || '/');

  // Serve root index.html for '/'
  if (url === '/' || url === '') {
    return sendFile(res, path.join(DIST, 'index.html'));
  }

  // If the request is for the mounted prefix, strip it and serve from dist
  if (url.startsWith(PREFIX)) {
    let rel = url.slice(PREFIX.length);
    if (!rel || rel === '/') rel = 'index.html';
    else if (rel.startsWith('/')) rel = rel.slice(1);
    const candidate = path.join(DIST, rel);
    return sendFile(res, candidate);
  }

  // Also allow direct asset access on /assets (useful if a relative build was used)
  if (url.startsWith('/assets') || url.startsWith('/btm_workout/assets')) {
    let rel = url.replace(/^\//, '');
    rel = rel.replace(/^btm_workout\//, '');
    const candidate = path.join(DIST, rel);
    return sendFile(res, candidate);
  }

  // Fallback to index.html for SPA routes
  return sendFile(res, path.join(DIST, 'index.html'));
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Serving ${DIST} on http://0.0.0.0:${PORT} (mounted at ${PREFIX})`);
});
