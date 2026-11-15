// Verify real form handlers use current input values, including out-of-range inputs.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const bundle=JSON.parse(fs.readFileSync(path.join(root,'assets/data/browser-models.json'),'utf8'));
const inference=require('../assets/js/inference.js');
const code=fs.readFileSync(path.join(root,'assets/js/predict.js'),'utf8');
const nodes={};
function node(id){return nodes[id]??=(
 {_value:'',get value(){return this._value;},set value(v){this._value=String(v);},textContent:'',innerHTML:'',disabled:true,handlers:{},classList:{toggle(){},remove(){},add(){}},
 addEventListener(type,fn){this.handlers[type]=fn;},reportValidity(){return true;}}
);}
for(const f of bundle.features)node('input-'+f).value=String(bundle.ranges[f].default);
const errors=[];
vm.runInNewContext(code,{document:{getElementById:node},TurbineInference:inference,fetch:async()=>({ok:true,json:async()=>bundle}),console:{error:e=>errors.push(e)}});
setImmediate(()=>{
 try{
  assert.equal(errors.length,0);
  assert.equal(node('predict-button').disabled,false);
  const numberFields=node('model-inputs').innerHTML.match(/<input[^>]*type="number"[^>]*>/g);
  assert.equal(numberFields.length,8);
  assert.ok(numberFields.every(field=>!/\s(?:min|max)=/.test(field)),'Numeric fields must allow extrapolation');
  assert.equal((node('model-inputs').innerHTML.match(/type="range"/g)||[]).length,8);
  const submit=()=>node('predict-form').handlers.submit({preventDefault(){}});
  const verify=()=>{const values=bundle.features.map(f=>Number(node('input-'+f).value));const expected=inference.predict(bundle,values);for(const t of ['TEY','CO','NOX'])assert.equal(node('result-'+t).textContent,expected[t].toFixed(3));};
  verify();
  for(const feature of bundle.features){
   node('slider-'+feature).value=String(bundle.ranges[feature].min);
   node('slider-'+feature).handlers.input();
   assert.equal(node('input-'+feature).value,node('slider-'+feature).value);verify();
   node('input-'+feature).value=String(bundle.ranges[feature].max);
   node('input-'+feature).handlers.input();
   assert.equal(node('slider-'+feature).value,node('input-'+feature).value);verify();
   node('response-feature').value=feature;node('response-feature').handlers.change();
   for(const target of ['TEY','CO','NOX']){
    const svg=node('response-'+target).innerHTML;
    assert.ok(svg.includes('<polyline')&&svg.includes('<circle'));
    assert.ok(svg.includes(`response to ${feature}`));
    assert.ok(!/NaN|Infinity|undefined/.test(svg));
    const input=bundle.features.map(f=>Number(node('input-'+f).value));
    const index=bundle.features.indexOf(feature),r=bundle.ranges[feature];
    const samples=Array.from({length:21},(_,i)=>{const row=input.slice();row[index]=r.min+(r.max-r.min)*i/20;return inference.predict(bundle,row)[target];});
    samples.push(inference.predict(bundle,input)[target]);
    const formatted=Number(Math.max(...samples)).toLocaleString('en-US',{maximumFractionDigits:4});
    assert.ok(svg.includes(formatted),'Response range must come from actual model predictions');
   }
  }
  for(const kind of ['min','max']){for(const f of bundle.features)node('input-'+f).value=String(bundle.ranges[f][kind]);submit();verify();}
  node('input-AT').value='-10';submit();verify();assert.match(node('predict-status').textContent,/Outside training ranges: AT/);
  node('input-AT').value='';submit();assert.match(node('predict-status').textContent,/finite number/);assert.equal(node('result-TEY').textContent,'-');
  node('input-AT').value='Infinity';submit();assert.match(node('predict-status').textContent,/finite number/);
  node('reset-inputs').handlers.click();verify();assert.match(node('predict-status').textContent,/Predictions updated/);
  console.log('PASS: eight bidirectional sliders; all eight response-graph selectors match fitted-model ranges; exact submitted predictions, extrapolation warnings, invalid values and reset.');
 }catch(e){console.error(e);process.exitCode=1;}
});
