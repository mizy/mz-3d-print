const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const room=path.resolve(process.argv[2]||'.');
(async()=>{const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH, headless:true,args:['--enable-unsafe-webgpu']});
try{
 const p=await b.newPage({viewport:{width:1280,height:900}}),err=[],net=[];
 p.on('pageerror',e=>err.push(e.message));p.on('request',r=>{if(/^https?:/.test(r.url()))net.push(r.url())});await p.route(/^https?:\/\//,r=>r.abort());await p.goto(pathToFileURL(path.join(room,'index.html')).href);
 const d=JSON.parse(await p.locator('#cad-data').textContent()),sha=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
 assert.equal(d.parts.assembly.nSolids,19);assert.deepEqual(d.parts.assembly.extent,[172,240,102.7]);assert.equal(d.parts.coupon.nSolids,4);assert.equal(d.parts.two_bay.nSolids,35);assert.equal(d.parts.expansion.nSolids,17);
 for(const x of Object.values(d.parts))assert.equal(sha(path.join(room,'STEP',x.name)),x.sha256);
 assert.equal(sha(path.join(room,d.expansion.print_3mf.path)),d.expansion.print_3mf.sha256);
 const axis={side:[1,2],side_top:[1,0],rear_end:[0,2],front:[0,2],top:[0,1]};
 assert.equal(d.panels.length,9);assert.equal(d.panels.find(x=>x.id==='rear').anchor.length,5);
 for(const s of d.panels){
  const figs=p.locator('#sheet-'+s.id+' svg');assert.equal(await figs.count(),s.views.length);
  assert.equal(await figs.evaluateAll(x=>new Set(x.map(v=>v.dataset.mmScale)).size),1);
  assert.equal(await p.locator('#sheet-'+s.id+' .anchor-label').count(),s.anchor.length);
  for(const v of s.views)for(const [i,a] of axis[v.key].entries())assert(Math.abs(v.extent[i]-s.extent[a])<=.00001,[s.id,v.key,v.extent[i],s.extent[a]]);
 }
 for(const id of ['rod','lowerrod']) for(const key of ['front','top']){
  const v=d.panels.find(x=>x.id===id).views.find(x=>x.key===key);
  const silhouette=v.layers[0].filter(line=>{
   const xx=line.map(p=>p[0]),yy=line.map(p=>p[1]);
   return Math.max(...xx)-Math.min(...xx)>7 && Math.max(...yy)-Math.min(...yy)<.0001;
  });
  assert(silhouette.length>=2,id+' '+key+' missing cylindrical shaft silhouette');
 }
 const rv=d.panels.find(x=>x.id==='rear').views.find(x=>x.key==='rear_end'),circs=rv.visible_full_circles.filter(c=>Math.abs(c[2]-4.28)<1e-5);
 assert.equal(circs.length,2);assert.equal(rv.hidden_full_circles.length,2);
 const fv=d.panels.find(x=>x.id==='rear').views.find(x=>x.key==='front');assert.equal(fv.hidden_full_circles.length,2);assert.equal(fv.visible_full_circles.filter(c=>Math.abs(c[2]-4.28)<1e-5).length,2);
 assert.equal(await p.locator('#sheet-rear .cad-hidden-circle').count(),4);assert(Math.abs(Math.abs(circs[1][0]-circs[0][0])-120.9)<.001);assert.equal(circs[0][1],circs[1][1]);
 await p.waitForFunction(()=>document.querySelector('#scene').dataset.visibleParts==='19',null,{timeout:60000});
 assert.equal(await p.locator('#scene').getAttribute('data-renderer'),'webgpu');assert(await p.locator('#navCube .cube-region').count()>10);
 await p.waitForFunction(()=>document.querySelector('#scene').dataset.displayMode==='edges'&&Number(document.querySelector('#scene').dataset.edgeMeshes)>0);
 for(const [id,n] of [['rear','1'],['coupon','4'],['expansion','17'],['two_bay','35'],['rod','1']]){
  await p.locator('#part').selectOption(id);await p.waitForFunction(ct=>document.querySelector('#scene').dataset.visibleParts===ct,n);
 }
 await p.locator('#scene').scrollIntoViewIfNeeded();const r=await p.locator('#scene').boundingBox(),xy=[r.x+r.width*.50,r.y+r.height*.50];
 await p.mouse.move(...xy);await p.waitForFunction(()=>document.querySelector('#scene').dataset.hoveredPart!=='',null,{timeout:12000});
 await p.mouse.click(...xy);await p.waitForFunction(()=>document.querySelector('#scene').dataset.selectedPart==='0',null,{timeout:12000});
 await p.mouse.click(...xy,{button:'right'});await p.getByRole('menuitem',{name:'隐藏此部件'}).waitFor({timeout:12000});
 await p.keyboard.press('Escape');
 assert(!/背插键|止退片/.test(await p.locator('main').innerText()),(await p.locator('main').innerText()).split('\n').filter(l=>/背插键|止退片/.test(l)).join(' | '));
 assert.deepEqual(err,[]);assert.deepEqual(net,[]);
 if(process.env.CHECK_DRAWINGS_DIR){
  for(const {id:s} of d.panels)await p.locator('#sheet-'+s).screenshot({path:path.join(process.env.CHECK_DRAWINGS_DIR,s+'.png')});
 }
 const fallback=await b.newPage();await fallback.addInitScript(()=>Object.defineProperty(navigator,'gpu',{configurable:true,value:undefined}));await fallback.goto(pathToFileURL(path.join(room,'index.html')).href);
 assert.equal(await fallback.locator('#sheets .sheet').count(),9);
 console.log('PASS orthographic BRep extents and equal scales, live leaders, two exact rear cam mouths, all current STEP/3MF digests, offline WebGPU selection/context/edges/NavCube, fallback, and latest-only links.');
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
