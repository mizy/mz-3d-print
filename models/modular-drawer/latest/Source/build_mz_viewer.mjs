import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";

const base=path.dirname(fileURLToPath(import.meta.url));
const [root,tgz,releaseMeta,repo]=process.argv.slice(2).map(x=>path.resolve(x));
const manifest=JSON.parse(fs.readFileSync(path.join(root,"package.json")));
const latest=JSON.parse(fs.readFileSync(releaseMeta));
const integrity="sha512-"+createHash("sha512").update(fs.readFileSync(tgz)).digest("base64");
if(manifest.name!=="@mizy/mz-3d-viewer"||manifest.version!==latest.version||manifest.gitHead!==latest.gitHead||integrity!==latest["dist.integrity"])throw new Error("Scope, version, source revision or registry package integrity does not match");
const upstream=execFileSync("git",["-C",repo,"rev-parse","HEAD"],{encoding:"utf8"}).trim();
if(upstream!==manifest.gitHead||execFileSync("git",["-C",repo,"status","--porcelain","--","src","LICENSE"],{encoding:"utf8"}).trim())throw new Error("Native chrome source must be clean and match package Git head");
const load=createRequire(path.join(repo,"package.json"));
const esbuild=load(load.resolve("esbuild",{paths:[path.dirname(load.resolve("vite/package.json"))]}));
const three=JSON.parse(fs.readFileSync(path.join(repo,"node_modules/three/package.json")));
const entry=path.join(root,"dist-lib/index.js");
const workerPattern=/new Worker\(new URL\(\s*\/\* @vite-ignore \*\/\s*new URL\("(assets\/edges\.worker-[^"]+\.js)", import\.meta\.url\)\.href,\s*"" \+ import\.meta\.url\s*\), \{ type: "module" \}\)/g;
let patchedPackage=false;
const plugin={name:"offline-package-and-native-chrome",setup(b){
 b.onLoad({filter:/\/dist-lib\/index\.js$/},({path:file})=>{
  if(fs.realpathSync(file)!==fs.realpathSync(entry))return;
  patchedPackage=true;
  let data=fs.readFileSync(file,"utf8"), count=0;
  data=data.replace(workerPattern,(_match,worker)=>{
   count++;
   const content=fs.readFileSync(path.join(root,"dist-lib",worker),"utf8").replace(/\/\/# sourceMappingURL=.*$/gm,"");
   return '(() => {const key=Symbol.for("mz.review.published-edge-worker"); const url=globalThis[key] ??= URL.createObjectURL(new Blob(['+JSON.stringify(content)+'], {type:"text/javascript"})); return new Worker(url)})()';
  });
  if(count!==1)throw new Error("Published edge worker wrapper changed");
  return {contents:data,loader:"js",resolveDir:path.dirname(file)};
 });
 b.onLoad({filter:/\/contextMenu\.ts$/},({path:file})=>{
  let data=fs.readFileSync(file,"utf8");
  if(!data.includes("pressed = event.button === 2 ?"))throw new Error("Native context menu handler changed");
  data=data.replace("pressed = event.button === 2 ?","pressed = event.button === 2 && canvas.contains(event.target as Node) ?");
  data=data.replace("const hit = await stage.pick(clientX, clientY);","const hit = await stage.pick(clientX, clientY).catch(() => null);");
  return {contents:data,loader:"ts",resolveDir:path.dirname(file)};
 });
}};
const out=path.join(base,"mz-viewer.runtime.js");
const license=["LICENSE","dist-lib/LICENSE.three.txt"].map(x=>fs.readFileSync(path.join(root,x),"utf8")).join("\n");
const result=await esbuild.build({absWorkingDir:repo,entryPoints:[path.join(base,"mz-viewer-entry.ts")],outfile:out,bundle:true,format:"iife",platform:"browser",target:"es2022",minify:true,legalComments:"none",metafile:true,
 nodePaths:[path.join(repo,"node_modules")],
 alias:{"@mizy/mz-3d-viewer":entry,"@mz/report-click":path.join(repo,"src/ui/canvasSelection.ts"),"@mz/report-menu":path.join(repo,"src/ui/contextMenu.ts"),"@mz/report-nav":path.join(repo,"src/ui/navCube.ts")},
 plugins:[plugin],define:{"import.meta.url":"document.baseURI"},
 banner:{js:"/* "+manifest.name+"@"+manifest.version+" from GitHub Packages\n"+license+" */"}});
const inputs=Object.keys(result.metafile.inputs);
if(!patchedPackage||!inputs.some(x=>x.includes("package-tree/package/dist-lib/index.js")||path.resolve(repo,x)===entry)||!inputs.some(x=>x.endsWith("src/ui/navCube.ts"))||Object.values(result.metafile.outputs).some(o=>o.imports.length))throw new Error("Not a self-contained bundle of the verified package");
const buf=fs.readFileSync(out);
fs.writeFileSync(path.join(base,"mz-viewer-runtime.json"), JSON.stringify({library:manifest.name,version:manifest.version,revision:manifest.gitHead,integrity,registry:"https://npm.pkg.github.com",renderer:"WebGPU",three:three.version,esbuild:esbuild.version,byteLength:buf.length,sha256:createHash("sha256").update(buf).digest("hex"),offline:true,uiSources:"matching release commit: native NavCube and context menu",meshSource:"current signed STEP mesh"},null,2)+"\n");
