#!/usr/bin/env node
import { createRequire } from 'module';
import { spawn } from 'child_process';
import path from 'path';
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

  // Execute the main E2E script
  const script = path.resolve(process.cwd(), '..', 'scripts', 'e2e_check.js');
  console.log('Spawning e2e script:', script);
  const child = spawn(process.execPath, [script], { stdio: 'inherit' });
  const fs = require('fs');
  const path = require('path');

  function ensureArtifacts(exitCode) {
    try {
      const wd = process.cwd();
      // artifacts go under client/e2e-artifacts (when run with cwd=client)
      const artifactsDir = path.resolve(wd, 'e2e-artifacts');
      if (!fs.existsSync(artifactsDir)) fs.mkdirSync(artifactsDir, { recursive: true });
      const tmpHtml = '/tmp/e2e_page_snapshot.html';
      const tmpPng = '/tmp/e2e_page_snapshot.png';
      if (fs.existsSync(tmpHtml)) fs.copyFileSync(tmpHtml, path.join(artifactsDir, 'e2e_page_snapshot.html'));
      if (fs.existsSync(tmpPng)) fs.copyFileSync(tmpPng, path.join(artifactsDir, 'e2e_page_snapshot.png'));
      // write an exit marker so CI can tell the script failed
      fs.writeFileSync(path.join(artifactsDir, 'e2e_exit_code.txt'), String(exitCode), 'utf8');
    } catch (e) {
      console.error('artifact preservation failed:', e && e.message ? e.message : e);
    }
  }

  child.on('exit', code => {
    ensureArtifacts(code ?? 0);
    process.exit(code ?? 0);
  });
  child.on('error', err => { console.error('failed to spawn e2e script', err); ensureArtifacts(5); process.exit(5); });
}

main().catch(err => { console.error(err); process.exit(2); });
