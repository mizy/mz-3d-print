// 生成索引页：扫描 models/<dir>/MODEL.json + 目录内文件 → index.html + models.json
// 用法：bun tools/build-site.mjs（或 node tools/build-site.mjs）
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MODELS = path.join(ROOT, "models");

const CLS_LABEL = {
  original: "原创",
  derived: "改造",
  tool: "样片",
};
const CLS_DESC = {
  original: "自建几何 / 参数化脚本，从零建模",
  derived: "基于第三方或 AI 生成网格，我们做切割、分件、支撑、朝向与装配",
  tool: "脚本试验样片，不是独立设计",
};
const KIND_LABEL = { ".stl": "STL", ".3mf": "3MF", ".step": "STEP", ".stp": "STEP", ".obj": "OBJ", ".scad": "SCAD", ".zip": "ZIP" };

function walk(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(p));
    else out.push(p);
  }
  return out.sort();
}

function isCover(rel) {
  return /preview|预览|cover|预览图/i.test(rel) && /\.(png|jpe?g|webp)$/i.test(rel);
}
function isImage(rel) {
  return /\.(png|jpe?g|webp)$/i.test(rel);
}
function isModel(rel) {
  return /\.(stl|3mf|step|stp|obj|scad|zip)$/i.test(rel);
}
function isHtml(rel) {
  return /\.html?$/i.test(rel);
}
// HTML 资产的链接文字取页面自己的 <title>；没有 title 时退回「模型名 + 文件名」。
function pageTitle(abs) {
  const head = fs.readFileSync(abs, "utf8").slice(0, 20000);
  const match = head.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return match ? match[1].replace(/\s+/g, " ").trim() : "";
}
const shortLabel = (text, max = 40) => (text.length > max ? `${text.slice(0, max - 1)}…` : text);

const enc = (rel) => rel.split("/").map(encodeURIComponent).join("/");
const human = (n) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);

const tracked = new Set(execFileSync("git", ["ls-files", "-z"], {cwd: ROOT, encoding: "utf8"}).split("\0").filter(Boolean));
const isTracked = (file) => tracked.has(path.relative(ROOT, file)) || tracked.has(path.relative(ROOT, fs.realpathSync(file)));
const models = [];
for (const dir of fs.readdirSync(MODELS, { withFileTypes: true })) {
  if (!dir.isDirectory()) continue;
  const abs = path.join(MODELS, dir.name);
  const metaPath = path.join(abs, "MODEL.json");
  if (!fs.existsSync(metaPath)) continue;
  const meta = JSON.parse(fs.readFileSync(metaPath, "utf8"));
  const files = walk(abs).filter(isTracked)
    .map((f) => path.relative(abs, f))
    .filter((r) => !r.endsWith("MODEL.json") && !(dir.name === "modular-drawer" && r.startsWith("History/")))
    .map((r) => ({ rel: r, size: fs.statSync(path.join(abs, r)).size }));
  const cover = meta.cover ? files.find(f => f.rel === meta.cover && isImage(f.rel)) : null;
  if (meta.cover && !cover) throw new Error(`${dir.name}: cover is missing or untracked: ${meta.cover}`);
  for (const rel of [...(meta.downloads ?? []), ...(meta.gallery ?? [])]) {
    if (!files.some(f => f.rel === rel)) throw new Error(`${dir.name}: selected file is missing or untracked: ${rel}`);
  }
  models.push({
    ...meta,
    dir: dir.name,
    cover: cover ? `${dir.name}/${cover.rel}` : null,
    files: files.map((f) => ({ ...f, url: `models/${dir.name}/${f.rel}` })),
    bytes: files.reduce((s, f) => s + f.size, 0),
  });
}
models.sort((a, b) => String(a.id).localeCompare(String(b.id), "zh"));

for (const m of models) {
  const html = m.files.filter((f) => isHtml(f.rel)).map((f) => ({
    rel: `models/${m.dir}/${f.rel}`,
    size: f.size,
    title: pageTitle(path.join(MODELS, m.dir, f.rel)),
  }));
  if (html.length) m.html = html;
}
const htmlAssets = models.flatMap((m) => (m.html ?? []).map((a) => ({ ...a, modelTitle: m.title })));

fs.writeFileSync(path.join(ROOT, "models.json"), JSON.stringify(models, null, 2));

const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const assetUrl = (rel) => {
  // GitHub Pages does not serve Git LFS content. Use the LFS media endpoint.
  const resolved = path.relative(ROOT, fs.realpathSync(path.join(ROOT, rel)));
  if (resolved.startsWith("..") || path.isAbsolute(resolved)) throw new Error(`Asset escapes repository: ${rel}`);
  const attr = execFileSync("git", ["check-attr", "filter", "--", resolved], {cwd: ROOT, encoding: "utf8"}).trim();
  return attr.endsWith(": lfs") ? `https://media.githubusercontent.com/media/mizy/mz-3d-print/main/${enc(resolved)}` : enc(resolved);
};
const publicLabel = (name) => name.replace(/miao[ _.-]*zhuang|zhuang[ _.-]*miao|苗壮|苗壯/gi, "personal");
const card = (m) => {
  const hasCurrentModels = m.files.some(f => f.rel.startsWith("Models/"));
  const selected = Array.isArray(m.downloads) ? new Set(m.downloads) : null;
  const models_ = m.files.filter((f) => isModel(f.rel) && (selected ? selected.has(f.rel) : (!hasCurrentModels || f.rel.startsWith("Models/"))));
  const partLabels = {"clip_fit_coupon.stl":"卡扣配合小样", "whole_bowl_AMS.stl":"整碗几何（STL不含颜色配置）", "ivory_bottom_z0_2.stl":"奶白底层 0–2 mm", "blue_middle_z2_28.stl":"蓝色主体 2–28 mm", "ivory_top_z28_30.stl":"奶白顶层 28–30 mm", "ivory_logo_print_flat.stl":"Logo 平放打印件", "ivory_glue_logo.stl":"Logo 装配位置参考"};
  const fileItem = f => {
    const name = path.basename(f.rel);
    const label = partLabels[name];
    return `<li><a href="${assetUrl(`models/${m.dir}/${f.rel}`)}" download>${label ? `${esc(label)}<small>${esc(name)}</small>` : esc(publicLabel(f.rel))}</a><span>${KIND_LABEL[path.extname(f.rel).toLowerCase()] ?? ""} ${human(f.size)}</span></li>`;
  };
  const groups = Array.isArray(m.downloadGroups) ? m.downloadGroups : [];
  const grouped = groups.map(g => ({...g, files: models_.filter(f => f.rel.startsWith(g.prefix))})).filter(g => g.files.length);
  const ungrouped = models_.filter(f => !grouped.some(g => g.files.includes(f)));
  const downloadHtml = grouped.map(g => `<section class="download-group"><h3>${esc(g.label)}</h3>${g.note ? `<p class="group-note">${esc(g.note)}</p>` : ""}<ul class="files">${g.files.map(fileItem).join("")}</ul></section>`).join("") + (ungrouped.length ? `<ul class="files">${ungrouped.map(fileItem).join("")}</ul>` : "");
  const gallery = new Set(m.gallery ?? []);
  const imgs = m.files.filter(f => isImage(f.rel) && gallery.has(f.rel) && `${m.dir}/${f.rel}` !== m.cover);
  const others = m.files.filter(f => !models_.includes(f) && !imgs.includes(f) && !isHtml(f.rel) && `${m.dir}/${f.rel}` !== m.cover);
  const htmls = m.html ?? [];
  const htmlLinks = htmls.length
    ? `<div class="html-links"><h3>网页资料（${htmls.length}）</h3>${htmls
        .map((a) => `<a href="${assetUrl(a.rel)}">${esc(a.title || shortLabel(`${m.title} · ${path.basename(a.rel)}`))}<small>${esc(a.rel)} · ${human(a.size)}</small></a>`)
        .join("")}</div>`
    : "";
  return `<article id="model-${esc(m.id)}" class="card" data-cls="${esc(m.cls)}" data-id="${esc(m.id)}" data-text="${encodeURIComponent(
    [m.title, m.category, m.id, ...m.files.map((f) => f.rel), ...(m.html ?? []).map((a) => a.title)].join(" ")
  )}">
  <a class="thumb" href="${m.cover ? assetUrl(`models/${m.cover}`) : `#model-${esc(m.id)}`}">
    ${m.cover ? `<img loading="lazy" src="${assetUrl(`models/${m.cover}`)}" alt="${esc(m.title)}">` : `<div class="noimg">无预览</div>`}
  </a>
  <div class="body">
    <h2>${esc(m.title)}</h2>
    ${m.release ? `<p class="rel"><a href="${esc(m.release)}">⬇ 完整工程 / 大文件（Release 资产）</a></p>` : ""}
    <p class="meta"><span class="badge ${esc(m.cls)}">${CLS_LABEL[m.cls] ?? m.cls}</span> ${esc(m.category)} · ${esc(m.id)} · ${human(m.bytes)}</p>
    ${m.summary ? `<p class="sum">${esc(m.summary)}</p>` : ""}
    ${models_.length ? `<details class="downloads"><summary>当前模型 <span>${models_.length} 个 · 展开下载</span></summary>${downloadHtml}</details>` : `<p class="group-note">${m.release ? "完整工程请从上方 Release 获取。" : "暂无当前模型下载。"}</p>`}
    ${htmlLinks}
    ${
      others.length
        ? `<details><summary>设计文档与历史资料（${others.length}）</summary><ul class="files dim">${others
            .map((f) => `<li><a href="${assetUrl(`models/${m.dir}/${f.rel}`)}">${esc(publicLabel(f.rel))}</a><span>${human(f.size)}</span></li>`)
            .join("")}</ul></details>`
        : ""
    }
    ${
      imgs.length
        ? `<details><summary>当前预览（${imgs.length}）</summary><ul class="files dim">${imgs
            .map((f) => `<li><a href="${assetUrl(`models/${m.dir}/${f.rel}`)}">${esc(f.rel)}</a></li>`)
            .join("")}</ul></details>`
        : ""
    }
  </div>
</article>`;
};

const htmlNav = htmlAssets
  .map((a) => {
    const label = a.title || `${a.modelTitle} · ${path.basename(a.rel)}`;
    return `<a class="html-resource" href="${assetUrl(a.rel)}" title="${esc(a.rel)}">网页 · ${esc(shortLabel(label))}</a>`;
  })
  .join("");

const html = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>3D 打印模型库</title>
<meta name="description" content="3D 打印模型与改造件索引：原创设计、改造件与参数记录，直接下载 STL / 3MF。">
<meta name="theme-color" content="#0f1115">
<link rel="manifest" href="manifest.json">
<link rel="icon" href="assets/icons/icon.svg" type="image/svg+xml">
<link rel="icon" href="assets/icons/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="assets/icons/apple-touch-icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="3D 打印">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip" href="#grid">跳到模型列表</a>
<header>
  <div class="topline"><h1>3D 打印模型库</h1><a class="repo" href="https://github.com/mizy/mz-3d-print">GitHub ↗</a></div>
  <p class="lead">模型、设计图和试错记录。打印机：Bambu Lab P1S · AMS</p>
  <nav class="resources" aria-label="资料导航"><a href="https://github.com/mizy/mz-3d-print/tree/main/models">项目目录</a><a href="https://github.com/mizy/mz-3d-print/tree/main/models/dog-bowl-shared">狗碗共享资料</a>${htmlNav}</nav>
  <p class="notice">来源与打印验证状态见各项目说明。<a href="README.md">仓库说明 ↗</a></p>
</header>
<section class="catalog" aria-label="模型筛选">
  <div class="catalog-heading"><h2>全部项目</h2><span id="count" aria-live="polite">${models.length} 个项目</span></div>
  <div class="bar"><label class="search"><span>⌕</span><input id="q" type="search" aria-label="搜索模型名称、分类或文件名" placeholder="搜索名称、分类、文件名…" autocomplete="off"></label>
  <div class="filters" role="group" aria-label="来源类别">
    <button data-f="all" aria-pressed="true">全部</button>
    <button data-f="original" aria-pressed="false">原创</button>
    <button data-f="derived" aria-pressed="false">改造</button>
    <button data-f="tool" aria-pressed="false">样片</button>
  </div></div>
</section>
<main id="grid">
${models.map(card).join("\n")}
<div class="empty" id="empty" hidden><h2>没有找到匹配的项目</h2><p>试试其他关键词，或清除筛选。</p><button id="reset">查看全部模型</button></div>
</main>
<footer>
  生成时间 ${new Date().toISOString().slice(0, 10)} · 共 ${models.length} 个项目 · 文件大小按目录引用合计（含重复引用）
  · 索引由 <code>tools/build-site.mjs</code> 从 <code>models/*/MODEL.json</code> 生成 · 打印机：Bambu Lab P1S
</footer>
<script>
  const q = document.getElementById('q'), grid = document.getElementById('grid'), empty = document.getElementById('empty');
  let cls = 'all';
  const cards = [...grid.querySelectorAll('.card')];
  function apply() {
    const s = q.value.trim().toLowerCase();
    let shown = 0;
    for (const c of cards) {
      const text = decodeURIComponent(c.dataset.text).toLowerCase();
      const ok = (cls === 'all' || c.dataset.cls === cls) && (!s || text.includes(s));
      c.hidden = !ok;
      if (ok) shown++;
    }
    empty.hidden = shown > 0;
    document.getElementById("count").textContent = shown + " / " + cards.length + " 个项目";
  }
  q.addEventListener('input', apply);
  document.getElementById('reset').addEventListener('click', () => { q.value = ''; document.querySelector('[data-f=all]').click(); q.focus(); });
  for (const b of document.querySelectorAll('.filters button')) {
    b.addEventListener('click', () => {
      cls = b.dataset.f;
      for (const x of document.querySelectorAll('.filters button')) x.setAttribute('aria-pressed', String(x === b));
      apply();
    });
  }
</script>
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('sw.js', { scope: '/mz-3d-print/' }).catch((error) => {
        console.warn('[pwa] service worker registration failed', error);
      });
    });
  }
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(ROOT, "index.html"), html.replace(/[ \t]+$/gm, ""));
console.log(`index.html 已生成：${models.length} 个模型，共 ${human(models.reduce((s, m) => s + m.bytes, 0))}`);
