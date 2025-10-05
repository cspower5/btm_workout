#!/usr/bin/env node
import { createRequire } from 'module';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);

async function tryImport(name){
  try{
    await import(name);
    console.log(`import ok: ${name}`);
    return true;
  }catch(e){
    return false;
  }
}

function tryRequireFromClient(name){
  try{
    require(path.resolve(process.cwd(), 'node_modules', name));
    console.log(`require ok from client/node_modules: ${name}`);
    return true;
  }catch(e){
    try{
      // fallback: require from repo root's client/node_modules
      require(path.resolve(process.cwd(), '..', 'client', 'node_modules', name));
      console.log(`require ok from ../client/node_modules: ${name}`);
      return true;
    }catch(e2){
      return false;
    }
  }
}

async function main(){
  console.log('run_e2e_with_fallbacks: cwd=', process.cwd());
  // Check availability of puppeteer or puppeteer-core and axios
  const hasPuppeteerCore = await tryImport('puppeteer-core');
  const hasPuppeteer = await tryImport('puppeteer');
  const hasAxios = await tryImport('axios') || tryRequireFromClient('axios');

  if(!hasAxios){
    console.error('axios not available: please ensure it is installed at root or in client');
    process.exit(3);
  }
  if(!hasPuppeteerCore && !hasPuppeteer){
    console.error('neither puppeteer-core nor puppeteer found; ensure dependencies are installed');
    process.exit(4);
  }

  // Execute the main E2E script. The repository may be invoked with different
  // working directories (repo root, client/, CI runners). Try several likely
  // candidate locations and pick the first that exists.
  const fs = require('fs');
  const candidates = [
    path.resolve(process.cwd(), 'scripts', 'e2e_check.js'),
    path.resolve(process.cwd(), '..', 'scripts', 'e2e_check.js'),
    path.resolve(process.cwd(), 'client', 'scripts', 'e2e_check.js'),
    path.resolve(process.cwd(), '..', 'client', 'scripts', 'e2e_check.js')
  ];
  let script = null;
  for (const c of candidates) {
    if (fs.existsSync(c)) { script = c; break; }
  }
  if (!script) {
    // fallback: the original expected location relative to client
    script = path.resolve(process.cwd(), '..', 'scripts', 'e2e_check.js');
  }
  console.log('Spawning e2e runner for script:', script);
  // Spawn a small CommonJS runner that imports the ESM script via a file URL.
  // Resolve the runner path relative to the script's location so this wrapper
  // works regardless of the current working directory.
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const repoRoot = path.resolve(__dirname, '..');
  const runner = path.resolve(repoRoot, 'scripts', 'e2e_runner.cjs');
  // Pass the discovered script path as an argument to the runner so it can import
  // the correct ESM file regardless of working directory.
  const child = spawn(process.execPath, [runner, script], { stdio: 'inherit' });
  child.on('exit', code => process.exit(code ?? 0));
  child.on('error', err => { console.error('failed to spawn e2e script', err); process.exit(5); });
}

main().catch(err => { console.error(err); process.exit(2); });
