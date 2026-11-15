const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'index.html'),'utf8'),code=fs.readFileSync(path.join(root,'assets/js/app.js'),'utf8');
const datasets=Object.fromEntries(['analysis','research','audit'].map(name=>[name,JSON.parse(fs.readFileSync(path.join(root,'assets/data',name+'.json'),'utf8'))]));
const nodes=Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],{innerHTML:'',textContent:'',value:'',checked:true,hidden:true,handlers:{},addEventListener(type,fn){this.handlers[type]=fn;}}]));
for(const match of html.matchAll(/<select[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)){
 const options=[...match[2].matchAll(/<option([^>]*)>([^<]*)<\/option>/g)];
 const option=options.find(o=>o[1].includes('selected'))||options[0];
 if(option)nodes[match[1]].value=(option[1].match(/value="([^"]+)"/)||[])[1]||option[2];
}
const errors=[];const ctx=vm.createContext({document:{getElementById:id=>{assert.ok(nodes[id],`Missing element ${id}`);return nodes[id];}},location:{hostname:'example.github.io',pathname:'/gas-turbine-ml/'},console:{error:e=>errors.push(e)},fetch:async url=>{const name=url.match(/assets\/data\/(\w+)\.json/)[1];assert.ok(datasets[name]);return{ok:true,json:async()=>datasets[name]};}});
vm.runInContext(code,ctx);
setImmediate(()=>{
 try{
  assert.equal(errors.length,0,errors[0]?.stack);assert.equal(nodes['load-status'].textContent,'');
  assert.equal(nodes['repository-link'].href,'https://github.com/devraj07/gas_turbine_es335');
  let changes=0;
  function check(){for(const [id,node] of Object.entries(nodes)){
   assert.ok(!/NaN|Infinity|undefined/.test(node.innerHTML),id);
   if(node.innerHTML.includes('<svg')){assert.ok(node.innerHTML.includes('</svg>'),id);assert.ok(node.innerHTML.includes('<title>'),id);}
   const text=(node.innerHTML.replace(/<[^>]*>/g,'')+' '+node.textContent);
   assert.ok(!text.includes('?'),`Unexpected question mark in ${id}`);
   assert.ok(!/[\uFFFD\u00c2\u00c3]/.test(text),`Encoding artifact in ${id}`);
  }}
  function change(id,value){nodes[id].value=String(value);assert.ok(nodes[id].handlers.change,id);nodes[id].handlers.change();changes++;check();}
  check();
  for(const period of Object.keys(datasets.analysis.periods)){change('audit-period',period);for(const view of ['summary','tails','quality'])change('stats-view',view);}
  for(const variable of [...datasets.analysis.features,...datasets.analysis.targets]){
   change('distribution-variable',variable);for(const period of Object.keys(datasets.analysis.periods))change('distribution-period',period);
   change('time-variable',variable);for(const year of [2011,2012,2013,2014,2015])change('sequence-year',year);
   change('cluster-variable',variable);
  }
  for(const feature of datasets.analysis.features){change('relationship-feature',feature);for(const target of datasets.analysis.targets)change('relationship-target',target);}
  for(const period of ['all','development','2015']){change('correlation-period',period);for(const method of ['pearson','spearman'])change('correlation-method',method);}
  for(const target of datasets.analysis.targets){change('model-target',target);for(const metric of ['MAE','RMSE','R2'])change('model-metric',metric);change('error-target',target);change('conditional-target',target);for(const feature of datasets.analysis.features)change('error-feature',feature);change('split-target',target);}
  for(const pair of ['TEY,CO','TEY,NOX','CO,NOX']){change('pareto-pair',pair);for(let i=0;i<4;i++){change('solution-select',i);for(const checked of [true,false]){nodes['show-candidates'].checked=checked;nodes['show-candidates'].handlers.change();changes++;check();assert.equal((nodes['pareto-chart'].innerHTML.match(/<circle/g)||[]).length,57+(checked?datasets.research.candidates.length:0));}}}
  for(const target of datasets.analysis.targets){change('model-target',target);change('error-target',target);for(const model of Object.keys(datasets.analysis.modelExplorers[target])){change('prediction-model',model);change('residual-model',model);assert.ok(nodes['error-interpretation'].textContent.includes(model));}}
  for(const cluster of ['all','0','1','2','3']){change('cluster-select',cluster);assert.equal((nodes['cluster-table'].innerHTML.match(/<tbody><tr>|<\/tr><tr>/g)||[]).length,cluster==='all'?4:1);}
  for(let i=0;i<datasets.research.pareto.length;i++){change('pareto-point',i);assert.ok(nodes['solution-table'].innerHTML.includes(Number(datasets.research.pareto[i].Predicted_TEY).toLocaleString('en-US',{minimumFractionDigits:3,maximumFractionDigits:3})));}
  const charts=Object.values(nodes).filter(n=>n.innerHTML.startsWith('<svg')).length;
  assert.equal(charts,23);assert.equal((nodes.notebooks.innerHTML.match(/<a /g)||[]).length,12);
  console.log(`PASS: ${changes} control changes; ${charts} SVG charts plus correlation heatmap; all Pareto points; no runtime or rendered-text encoding errors.`);
  const failed=vm.createContext({document:ctx.document,console:ctx.console,fetch:async()=>({ok:false,status:404})});vm.runInContext(code,failed);
  setImmediate(()=>{assert.match(nodes['load-status'].textContent,/could not load/);assert.equal(errors.length,1);console.log('PASS: data-loading failure message.');});
 }catch(e){console.error(e);process.exitCode=1;}
});
