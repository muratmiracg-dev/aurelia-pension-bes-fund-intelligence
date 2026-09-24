/* Pure calculation module, shared by the browser and Node verification tests. */
(function(root) {
  'use strict';
  function finite(a, min=2) {
    if (!Array.isArray(a) || a.length<min || !a.every(Number.isFinite)) throw Error('Geçerli gözlemler gerekli');
    return a;
  }
  function returns(a) {
    finite(a); if(a.some(x=>x<=0)) throw Error('NAV pozitif olmalı');
    return a.slice(1).map((x,i)=>x/a[i]-1);
  }
  const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
  const sd=a=>Math.sqrt(a.reduce((s,x)=>s+(x-mean(a))**2,0)/(a.length-1));
  function tail(r, confidence=.95) {
    finite(r); if(!(confidence>0&&confidence<1)||r.some(x=>x<=-1)) throw Error('Geçersiz getiri');
    const loss=r.map(x=>-x).sort((a,b)=>b-a), mass=(1-confidence)*r.length;
    const whole=Math.floor(mass+1e-12), rem=Math.max(0,mass-whole);
    let sum=loss.slice(0,whole).reduce((a,b)=>a+b,0);
    if(rem>1e-12) sum+=rem*loss[whole];
    const asc=loss.slice().reverse();
    return {var95:Math.max(0,asc[Math.ceil(confidence*loss.length)-1]),es95:Math.max(0,sum/mass)};
  }
  function stats(nav) {
    finite(nav,3);const r=returns(nav); let peak=nav[0],dd=0;
    nav.forEach(v=>{peak=Math.max(peak,v);dd=Math.min(dd,v/peak-1)});
    return {total_return:nav.at(-1)/nav[0]-1,annual_return:(nav.at(-1)/nav[0])**(252/r.length)-1,
      volatility:sd(r)*Math.sqrt(252),max_drawdown:dd,...tail(r)};
  }
  function project(monthly,years,annual,inflation,escalation=0) {
    if(![monthly,annual,inflation,escalation].every(Number.isFinite)||monthly<0||!Number.isInteger(years)||years<1||years>40||annual<-.95||annual>1||inflation<0||inflation>1||escalation<0||escalation>1) throw Error('Varsayımları kontrol edin');
    const growth=(1+annual)**(1/12);let balance=0,paid=0;
    const out=[{month:0,balance:0,paid:0,real_balance:0}];
    for(let m=1;m<=years*12;m++) {
      const deposit=monthly*(1+escalation)**Math.floor((m-1)/12);paid+=deposit;
      balance=(balance+deposit)*growth;
      out.push({month:m,balance,paid,real_balance:balance/(1+inflation)**(m/12)});
    }
    return out;
  }
  const api={returns,stats,tail,project,mean,sd};
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  else root.PensionEngine=api;
})(typeof window!=='undefined'?window:this);
