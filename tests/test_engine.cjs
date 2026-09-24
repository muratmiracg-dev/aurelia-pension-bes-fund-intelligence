const assert = require('node:assert/strict');
const fs = require('node:fs');
const E = require('../web/engine.js');
const data = JSON.parse(fs.readFileSync('artifacts/dashboard_data.json','utf8'));
let comparisons = 0;
function close(a,b){assert.ok(Math.abs(a-b)<1e-9*Math.max(1,Math.abs(b)),`${a} != ${b}`);comparisons++;}
for(const fund of data.funds){
  for(const [period,n] of [['1Y',252],['3Y',756],['ALL',null]]){
    const m=E.stats(n?fund.nav.slice(-n-1):fund.nav), py=fund.metrics[period];
    for(const key of ['total_return','annual_return','volatility','max_drawdown','var95','es95'])close(m[key],py[key]);
  }
}
assert.equal(E.project(5000,2,0,0).at(-1).balance,120000);
close(E.project(100,2,0,0,.1).at(-1).paid,2520);
const g=1.01;close(E.project(100,1,g**12-1,0).at(-1).balance,100*g*(g**12-1)/(g-1));
close(E.tail([-.2,-.1,...Array(28).fill(0)]).es95,(.2+.05)/1.5);
assert.throws(()=>E.project(100,1.5,.1,.1));
assert.throws(()=>E.stats([1,0,2]));
console.log(`Browser engine verified: ${comparisons} numerical comparisons + boundary checks.`);
