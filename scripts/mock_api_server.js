const http = require('http');
const url = require('url');

const PORT = process.env.PORT || 4000;

function sendJSON(res, status, obj){
  const body = JSON.stringify(obj);
  res.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
  res.end(body);
}

// A small in-memory sample dataset used by the mock
const sampleExercises = [
  { name: 'Push Up', bodyPart: 'chest', equipment: 'body weight', target: 'pectorals' },
  { name: 'Bench Press', bodyPart: 'chest', equipment: 'barbell', target: 'pectorals' },
  { name: 'Incline Dumbbell Fly', bodyPart: 'chest', equipment: 'dumbbell', target: 'pectorals' },
  { name: 'Squat', bodyPart: 'legs', equipment: 'barbell', target: 'quadriceps' }
];

const server = http.createServer((req, res) => {
  try {
    const parsed = url.parse(req.url, true);
    if (req.method === 'POST' && parsed.pathname === '/api/v1/get_random_exercises') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const data = body ? JSON.parse(body) : {};
          const bp = (data.bodyPart || data.body_part || 'chest').toLowerCase();
          const num = Math.max(1, Math.min(parseInt(data.num_exercises || data.numExercises || 3, 10) || 3, 20));
          const filtered = sampleExercises.filter(e => (e.bodyPart || '').toLowerCase() === bp);
          // If nothing matches, return a small fallback set
          const pool = filtered.length ? filtered : sampleExercises;
          // Simple sampling (not cryptographically strong)
          const result = [];
          for (let i=0; i<num; i++) result.push(pool[i % pool.length]);
          return sendJSON(res, 200, result);
        } catch (e) {
          return sendJSON(res, 400, { error: 'Bad JSON' });
        }
      });
      return;
    }

    // Health endpoint for CI readiness
    if (req.method === 'GET' && parsed.pathname === '/health') {
      return sendJSON(res, 200, { status: 'ok' });
    }

    // Default not found
    sendJSON(res, 404, { error: 'Not found' });
  } catch (e) {
    sendJSON(res, 500, { error: 'Server error' });
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`mock_api_server listening on http://0.0.0.0:${PORT}`);
});
