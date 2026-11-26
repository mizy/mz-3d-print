// 发布前自检：页面引用的本地文件、manifest 图标、Service Worker 预缓存清单必须都存在。
// 用法：node tools/check-site.mjs
// 任何一项不一致都以非零码退出，让 CI 直接拦下这次发布。

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const problems = [];
const fail = (message) => problems.push(message);

const read = (file) => fs.readFileSync(path.join(ROOT, file), "utf8");
const exists = (file) => fs.existsSync(path.join(ROOT, file));

function checkIndexLinks() {
  const html = read("index.html");
  if (!/class="card"/.test(html)) fail("index.html has no model cards");

  // 只校验站内相对链接；LFS 文件走 media.githubusercontent.com 绝对地址，不在发布产物的检查范围。
  const refs = new Set();
  for (const match of html.matchAll(/(?:href|src)="([^"#?]+)"/g)) {
    const ref = match[1];
    if (/^[a-z]+:/i.test(ref) || ref.startsWith("//")) continue;
    if (ref.startsWith("/")) {
      fail(`index.html uses a root-absolute link; project Pages must stay relocatable: ${ref}`);
      continue;
    }
    refs.add(ref);
  }
  for (const ref of refs) {
    if (!exists(decodeURIComponent(ref))) fail(`index.html references a missing file: ${ref}`);
  }
}

function checkManifest() {
  const manifest = JSON.parse(read("manifest.json"));
  for (const key of ["name", "short_name", "start_url", "scope", "display"]) {
    if (!manifest[key]) fail(`manifest.json missing ${key}`);
  }
  if (manifest.start_url !== "/mz-3d-print/" || manifest.scope !== "/mz-3d-print/") {
    fail("manifest.json must be scoped to /mz-3d-print/");
  }
  const sizes = (manifest.icons ?? []).map((icon) => `${icon.sizes}:${icon.purpose ?? "any"}`);
  if (!sizes.includes("192x192:any")) fail("manifest.json needs a 192x192 any icon");
  if (!sizes.includes("512x512:any")) fail("manifest.json needs a 512x512 any icon");
  if (!manifest.icons.some((icon) => (icon.purpose ?? "any").includes("maskable"))) {
    fail("manifest.json needs a maskable icon");
  }
  for (const icon of manifest.icons ?? []) {
    if (!exists(icon.src)) fail(`manifest icon missing: ${icon.src}`);
  }
}

function checkServiceWorker() {
  const source = read("sw.js");
  const listed = [...source.matchAll(/^\s*'(\/[^']*)',?$/gm)].map((match) => match[1]);
  if (listed.length === 0) fail("sw.js has no precache URLs");
  for (const url of listed) {
    if (!url.startsWith("/mz-3d-print/")) fail(`sw.js precaches a path outside the site scope: ${url}`);
    const relative = url.replace(/^\/mz-3d-print\//, "");
    const full = relative === "" || relative.endsWith("/") ? `${relative}index.html` : relative;
    if (!exists(full)) fail(`sw.js precaches a missing path: ${url}`);
  }
}

checkIndexLinks();
checkManifest();
checkServiceWorker();

if (problems.length > 0) {
  console.error(problems.map((problem) => `FAIL ${problem}`).join("\n"));
  process.exit(1);
}
console.log("site check passed");
