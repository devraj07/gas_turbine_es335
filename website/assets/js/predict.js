'use strict';
const fieldNames={AT:'Ambient temperature',AP:'Ambient pressure',AH:'Ambient humidity',AFDP:'Air filter differential pressure',GTEP:'Turbine exhaust pressure',TIT:'Turbine inlet temperature',TAT:'Turbine after temperature',CDP:'Compressor discharge pressure'};
const el=id=>document.getElementById(id);
let bundle;
const number=v=>Number(v).toLocaleString('en-US',{maximumFractionDigits:4});
function status(message,error=false){el('predict-status').textContent=message;el('predict-status').classList.toggle('error',error);}
function renderResponses(input,values){
 const feature=el('response-feature').value,index=bundle.features.indexOf(feature),range=bundle.ranges[feature];
 const xs=Array.from({length:21},(_,i)=>range.min+(range.max-range.min)*i/20);
 const inside=input[index]>=range.min&&input[index]<=range.max;
 if(inside)xs.push(input[index]);xs.sort((a,b)=>a-b);
 const samples=xs.map(x=>{const row=input.slice();row[index]=x;return {x,y:TurbineInference.predict(bundle,row)};});
 for(const target of ['TEY','CO','NOX']){
  const ys=samples.map(p=>p.y[target]),low=Math.min(...ys),high=Math.max(...ys),pad=Math.max((high-low)*.12,Math.abs(low)*.001,1e-6);
  const x=v=>42+(v-range.min)/(range.max-range.min)*274,y=v=>65-(v-low+pad)/(high-low+2*pad)*51;
  const points=samples.map(p=>`${x(p.x).toFixed(2)},${y(p.y[target]).toFixed(2)}`).join(' ');
  el('response-'+target).innerHTML=`<svg viewBox="0 0 330 90" role="img" aria-label="${target} model response to ${feature}, holding the other seven inputs fixed"><title>${target} prediction as ${feature} varies. Current ${feature}: ${number(input[index])}. Current prediction: ${number(values[target])}.</title><line x1="42" y1="68" x2="316" y2="68" stroke="#d5dfd8"/><text x="2" y="19">${number(high)}</text><text x="2" y="65">${number(low)}</text><polyline points="${points}" fill="none" stroke="#146b43" stroke-width="2"/>${inside?`<circle cx="${x(input[index])}" cy="${y(values[target])}" r="4" fill="#d18531"><title>Current prediction: ${number(values[target])}</title></circle>`:''}<text x="42" y="85">${number(range.min)}</text><text x="316" y="85" text-anchor="end">${number(range.max)} ${feature}</text></svg>`;
 }
}
function runPrediction(event){
 if(event)event.preventDefault();
 if(!bundle)return;
 if(!el('predict-form').reportValidity()){
  for(const t of ['TEY','CO','NOX']){el('result-'+t).textContent='-';el('response-'+t).innerHTML='';}
  status('Enter a valid number for every input.',true);return;
 }
 const raw=bundle.features.map(f=>el('input-'+f).value.trim());
 const input=raw.map(Number);
 try{
  if(raw.some(v=>v==='')||!input.every(Number.isFinite))throw Error('Enter a finite number for every input.');
  const values=TurbineInference.predict(bundle,input);
  if(!Object.values(values).every(Number.isFinite))throw Error('These input magnitudes exceed the model numeric limits. Enter smaller values.');
  for(const t of ['TEY','CO','NOX']){el('result-'+t).textContent=values[t].toFixed(3);el('result-'+t).classList.remove('predict-result-stale');}
  const outside=bundle.features.filter((f,i)=>input[i]<bundle.ranges[f].min||input[i]>bundle.ranges[f].max);
  renderResponses(input,values);
  status(outside.length?`Predictions updated. Outside training ranges: ${outside.join(', ')}. These estimates may be unreliable.`:'Predictions updated. Values use native target units.',outside.length>0);
 }catch(e){for(const t of ['TEY','CO','NOX']){el('result-'+t).textContent='-';el('response-'+t).innerHTML='';}status(e.message,true);}
}
function reset(){for(const f of bundle.features){el('input-'+f).value=bundle.ranges[f].default;el('slider-'+f).value=bundle.ranges[f].default;}runPrediction();}
fetch('../assets/data/browser-models.json').then(r=>{if(!r.ok)throw Error('Model download failed. Reload to try again.');return r.json();}).then(d=>{
 bundle=d;el('model-inputs').innerHTML=d.features.map(f=>{const r=d.ranges[f];return `<div class="input-field"><label for="input-${f}"><b>${f}</b>${fieldNames[f]}</label><input id="input-${f}" name="${f}" type="number" step="any" value="${r.default}" required aria-describedby="range-${f}"><input id="slider-${f}" type="range" min="${r.min}" max="${r.max}" step="any" value="${r.default}" aria-label="${fieldNames[f]} slider" aria-describedby="range-${f}"><small id="range-${f}">Training: ${number(r.min)} - ${number(r.max)}</small></div>`;}).join('');
 el('response-feature').innerHTML=d.features.map(f=>`<option value="${f}">${f} â€” ${fieldNames[f]}</option>`).join('');el('response-feature').value='TIT';
 for(const f of d.features){
  el('slider-'+f).addEventListener('input',()=>{el('input-'+f).value=el('slider-'+f).value;runPrediction();});
  el('input-'+f).addEventListener('input',()=>{const value=Number(el('input-'+f).value);if(Number.isFinite(value))el('slider-'+f).value=Math.max(d.ranges[f].min,Math.min(d.ranges[f].max,value));runPrediction();});
 }
 el('response-feature').addEventListener('change',()=>runPrediction());
 el('response-feature').disabled=false;el('predict-button').disabled=false;el('predict-button').textContent='Predict outputs';el('reset-inputs').disabled=false;
 el('predict-form').addEventListener('submit',runPrediction);el('reset-inputs').addEventListener('click',reset);
 reset();
}).catch(e=>{status(e.message,true);el('predict-button').textContent='Models unavailable';});
