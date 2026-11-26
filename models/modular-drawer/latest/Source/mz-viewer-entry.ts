import { createModelViewer, type ModelViewer } from "@mizy/mz-3d-viewer";
import { createNavCube } from "@mz/report-nav";
import { bindCanvasClick } from "@mz/report-click";
import { createContextMenu, type ContextMenuActions } from "@mz/report-menu";
import type { DisplayStyle } from "@mizy/mz-3d-viewer";
import * as THREE from "three/webgpu";

type Packet = { v: string; i: string; n: number; kind: string; rgb?: string };
type Part = { name: string; quantum: number; extent: number[]; nSolids: number; meshes: Packet[]; href?: string };
type Cad = { parts: Record<string, Part>; panels: { id: string; mesh: string; title: string }[]; trays?: { id: string; mesh: string; title: string }[]; handles?: { id: string; mesh: string; title: string }[] };
const pigments: Readonly<Record<string, number>> = {
  side: 0x29918f, front: 0x4f7aad, rear: 0x2e4a6e, drawer: 0x8ca697, hardware: 0xd67533, grip: 0xf6e9cd
};
type View = "iso" | "front" | "back" | "right" | "top";
const fmt = new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 4 });
const names: Record<string,string> = { side:"侧板",front:"前梁",rear:"后板",drawer:"抽屉",hardware:"锁件",grip:"拉手" };
const byId = <T extends HTMLElement>(id: string): T => document.getElementById(id) as T;

function decode(base64: string): ArrayBuffer {
  const raw = atob(base64);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; ++i) bytes[i] = raw.charCodeAt(i);
  return bytes.buffer;
}

// The report packets are display meshes from the signed STEP. This adapter
// only dequantizes the existing vertices and maps CAD Z-up to the viewer Y-up.
function toViewerModel(part: Part): THREE.Group {
  const root = new THREE.Group();
  for (const source of part.meshes) {
    const integers = new Int16Array(decode(source.v));
    const xyz = new Float32Array(integers.length);
    for (let i = 0; i < integers.length; i += 3) {
      xyz[i] = integers[i] * part.quantum;
      xyz[i + 1] = integers[i + 2] * part.quantum;
      xyz[i + 2] = -integers[i + 1] * part.quantum;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(xyz, 3));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(decode(source.i)), 1));
    if (source.rgb) {
      const srgb = new Uint8Array(decode(source.rgb));
      if (srgb.length !== xyz.length) throw new Error("预览顶点和颜色数不一致");
      const color = new Float32Array(srgb.length);
      const palette = new THREE.Color();
      for (let i = 0; i < srgb.length; i += 3) {
        palette.setRGB(srgb[i]/255,srgb[i+1]/255,srgb[i+2]/255,THREE.SRGBColorSpace);
        color[i]=palette.r; color[i+1]=palette.g; color[i+2]=palette.b;
      }
      g.setAttribute("color", new THREE.BufferAttribute(color, 3));
    }
    g.computeVertexNormals();
    const mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      color: source.rgb ? 0xffffff : (pigments[source.kind] ?? pigments.hardware),
      vertexColors: Boolean(source.rgb),
      roughness: 0.79, metalness: 0, flatShading: true, side: THREE.DoubleSide
    }));
    mesh.name = (names[source.kind] ?? "部件") + " " + (root.children.length + 1);
    root.add(mesh);
  }
  return root;
}

async function setup(): Promise<void> {
  const status = byId("status"), canvas = byId<HTMLCanvasElement>("scene");
  const menu = byId<HTMLSelectElement>("part");
  const controls = document.querySelectorAll<HTMLButtonElement>("[data-camera],#reset,#zoom-in,#zoom-out");
  menu.disabled = true;
  controls.forEach(e => { e.disabled = true; });
  const cad = JSON.parse(byId("cad-data").textContent ?? "") as Cad;
  menu.add(new Option("后板背插键 · 关合总成", "assembly"));
  const models = [...cad.panels, ...(cad.trays ?? []), ...(cad.handles ?? [])];
  for (const p of models) menu.add(new Option(p.title + "（单件）", p.id));
  const viewer: ModelViewer = await createModelViewer(canvas, {
    edges: true, background: 0xe8f0ee
  });
  const { stage } = viewer;
  stage.setGridVisible(false);
  stage.setPickMode("part");
  stage.setProjection("orthographic");
  createNavCube(stage, byId("navCube"));
  canvas.dataset.mzViewer = "mz-3d-viewer";
  canvas.dataset.renderer = viewer.backend;
  const interactions = new AbortController();
  const signal = interactions.signal;
  const pickState = byId("pick-state");
  let hoverName = "", clickGeneration = 0, hoverGeneration = 0;
  let pending: { x: number; y: number } | null = null;
  let pickingHover = false;
  function showPickState(): void {
    const model = stage.active;
    const selected = model?.selectedPart;
    const name = selected == null ? null : model!.parts[selected]?.mesh.name;
    canvas.dataset.selectedPart = selected == null ? "" : String(selected);
    canvas.dataset.hoveredPart = hoverName;
    pickState.textContent = name ? "已选中：" + name : hoverName ? "悬停：" + hoverName : "悬停高亮 · 单击选中 · 右键操作";
  }
  function clearHover(): void {
    ++hoverGeneration;
    pending = null;
    hoverName = "";
    stage.setHoveredSurface(null);
    showPickState();
  }
  async function drainHover(): Promise<void> {
    if (pickingHover) return;
    pickingHover = true;
    try {
      while (pending && !signal.aborted) {
        const point = pending, generation = hoverGeneration, id = stage.active?.id;
        pending = null;
        const hit = id && document.elementFromPoint(point.x, point.y) === canvas
          ? await stage.pick(point.x, point.y, { inspect: true }).catch(() => null) : null;
        if (generation !== hoverGeneration || pending || signal.aborted || stage.active?.id !== id) continue;
        stage.setHoveredSurface(hit);
        hoverName = hit?.mesh.name ?? "";
        showPickState();
      }
    } finally { pickingHover = false; }
  }
  canvas.addEventListener("pointermove", ev => {
    if (ev.buttons || ev.pointerType !== "mouse" || !stage.active) { clearHover(); return; }
    pending = { x: ev.clientX, y: ev.clientY };
    void drainHover();
  }, { signal });
  for (const e of ["pointerleave","pointerdown","pointercancel","wheel"]) canvas.addEventListener(e, clearHover, { passive: true, signal });
  stage.controls.addEventListener("change", clearHover);
  window.addEventListener("blur", clearHover, { signal });
  bindCanvasClick(canvas, async ev => {
    const generation = ++clickGeneration, id = stage.active?.id;
    if (!id) return;
    const hit = await stage.pick(ev.clientX, ev.clientY, { inspect: true }).catch(() => null);
    if (generation !== clickGeneration || signal.aborted || stage.active?.id !== id) return;
    stage.selectHit(hit);
    showPickState();
  }, signal);
  canvas.addEventListener("dblclick", () => {
    const i = stage.active?.selectedPart;
    if (i != null) stage.fitToPart(i);
  }, { signal });
  let frames = 0;
  stage.onRender = () => {
    canvas.dataset.frames = String(++frames);
    canvas.dataset.visibleParts = String(stage.active?.root.visible ? stage.active.parts.filter(p => p.mesh.visible).length : 0);
    showPickState();
    canvas.dataset.displayMode = stage.style;
    canvas.dataset.edgeMeshes = String(stage.active?.edges?.children.length ?? 0);
    canvas.dataset.projection = stage.projectionKind;
    canvas.dataset.camera = [...stage.camera.position.toArray(), stage.camera.zoom].map(x => x.toFixed(6)).join(",");
  };
  function camera(view: View): void {
    stage.setStandardView(view, false);
    canvas.dataset.view = view;
  }
  function projection(kind: "orthographic" | "perspective"): void {
    stage.setProjection(kind);
    byId("mz-ortho").setAttribute("aria-pressed", String(kind === "orthographic"));
    byId("mz-perspective").setAttribute("aria-pressed", String(kind === "perspective"));
  }
  byId("mz-ortho").onclick = () => projection("orthographic");
  byId("mz-perspective").onclick = () => projection("perspective");
  function changeStyle(style: DisplayStyle): void {
    void stage.setDisplayStyle(style).catch(e => {
      if (e instanceof DOMException && e.name === "AbortError") return;
      canvas.dataset.styleError = e instanceof Error ? e.message : "显示模式切换失败";
      status.textContent = "显示模式切换失败，已回到实体模式。";
      void stage.setDisplayStyle("solid");
    });
  }
  // The published native context menu resolves targets with the same WebGPU stage.
  const actions: ContextMenuActions = {
    fitAll: () => stage.fitToScene(),
    fitPart: (i) => stage.fitToPart(i),
    hidePart: (i) => stage.setPartVisible(i, false),
    isolatePart: (i) => stage.isolatePart(i),
    hideModel: (id) => stage.setVisible(id, false),
    showAll: () => { stage.showAllParts(); stage.selectPart(null); },
    resetView: () => camera("iso"),
    setStyle: changeStyle
  };
  const disposeMenu = createContextMenu(stage, canvas, actions);
  function loadSelected(): void {
    const panel = models.find(p => p.id === menu.value);
    const part = cad.parts[panel?.mesh ?? "assembly"];
    if (part.meshes.length !== part.nSolids) throw new Error("预览实体数量与 STEP 清单不一致");
    ++clickGeneration;
    clearHover();
    viewer.clear();
    const root = toViewerModel(part);
    stage.addModel({ root, sourceUnit: { label: "毫米", mmPerUnit: 1 }, format: "step", warnings: [] }, part.name);
    stage.setActiveMaterial("original");
    if (stage.style === "edges") changeStyle("edges");
    canvas.dataset.draws = String(root.children.length);
    status.textContent = (panel?.title ?? "后板背插键 · 关合总成") + " · " + part.nSolids + " 个实体 · "
      + part.extent.map(x => fmt.format(x)).join(" × ") + " mm · mz-3d-viewer / " + viewer.backend.toUpperCase();
    const ref = byId("view-file");
    const link = document.createElement("a");
    link.href = part.href ?? ("STEP/" + encodeURIComponent(part.name));
    link.textContent = part.name;
    ref.replaceChildren(link);
    camera("iso");
  }
  function zoom(factor: number): void {
    const cam = stage.camera;
    cam.zoom = Math.max(0.00001, Math.min(40, cam.zoom * factor));
    cam.updateProjectionMatrix();
    stage.controls.syncCamera();
    stage.controls.notifyChange();
  }

  for (const button of document.querySelectorAll<HTMLButtonElement>("[data-camera]")) {
    button.onclick = () => camera((button.dataset.camera === "side" ? "right" : button.dataset.camera) as View);
  }
  byId("reset").onclick = () => camera("iso");
  byId("zoom-in").onclick = () => zoom(1.2);
  byId("zoom-out").onclick = () => zoom(1 / 1.2);
  menu.onchange = loadSelected;
  canvas.addEventListener("pointerdown", () => canvas.focus({ preventScroll: true }));
  canvas.addEventListener("keydown", e => {
    if (e.key === "Escape") { ++clickGeneration; stage.selectPart(null); clearHover(); }
    else if (e.key === "Home") camera("iso");
    else if (e.key === "+" || e.key === "=") zoom(1.15);
    else if (e.key === "-") zoom(1 / 1.15);
    else if (e.key === "ArrowLeft") stage.rotateView(-.12, 0);
    else if (e.key === "ArrowRight") stage.rotateView(.12, 0);
    else if (e.key === "ArrowUp") stage.rotateView(0, -.12);
    else if (e.key === "ArrowDown") stage.rotateView(0, .12);
    else return;
    e.preventDefault();
  });
  window.addEventListener("pagehide", e => { if (!e.persisted) { interactions.abort(); disposeMenu(); viewer.dispose(); } });
  loadSelected();
  menu.disabled = false;
  controls.forEach(e => { e.disabled = false; });
}

void setup().catch((e: unknown) => {
  const status = byId("status");
  status.dataset.error = "true";
  status.textContent = "3D 需要支持 WebGPU 的浏览器和图形加速；三视图与 STEP 仍然可用。"
    + (e instanceof Error ? " " + e.message : "");
});
