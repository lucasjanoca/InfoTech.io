'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../css/jss/v6-app.js'),'utf8');

function setup({user={id:'client-a',email:'a@example.test'}, reject=false, pause=null}={}) {
  let submit;
  const controls=['title','service','description','deadline','budget','contact','reference'].map(name=>({name,value: name==='reference'?'https://example.test':name+' value',disabled:false}));
  const out={};
  const form={elements:{},checkValidity:()=>true,querySelectorAll:()=>controls,setAttribute(){},addEventListener(event,fn){submit=fn;}};
  const inserted=[];
  const filters=[];
  let selected;
  const query={select(columns){selected=columns;return this;},eq(key,value){filters.push([key,value]);return this;},maybeSingle:async()=>({data:null}),order:async()=>({data:[],error:null})};
  const db={
    auth:{getUser:async()=>{if(pause)await pause;return {data:{user}};}},
    from(){return {
      ...query,
      insert(payload){
        inserted.push(payload);
        return {select(){return {single:async()=>{
          if(reject)throw new Error('offline');
          return {data:{protocol:'INF-TEST'}};
        }};}};
      }
    };}
  };
  const location={search:'',pathname:'/nova-solicitacao.html',href:'https://example.test/nova-solicitacao.html'};
  const list={innerHTML:''};
  const document={body:{hasAttribute:()=>false},readyState:'loading',addEventListener(){},querySelector:s=>s==='#request-form'?form:s==='#request-message'?out:s==='#requests-list'?list:null,querySelectorAll:()=>[]};
  class FormData {constructor(){this.values=new Map(controls.filter(c=>!c.disabled).map(c=>[c.name,c.value]));}get(k){return this.values.get(k)??null;}}
  const context={window:{INFOTECH_SUPABASE_CONFIG:{url:'https://example.test',publishableKey:'public'},supabase:{createClient:()=>db}},document,location,URL,URLSearchParams,FormData,console:{error(){},warn(){}},localStorage:{getItem:()=>null},sessionStorage:{setItem(){}},exports:{}};
  // Expose closure functions in the test sandbox only; production code stays private.
  vm.runInNewContext(source.replace("  if(document.readyState==='loading')", "  exports.initRequestCreate=initRequestCreate;exports.loadRequest=loadRequest;exports.initRequestList=initRequestList;\n  if(document.readyState==='loading')"),context);
  context.exports.initRequestCreate();
  return {submit:()=>submit({preventDefault(){}}),inserted,controls,out,location,filters,list,api:context.exports,get selected(){return selected;}};
}

test('request submission preserves enabled field values before locking controls',async()=>{
 const app=setup();await app.submit();
 assert.equal(app.inserted.length,1);
 for(const key of ['title','service','description','deadline','budget','contact'])assert.equal(app.inserted[0][key],key+' value');
 assert.equal(app.inserted[0].user_id,'client-a');
 assert.equal(app.location.href,'solicitacao-enviada.html');
 assert.ok(app.controls.every(c=>!c.disabled));
});
test('double submit creates only one request even while auth is pending',async()=>{
 let release;const pause=new Promise(r=>release=r);const app=setup({pause});
 const first=app.submit();await app.submit();release();await first;
 assert.equal(app.inserted.length,1);
});
test('network failure restores controls and gives retry feedback',async()=>{
 const app=setup({reject:true});await app.submit();
 assert.ok(app.controls.every(c=>!c.disabled));assert.match(app.out.textContent,/Tente novamente/);
 await app.submit();assert.equal(app.inserted.length,2);
});
test('signed-out visitor cannot create or load a request',async()=>{
 const app=setup({user:null});await app.submit();
 assert.equal(app.inserted.length,0);assert.match(app.location.href,/login.html/);
 assert.equal(await app.api.loadRequest('INF-OTHER'),null);assert.deepEqual(app.filters,[]);
});
test('detail and list queries constrain ownership; list omits chat and project payloads',async()=>{
 const app=setup();await app.api.loadRequest('INF-TEST');
 assert.deepEqual(app.filters,[['protocol','INF-TEST'],['user_id','client-a']]);
 await app.api.initRequestList();
 assert.equal(app.filters.at(-1)[1],'client-a');
 assert.ok(!app.selected.includes('*'));assert.ok(!app.selected.includes('messages'));assert.ok(!app.selected.includes('project'));
});
