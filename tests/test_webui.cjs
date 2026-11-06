const { chromium } = require(process.env.SPATIAL_PLAYWRIGHT_PATH || 'playwright');
const fs = require('fs');
const http = require('http');
const path = require('path');
const assert = require('assert');
const root = process.env.WEBUI_ROOT ? path.resolve(process.env.WEBUI_ROOT) : path.resolve(__dirname,'../build/module/webroot');
const server = http.createServer((req,res) => {
  const name = req.url === '/' ? 'index.html' : req.url.slice(1);
  if (!['index.html','app.js','style.css'].includes(name)) {res.writeHead(404);res.end();return;}
  res.setHeader('content-type',name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':'text/html');
  res.end(fs.readFileSync(path.join(root,name)));
});
(async () => {
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const base='http://127.0.0.1:'+server.address().port;
  const browser = await chromium.launch({executablePath:process.env.SPATIAL_BROWSER_BINARY || undefined,args:['--no-sandbox','--disable-dev-shm-usage']});
  try {
    const page=await browser.newPage({viewport:{width:393,height:852},deviceScaleFactor:1});
    await page.goto(base);
    await page.waitForFunction(()=>document.querySelector('#feedback').textContent.includes('compatible root manager'));
    assert(await page.locator('#spatial').isDisabled());
    assert.equal(await page.locator('#spatial').getAttribute('aria-pressed'),'false');
    console.log('PASS missing root bridge: controls unavailable, no simulated activation');
    await page.addInitScript(() => {
      window.mockState={enabled:true,available:true,level:1,mounted:true,headTrackerAvailable:false,device:'USB · KM-HIFI-384KHZ'};
      window.mockCalls=[];
      window.ksu={exec:(command,options,name)=>{
        const action=command.split(' ').at(-1);window.mockCalls.push(action);
        let result;
        if (window.mockError) result={error:window.mockError};
        else {if(action==='on')window.mockState.enabled=true;if(action==='off')window.mockState.enabled=false;result=window.mockState;}
        setTimeout(()=>window[name](0,JSON.stringify(result),''),10);
      }};
    });
    await page.reload();
    await page.waitForFunction(()=>document.querySelector('#status').textContent==='Enabled · available');
    assert(await page.locator('#demo').isEnabled());
    assert.equal(await page.locator('#spatial').getAttribute('aria-pressed'),'true');
    if (await page.locator('.orb-ring').count()) await page.waitForFunction(()=>Number(getComputedStyle(document.querySelector('.ring-edge')).opacity)>.9);
    await page.screenshot({path:path.resolve(__dirname,'../build/webui-review.png'),fullPage:true});
    await page.emulateMedia({reducedMotion:'reduce'});
    if (await page.locator('.orb-ring').count()) {
      assert.equal(await page.locator('.orb-ring').first().evaluate(el=>getComputedStyle(el).animationName),'none');
    }
    await page.emulateMedia({reducedMotion:'no-preference'});
    await page.locator('#original').click();
    await page.waitForFunction(()=>document.querySelector('#status').textContent==='Original audio');
    assert(await page.locator('#demo').isDisabled());
    await page.locator('#spatial').click();
    await page.waitForFunction(()=>document.querySelector('#status').textContent==='Enabled · available');
    console.log('PASS confirmed original/spatial state transitions and demo gating');
    await page.evaluate(()=>window.mockError='Mounts missing');
    await page.locator('#refresh').click();
    await page.waitForFunction(()=>document.querySelector('#feedback').textContent==='Mounts missing');
    assert(await page.locator('#spatial').isDisabled());
    assert.equal(await page.locator('#spatial').getAttribute('aria-pressed'),'false');
    console.log('PASS failed status clears prior enabled UI');
    await page.evaluate(()=>{window.mockError=null;window.mockState.mounted=false;});
    await page.locator('#refresh').click();
    await page.waitForFunction(()=>document.querySelector('#status').textContent==='Audio files not mounted');
    assert((await page.locator('#device').textContent()).includes('KM-HIFI'));
    assert(await page.locator('#spatial').isDisabled());
    assert.equal(await page.locator('#spatial').getAttribute('aria-pressed'),'false');
    console.log('PASS detected headphones remain visible with missing audio mounts; activation stays blocked');
    await page.evaluate(()=>{window.mockError=null;window.mockState.level=0;window.mockState.mounted=true;});
    await page.locator('#refresh').click();
    await page.waitForFunction(()=>document.querySelector('#status').textContent==='Audio engine unavailable');
    assert(await page.locator('#original').isDisabled());
    console.log('PASS unsupported engine is reported without offering an ineffective toggle');
    await page.evaluate(()=>{window.mockState.level=1;window.mockState.device='<img src=x onerror=alert(1)>';});
    await page.locator('#refresh').click();
    await page.waitForFunction(()=>document.querySelector('#device').textContent.startsWith('<img'));
    assert.equal(await page.locator('#device img').count(),0);
    await page.setViewportSize({width:320,height:740});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
    assert.deepEqual(await page.evaluate(()=>[...new Set(window.mockCalls)]),['status','off','on']);
    console.log('PASS escaped device names, 320px layout and explicit-only operations');
    await page.close();
  } finally {await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exit(1);});
