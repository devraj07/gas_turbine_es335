const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {predict}=require('../assets/js/inference.js');const folder=path.join(__dirname,'../assets/data');
const bundle=JSON.parse(fs.readFileSync(path.join(folder,'browser-models.json'))),fixtures=JSON.parse(fs.readFileSync(path.join(folder,'prediction-fixtures.json')));
let maxError=0;
for(const f of fixtures){const actual=predict(bundle,f.input);for(const t of ['TEY','CO','NOX']){const error=Math.abs(actual[t]-f.expected[t]);maxError=Math.max(maxError,error);assert.ok(error<1e-9,`${t}: ${error}`);}}
assert.throws(()=>predict(bundle,[NaN]),/finite/);
assert.throws(()=>predict(bundle,Array(8).fill(Infinity)),/finite/);
for(const side of ['min','max','default']){const outputs=predict(bundle,bundle.features.map(f=>bundle.ranges[f][side]));assert.ok(Object.values(outputs).every(Number.isFinite));}
console.log(`PASS: ${fixtures.length} Python/JavaScript prediction fixtures; max absolute difference ${maxError}; invalid input and boundary checks.`);
