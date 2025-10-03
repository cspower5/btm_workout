#!/usr/bin/env node
const express = require('express');
const path = require('path');

const app = express();
const port = process.env.PORT || 5174;

// Serve the client/dist directory at the /btm_workout mount path
const distDir = path.resolve(process.cwd(), 'client', 'dist');
app.use('/btm_workout', express.static(distDir));

// For any other request under /btm_workout, serve index.html to allow SPA routing
// Use a regex to avoid path-to-regexp parameter parsing issues for '*' patterns
app.get(/^\/btm_workout\/.*$/, (req, res) => {
  res.sendFile(path.join(distDir, 'index.html'));
});

app.listen(port, () => {
  console.log(`Serving client/dist at http://localhost:${port}/btm_workout`);
});
