const http = require('http');
const fs = require('fs');
const path = require('path');

const DIST = path.join(__dirname, 'dist');
const PORT = process.env.PORT || 8081;

const mime = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
};

function sendFile(res, filePath) {
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      return res.end('Not found');
    }
    const ext = path.extname(filePath).toLowerCase();
    const type = mime[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': type });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  try {
    // Redirect root to the mounted prefix so visiting / shows the app
    if (req.url === '/') {
      res.writeHead(302, { Location: '/btm_workout/' });
      return res.end();
    }

    // Only serve under /btm_workout/
    const prefix = '/btm_workout/';
    if (!req.url.startsWith(prefix)) {
      // Small convenience: redirect other requests to the prefix root
      res.writeHead(302, { Location: '/btm_workout/' });
      return res.end();
    }

    let relPath = req.url.slice(prefix.length);
    if (!relPath || relPath.endsWith('/')) {
      relPath = path.posix.join(relPath || '', 'index.html');
    }

    // Prevent path traversal
    const safePath = path.normalize(relPath).replace(/^\.\./, '');
    const filePath = path.join(DIST, safePath);

    // If path points to a directory, serve index.html
    fs.stat(filePath, (err, stats) => {
      if (!err && stats.isDirectory()) {
        return sendFile(res, path.join(filePath, 'index.html'));
      }
      return sendFile(res, filePath);
    });
  } catch (e) {
    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end('Server error');
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`serve_with_prefix running on http://0.0.0.0:${PORT} (mounted at /btm_workout/)`);
});
