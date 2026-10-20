'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../css/jss/v6-ui.js'),'utf8');
function node(dataset={}) {
  const attrs={},events={};
  return {dataset,attrs,events,id:'',hidden:false,tabIndex:0,
    classList:{toggle(){}},setAttribute(k,v){attrs[k]=v;},
    addEventListener(k,v){events[k]=v;},focus(){this.focused=true;}};
}
function tabs() {
  const tablist=node();
  const buttons=['chat','files','project'].map(tab=>Object.assign(node({tab}),{parentElement:tablist}));
  const panels=['chat','files','project'].map(panel=>node({panel}));
  const root={buttons,panels};
  const code=source.slice(source.indexOf("  $$('[data-tabs]')"),source.indexOf('  // Password strength'));
  vm.runInNewContext(code,{$$:(selector)=>selector==='[data-tabs]'?[root]:selector==='[data-tab]'?buttons:panels});
  return {buttons,panels,tablist};
}
test('tabs expose relationships and only the selected tab enters the tab order',()=>{
 const {buttons,panels,tablist}=tabs();
 assert.equal(tablist.attrs.role,'tablist');
 buttons.forEach((button,i)=>{
   assert.equal(button.attrs.role,'tab');assert.equal(button.attrs['aria-controls'],panels[i].id);
   assert.equal(panels[i].attrs['aria-labelledby'],button.id);
   assert.equal(button.tabIndex,i===0?0:-1);assert.equal(panels[i].hidden,i!==0);
 });
});
test('keyboard wraps and Home/End select the matching panel and move focus',()=>{
 const {buttons,panels}=tabs();
 function key(index,key,target){let prevented=false;
   buttons[index].events.keydown({key,preventDefault(){prevented=true;}});
   assert.equal(prevented,true);assert.equal(buttons[target].focused,true);
   assert.equal(buttons[target].attrs['aria-selected'],'true');
   panels.forEach((p,i)=>assert.equal(p.hidden,i!==target));
 }
 key(0,'ArrowLeft',2);key(2,'ArrowRight',0);key(0,'End',2);key(2,'Home',0);
});
test('click selects the panel and unrelated keys retain normal scrolling',()=>{
 const {buttons,panels}=tabs();buttons[1].events.click();assert.equal(panels[1].hidden,false);
 buttons[1].events.keydown({key:'ArrowDown',preventDefault(){assert.fail('vertical scrolling must remain available');}});
 assert.equal(buttons[1].attrs['aria-selected'],'true');
});
