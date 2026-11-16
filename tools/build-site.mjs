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

const enc = (rel) => rel.split("/").map(encodeURIComponent).join("/");
const human = (n) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);

const models = [];
for (const dir of fs.readdirSync(MODELS, { withFileTypes: true })) {
  if (!dir.isDirectory()) continue;
  const abs = path.join(MODELS, dir.name);
  const metaPath = path.join(abs, "MODEL.json");
  if (!fs.existsSync(metaPath)) continue;
  const meta = JSON.parse(fs.readFileSync(metaPath, "utf8"));
  const files = walk(abs)
    .map((f) => path.relative(abs, f))
    .filter((r) => !r.endsWith("MODEL.json"))
    .map((r) => ({ rel: r, size: fs.statSync(path.join(abs, r)).size }));
  const cover = files.find((f) => f.rel === meta.cover) ?? files.find((f) => isCover(f.rel)) ?? files.find((f) => isImage(f.rel));
  models.push({
    ...meta,
    dir: dir.name,
    cover: cover ? `${dir.name}/${cover.rel}` : null,
    files: files.map((f) => ({ ...f, url: `models/${dir.name}/${f.rel}` })),
    bytes: files.reduce((s, f) => s + f.size, 0),
  });
}
models.sort((a, b) => String(a.id).localeCompare(String(b.id), "zh"));

fs.writeFileSync(path.join(ROOT, "models.json"), JSON.stringify(models, null, 2));

const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const assetUrl = (rel) => {
  // GitHub Pages does not serve Git LFS content. Use the LFS media endpoint.
  const resolved = path.relative(ROOT, fs.realpathSync(path.join(ROOT, rel)));
  if (resolved.startsWith("..") || path.isAbsolute(resolved)) throw new Error(`Asset escapes repository: ${rel}`);
  const attr = execFileSync("git", ["check-attr", "filter", "--", resolved], {cwd: ROOT, encoding: "utf8"}).trim();
  return attr.endsWith(": lfs") ? `https://media.githubusercontent.com/media/mizy/mz-3d-print/main/${enc(resolved)}` : enc(resolved);
};
const card = (m) => {
  const hasCurrentModels = m.files.some(f => f.rel.startsWith("Models/"));
  const models_ = m.files.filter((f) => isModel(f.rel) && (!hasCurrentModels || f.rel.startsWith("Models/")));
  const others = m.files.filter((f) => (!isModel(f.rel) || (hasCurrentModels && !f.rel.startsWith("Models/"))) && !isImage(f.rel) && !f.rel.endsWith("MODEL.json"));
  const imgs = m.files.filter((f) => isImage(f.rel) && `${m.dir}/${f.rel}` !== m.cover);
  return `<article id="model-${esc(m.id)}" class="card" data-cls="${esc(m.cls)}" data-id="${esc(m.id)}" data-text="${encodeURIComponent(
    [m.title, m.category, m.id, ...m.files.map((f) => f.rel)].join(" ")
  )}">
  <a class="thumb" href="${m.cover ? assetUrl(`models/${m.cover}`) : `#model-${esc(m.id)}`}">
    ${m.cover ? `<img loading="lazy" src="${assetUrl(`models/${m.cover}`)}" alt="${esc(m.title)}">` : `<div class="noimg">无预览</div>`}
  </a>
  <div class="body">
    <h2>${esc(m.title)}</h2>
    ${m.release ? `<p class="rel"><a href="${m.release}">⬇ 完整工程 / 大文件（Release 资产）</a></p>` : ""}
    <p class="meta"><span class="badge ${esc(m.cls)}">${CLS_LABEL[m.cls] ?? m.cls}</span> ${esc(m.category)} · ${esc(m.id)} · ${human(m.bytes)}</p>
    ${m.summary ? `<p class="sum">${esc(m.summary)}</p>` : ""}
    <details class="downloads"><summary>模型文件 <span>${models_.length} 个 · 展开下载</span></summary><ul class="files">
      ${models_
        .map(
          (f) =>
            `<li><a href="${assetUrl(`models/${m.dir}/${f.rel}`)}" download>${esc(f.rel.split("/").pop())}</a><span>${KIND_LABEL[path.extname(f.rel).toLowerCase()] ?? ""} ${human(f.size)}</span></li>`
        )
        .join("\n      ")}
    </ul></details>
    ${
      others.length
        ? `<details><summary>其他文件（${others.length}）</summary><ul class="files dim">${others
            .map((f) => `<li><a href="${assetUrl(`models/${m.dir}/${f.rel}`)}">${esc(f.rel)}</a><span>${human(f.size)}</span></li>`)
            .join("")}</ul></details>`
        : ""
    }
    ${
      imgs.length
        ? `<details><summary>预览图（${imgs.length}）</summary><ul class="files dim">${imgs
            .map((f) => `<li><a href="${assetUrl(`models/${m.dir}/${f.rel}`)}">${esc(f.rel.split("/").pop())}</a></li>`)
            .join("")}</ul></details>`
        : ""
    }
  </div>
</article>`;
};

const html = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>苗壮的 3D 打印模型库</title>
<meta name="description" content="3D 打印模型与改造件索引：原创设计、改造件与参数记录，直接下载 STL / 3MF。">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip" href="#grid">跳到模型列表</a>
<header>
  <div class="topline"><a class="brand" href="./">MZ<span> / </span>3D PRINT</a><a class="repo" href="https://github.com/mizy/mz-3d-print">GitHub 仓库 ↗</a></div>
  <div class="hero"><div><p class="eyebrow">THE PERSONAL WORKSHOP · 个人打印工坊</p><h1>从想法，<br>到手里的实物<span>。</span></h1><p class="lead">苗壮的 3D 打印模型库。把模型、设计过程与试错记录放在一起，让每一次迭代都有迹可循。</p></div>
  <div class="workshop"><span class="machine">BAMBU LAB P1S / AMS</span><strong>${models.length}<small>个模型项目</small></strong><div class="formats">STL · 3MF · STEP · 设计文档</div></div></div>
  <p class="notice"><span>关于来源</span> 并非全部原创；各项目标注原创、改造或样片。打印设置与验证状态以项目文档为准。<a href="README.md">阅读说明 ↗</a></p>
</header>
<section class="catalog" aria-label="模型筛选">
  <div class="catalog-heading"><h2>模型与实验</h2><span id="count" aria-live="polite">${models.length} 个项目</span></div>
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
  生成时间 ${new Date().toISOString().slice(0, 10)} · 共 ${models.length} 个模型 / ${human(models.reduce((s, m) => s + m.bytes, 0))}
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
</body>
</html>
`;

fs.writeFileSync(path.join(ROOT, "index.html"), html.replace(/[ \t]+$/gm, ""));
console.log(`index.html 已生成：${models.length} 个模型，共 ${human(models.reduce((s, m) => s + m.bytes, 0))}`);
