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
  child.on('exit', code => process.exit(code ?? 0));
  child.on('error', err => { console.error('failed to spawn e2e script', err); process.exit(5); });
}

main().catch(err => { console.error(err); process.exit(2); });
