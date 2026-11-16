// 生成索引页：扫描 models/<dir>/MODEL.json + 目录内文件 → index.html + models.json
// 用法：bun tools/build-site.mjs（或 node tools/build-site.mjs）
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(import.meta.dir, "..");
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
  const cover = files.find((f) => isCover(f.rel)) ?? files.find((f) => isImage(f.rel));
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

const card = (m) => {
  const models_ = m.files.filter((f) => isModel(f.rel));
  const others = m.files.filter((f) => !isModel(f.rel) && !isImage(f.rel) && !f.rel.endsWith("MODEL.json"));
  const imgs = m.files.filter((f) => isImage(f.rel) && f.rel !== m.cover);
  return `<article class="card" data-cls="${m.cls}" data-id="${m.id}" data-text="${encodeURIComponent(
    [m.title, m.category, m.id, ...m.files.map((f) => f.rel)].join(" ")
  )}">
  <a class="thumb" href="models/${enc(m.dir)}/${m.cover ? enc(m.cover.split("/").slice(1).join("/")) : ""}">
    ${m.cover ? `<img loading="lazy" src="models/${enc(m.cover)}" alt="${m.title}">` : `<div class="noimg">无预览</div>`}
  </a>
  <div class="body">
    <h2>${m.title}</h2>
    ${m.release ? `<p class="rel"><a href="${m.release}">⬇ 完整工程 / 大文件（Release 资产）</a></p>` : ""}
    <p class="meta"><span class="badge ${m.cls}">${CLS_LABEL[m.cls] ?? m.cls}</span> ${m.category} · ${m.id} · ${human(m.bytes)}</p>
    ${m.summary ? `<p class="sum">${m.summary}</p>` : ""}
    <ul class="files">
      ${models_
        .map(
          (f) =>
            `<li><a href="models/${enc(m.dir)}/${enc(f.rel)}" download>${f.rel.split("/").pop()}</a><span>${KIND_LABEL[path.extname(f.rel).toLowerCase()] ?? ""} ${human(f.size)}</span></li>`
        )
        .join("\n      ")}
    </ul>
    ${
      others.length
        ? `<details><summary>其他文件（${others.length}）</summary><ul class="files dim">${others
            .map((f) => `<li><a href="models/${enc(m.dir)}/${enc(f.rel)}">${f.rel}</a><span>${human(f.size)}</span></li>`)
            .join("")}</ul></details>`
        : ""
    }
    ${
      imgs.length
        ? `<details><summary>预览图（${imgs.length}）</summary><ul class="files dim">${imgs
            .map((f) => `<li><a href="models/${enc(m.dir)}/${enc(f.rel)}">${f.rel.split("/").pop()}</a></li>`)
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
<style>
  :root{--bg:#0f1115;--fg:#e6e8ee;--dim:#8b93a7;--card:#171a21;--line:#252a35;--acc:#7ad0a1;--warn:#e0b062}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",Arial,sans-serif}
  header{padding:34px 20px 18px;border-bottom:1px solid var(--line)}
  h1{margin:0 0 6px;font-size:22px}
  .lead{margin:0;color:var(--dim);max-width:760px}
  .lead b{color:var(--acc)}
  .bar{position:sticky;top:0;z-index:5;background:rgba(15,17,21,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:10px 20px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
  input{flex:1 1 240px;min-width:180px;background:#101318;border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 12px;font-size:14px}
  .filters button{background:#101318;border:1px solid var(--line);color:var(--dim);border-radius:999px;padding:6px 12px;font-size:13px;cursor:pointer}
  .filters button[aria-pressed="true"]{border-color:var(--acc);color:var(--acc)}
  main{padding:20px;display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));max-width:1400px;margin:0 auto}
  .card{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;display:flex;flex-direction:column}
  .thumb{display:block;aspect-ratio:16/10;background:#0b0d11;overflow:hidden}
  .thumb img{width:100%;height:100%;object-fit:cover;display:block}
  .noimg{display:flex;align-items:center;justify-content:center;height:100%;color:var(--dim);font-size:13px}
  .body{padding:14px 16px 16px;display:flex;flex-direction:column;gap:8px}
  h2{margin:0;font-size:16px;line-height:1.35}
  .meta{margin:0;color:var(--dim);font-size:12.5px}
  .badge{display:inline-block;border-radius:6px;padding:1px 6px;font-size:12px;margin-right:4px}
  .badge.original{background:rgba(122,208,161,.16);color:var(--acc);border:1px solid rgba(122,208,161,.35)}
  .badge.derived{background:rgba(224,176,98,.14);color:var(--warn);border:1px solid rgba(224,176,98,.35)}
  .badge.tool{background:rgba(139,147,167,.14);color:var(--dim);border:1px solid var(--line)}
  .sum{margin:0;color:#b9c0d0;font-size:13.5px}
  .rel{margin:0}
  .rel a{display:inline-block;background:rgba(122,208,161,.12);border:1px solid rgba(122,208,161,.4);color:var(--acc);text-decoration:none;border-radius:8px;padding:6px 10px;font-size:13px}
  .rel a:hover{background:rgba(122,208,161,.2)}
  .files{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px}
  .files li{display:flex;justify-content:space-between;gap:10px;font-size:13px;border-bottom:1px dashed rgba(255,255,255,.05);padding:3px 0}
  .files a{color:var(--acc);text-decoration:none;word-break:break-all}
  .files a:hover{text-decoration:underline}
  .files span{color:var(--dim);white-space:nowrap;font-size:12px}
  .files.dim a{color:#9aa3b6}
  details summary{cursor:pointer;color:var(--dim);font-size:12.5px}
  footer{padding:26px 20px 60px;color:var(--dim);font-size:12.5px;border-top:1px solid var(--line);margin-top:20px}
  footer a{color:#9aa3b6}
  .empty{grid-column:1/-1;color:var(--dim);text-align:center;padding:40px}
</style>
</head>
<body>
<header>
  <h1>苗壮的 3D 打印模型库</h1>
  <p class="lead">这里放我打过的 3D 打印件：<b>原创设计</b>、<b>改造件</b>（第三方或 AI 网格 + 我们自己的分件/支撑/朝向处理）、以及参数记录。
  <b>不是全部原创</b>——每个模型都标了来源类别，明细见 <a href="README.md" style="color:#9aa3b6">README</a>。点文件名直接下载，3MF 里已带打印设置。</p>
</header>
<div class="bar">
  <input id="q" type="search" placeholder="搜名称 / 编号 / 文件名…" autocomplete="off">
  <div class="filters">
    <button data-f="all" aria-pressed="true">全部</button>
    <button data-f="original" aria-pressed="false">原创</button>
    <button data-f="derived" aria-pressed="false">改造</button>
  </div>
</div>
<main id="grid">
${models.map(card).join("\n")}
<div class="empty" id="empty" hidden>没有匹配的模型</div>
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
  }
  q.addEventListener('input', apply);
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

fs.writeFileSync(path.join(ROOT, "index.html"), html);
console.log(`index.html 已生成：${models.length} 个模型，共 ${human(models.reduce((s, m) => s + m.bytes, 0))}`);
