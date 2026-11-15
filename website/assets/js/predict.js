'use strict';
const fieldNames={AT:'Ambient temperature',AP:'Ambient pressure',AH:'Ambient humidity',AFDP:'Air filter differential pressure',GTEP:'Turbine exhaust pressure',TIT:'Turbine inlet temperature',TAT:'Turbine after temperature',CDP:'Compressor discharge pressure'};
const el=id=>document.getElementById(id);
let bundle;
const number=v=>Number(v).toLocaleString('en-US',{maximumFractionDigits:4});
function status(message,error=false){el('predict-status').textContent=message;el('predict-status').classList.toggle('error',error);}
function runPrediction(event){
 if(event)event.preventDefault();
 if(!bundle)return;
 if(!el('predict-form').reportValidity())return;
 const raw=bundle.features.map(f=>el('input-'+f).value.trim());
 const input=raw.map(Number);
 try{
  if(raw.some(v=>v==='')||!input.every(Number.isFinite))throw Error('Enter a finite number for every input.');
  const values=TurbineInference.predict(bundle,input);
  if(!Object.values(values).every(Number.isFinite))throw Error('These input magnitudes exceed the model numeric limits. Enter smaller values.');
  for(const t of ['TEY','CO','NOX']){el('result-'+t).textContent=values[t].toFixed(3);el('result-'+t).classList.remove('predict-result-stale');}
  const outside=bundle.features.filter((f,i)=>input[i]<bundle.ranges[f].min||input[i]>bundle.ranges[f].max);
  status(outside.length?`Predictions updated. Outside training ranges: ${outside.join(', ')}. These estimates may be unreliable.`:'Predictions updated. Values use native target units.',outside.length>0);
 }catch(e){for(const t of ['TEY','CO','NOX'])el('result-'+t).textContent='-';status(e.message,true);}
}
function reset(){for(const f of bundle.features)el('input-'+f).value=bundle.ranges[f].default;runPrediction();}
fetch('../assets/data/browser-models.json').then(r=>{if(!r.ok)throw Error('Model download failed. Reload to try again.');return r.json();}).then(d=>{
 bundle=d;el('model-inputs').innerHTML=d.features.map(f=>{const r=d.ranges[f];return `<div class="input-field"><label for="input-${f}"><b>${f}</b>${fieldNames[f]}</label><input id="input-${f}" name="${f}" type="number" step="any" value="${r.default}" required aria-describedby="range-${f}"><small id="range-${f}">Training: ${number(r.min)} - ${number(r.max)}</small></div>`;}).join('');
 el('predict-button').disabled=false;el('predict-button').textContent='Predict outputs';el('reset-inputs').disabled=false;
 el('predict-form').addEventListener('submit',runPrediction);el('reset-inputs').addEventListener('click',reset);
 el('predict-form').addEventListener('input',()=>{status('Inputs changed. Select Predict outputs to update.');for(const t of ['TEY','CO','NOX'])el('result-'+t).classList.add('predict-result-stale');});
 reset();
}).catch(e=>{status(e.message,true);el('predict-button').textContent='Models unavailable';});
