import { chromium } from '@playwright/test';
const APP='http://localhost:3000';const OUT='C:/Users/sonkh/AppData/Local/Temp/claude/d--PE-test/5192ee2d-32a6-400e-b0de-d9b2020fb7a3/scratchpad/shots';
const a=process.env.SHOT_ACCESS,r=process.env.SHOT_REFRESH;
const b=await chromium.launch();const p=await(await b.newContext({viewport:{width:900,height:820}})).newPage();
const errs=[];p.on('pageerror',e=>errs.push(String(e)));
await p.goto(APP+'/login',{waitUntil:'domcontentloaded'});
await p.evaluate(([a,r])=>{localStorage.setItem('pe_access',a);localStorage.setItem('pe_refresh',r);},[a,r]);
await p.goto(APP+'/questionaire',{waitUntil:'networkidle',timeout:90000});
await p.waitForSelector('.step',{timeout:15000});
const n=await p.$$eval('.step',s=>s.length); console.log('số .step =',n);
// kích hoạt step 13 (index 12) để chụp câu thái độ
await p.evaluate(()=>{const s=document.querySelectorAll('.step');s.forEach((e,i)=>e.classList.toggle('active',i===12));});
await p.waitForTimeout(500); await p.screenshot({path:`${OUT}/q_attitude.png`});
console.log(errs.length?('ERR:'+errs[0]):'no page errors');console.log('DONE');await b.close();
