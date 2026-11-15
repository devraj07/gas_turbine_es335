/* Browser inference mirrors sklearn tree input conversion to float32. */
(function(root){
 'use strict';
 function treeValue(tree,input){let node=0;while(tree.left[node]!==-1){node=input[tree.feature[node]]<=tree.threshold[node]?tree.left[node]:tree.right[node];}return tree.value[node];}
 function predict(bundle,input){
  if(input.length!==bundle.features.length||!input.every(Number.isFinite))throw new Error('Supply eight finite numeric values.');
  const f32=input.map(Math.fround),out={};
  for(const [target,model] of Object.entries(bundle.models)){
   if(model.kind==='linear')out[target]=model.intercept+model.coefficients.reduce((s,c,i)=>s+c*input[i],0);
   else if(model.kind==='forest')out[target]=model.trees.reduce((s,t)=>s+treeValue(t,f32),0)/model.trees.length;
   else if(model.kind==='boosting')out[target]=model.trees.reduce((s,t)=>s+model.rate*treeValue(t,f32),model.base);
   else throw new Error('Unsupported model type');
  }
  return out;
 }
 root.TurbineInference={predict};
 if(typeof module!=='undefined')module.exports={predict};
})(globalThis);
