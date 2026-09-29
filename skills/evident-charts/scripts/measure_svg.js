// Measurer for check_svg.py. Runs in headless Chrome on a page check_svg.py builds, which first defines
// EVIDENT_SVG (the chart's SVG source). Parses the SVG as XML, lays it out, and measures every visible text
// and shape in canvas px (origin at the SVG's top-left corner). Then it replaces the page body with one
// <pre> holding JSON, which check_svg.py reads from Chrome's --dump-dom output.
(function () {
  "use strict";
  const PAD = 4 / 3;          // 1 pt in px: text boxes shrink by this before sampling (check_chart TEXT_LINE_PAD_PT)
  const STEP = 1.5;           // px between samples along a stroke
  const MAX_SAMPLES = 1500;   // per stroke
  const SHAPES = "rect, path, circle, ellipse, line, polyline, polygon";

  // Which shapes are data marks, from class names on the element or any ancestor (chrome is tested first):
  //   Plotly:  data g.trace (bars, scatter points, path.js-line, path.js-fill); chrome rect.bg, grid and zero lines,
  //            axis ticks, g.legend, g.infolayer (titles, annotations).
  //   Vega:    data g.role-mark; chrome role-axis*, role-legend*, role-title, path.background / foreground.
  //   D3:      house classes ev-series ev-accent ev-context ev-alt ev-stem ev-segment are data; d3-axis output
  //            (g.tick, path.domain) and ev-axis / ev-grid / ev-annotation are chrome.
  //   Anything else (svglite and other R devices, hand-written SVG) is "unknown": check_svg.py decides by color
  //   and size.
  const CHROME_RE = /legend|axis|grid|tick|\bdomain\b|zeroline|title|annotation|\bbg\b|background|foreground|draglayer|hoverlayer|infolayer/;
  const DATA_RE = /\btrace\b|role-mark|ev-(series|accent|context|alt|stem|segment)\b/;
  // Mark kind: bar (rects and bar classes), point (circles, symbols), else area (filled) or line.
  const BAR_RE = /\bbars?\b|mark-rect|ev-bar/;
  const POINT_RE = /\bpoints?\b|mark-symbol|\bdots?\b/;
  // Text kind, used to skip ticks and legends where check_chart does.
  const TEXT_KINDS = [["tick", /tick|role-axis-label/], ["legend", /legend/], ["title", /title/]];

  const out = { error: null };
  try {
    const doc = new DOMParser().parseFromString(EVIDENT_SVG, "image/svg+xml");
    const bad = doc.getElementsByTagName("parsererror")[0];
    if (bad) throw new Error("the file does not parse as SVG/XML: " + bad.textContent.trim().slice(0, 160));
    if (doc.documentElement.localName !== "svg") throw new Error("the root element is not <svg>");
    const svg = document.importNode(doc.documentElement, true);
    const vb = svg.viewBox && svg.viewBox.baseVal;
    for (const [attr, v] of [["width", vb && vb.width], ["height", vb && vb.height]]) {
      const a = svg.getAttribute(attr);
      if ((!a || a.trim().endsWith("%")) && v) svg.setAttribute(attr, v);  // responsive D3: size from the viewBox
    }
    document.body.appendChild(svg);
    measure(svg);
  } catch (e) {
    out.error = String((e && e.message) || e);
  }
  document.body.textContent = "";  // drop the chart and scripts: only the result is dumped
  const pre = document.createElement("pre");
  pre.id = "evident-measure";
  pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);

  function measure(svg) {
    const R = svg.getBoundingClientRect();
    out.width = R.width;
    out.height = R.height;
    const styleCache = new Map(), clsCache = new Map(), opCache = new Map();
    const cs = (e) => { let s = styleCache.get(e); if (!s) { s = getComputedStyle(e); styleCache.set(e, s); } return s; };
    const up = (e) => (e.parentNode && e.parentNode.nodeType === 1 ? e.parentNode : null);
    function classes(e) {  // own and ancestor class names, joined
      if (!e) return "";
      if (!clsCache.has(e)) clsCache.set(e, ((e.getAttribute("class") || "") + " " + classes(up(e))).trim());
      return clsCache.get(e);
    }
    function opacity(e) {  // product of ancestor opacities
      if (!e) return 1;
      if (!opCache.has(e)) opCache.set(e, +cs(e).opacity * opacity(up(e)));
      return opCache.get(e);
    }
    function visible(e) {
      if (cs(e).visibility !== "visible" || opacity(e) === 0) return false;
      for (let n = e; n; n = up(n)) if (cs(n).display === "none") return false;
      return true;
    }
    const inDefs = (e) => !!e.closest("defs, clipPath, mask, marker, pattern, symbol, linearGradient, radialGradient");
    const rel = (x, y) => [x - R.left, y - R.top];
    const boxOf = (r) => [r.left - R.left, r.top - R.top, r.right - R.left, r.bottom - R.top];
    const meet = (a, b) => (!a ? b : !b ? a : [Math.max(a[0], b[0]), Math.max(a[1], b[1]), Math.min(a[2], b[2]), Math.min(a[3], b[3])]);
    const has = (b, x, y) => x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3];
    const paint = (v) => v && v !== "none" && !/^rgba\(.*,\s*0\)$/.test(v);
    const scaleOf = (m) => Math.hypot(m.a, m.b);

    function clipBox(e) {  // intersection of every ancestor clip-path that is a rect, in canvas px
      let box = null;
      for (let n = e; n && n !== svg.parentNode; n = up(n)) {
        const m = (cs(n).clipPath || "").match(/url\(["']?#([^"')]+)["']?\)/);
        const cp = m && document.getElementById(m[1]);
        if (!cp || cp.getAttribute("clipPathUnits") === "objectBoundingBox") continue;
        const r = cp.querySelector("rect");
        if (!r) continue;
        let ctm = n.getScreenCTM();
        if (r.transform && r.transform.baseVal.numberOfItems) ctm = ctm.multiply(r.transform.baseVal.consolidate().matrix);
        const x = r.x.baseVal.value, y = r.y.baseVal.value, w = r.width.baseVal.value, h = r.height.baseVal.value;
        const p = [[x, y], [x + w, y], [x, y + h], [x + w, y + h]].map(([a, b]) => new DOMPoint(a, b).matrixTransform(ctm));
        const xs = p.map((q) => q.x), ys = p.map((q) => q.y);
        box = meet(box, [...rel(Math.min(...xs), Math.min(...ys)), ...rel(Math.max(...xs), Math.max(...ys))]);
      }
      return box;
    }

    const traceIds = new Map();
    function traceOf(e) {  // Plotly: the g.trace holding a mark (one trace = one series)
      const g = e.closest("g.trace");
      if (!g) return null;
      if (!traceIds.has(g)) traceIds.set(g, traceIds.size);
      return traceIds.get(g);
    }

    const shapes = [], texts = [], els = [];
    const all = [...svg.querySelectorAll("text, " + SHAPES)].filter((e) => !inDefs(e));
    const orderOf = new Map(all.map((e, k) => [e, k]));  // paint order
    for (const e of all) {
      if (!visible(e)) continue;
      if (e.localName === "text") { const t = textRecord(e); if (t) texts.push(t); continue; }
      const s = cs(e), cls = classes(e), clip = clipBox(e);
      const vbox = meet(boxOf(e.getBoundingClientRect()), clip);
      if (vbox[2] < vbox[0] || vbox[3] < vbox[1]) continue;  // clipped away
      const role = CHROME_RE.test(cls) ? "chrome" : DATA_RE.test(cls) ? "data" : "unknown";
      const fill = paint(s.fill) && +s.fillOpacity > 0 ? s.fill : null;
      const ctm = e.getScreenCTM();
      const sw = parseFloat(s.strokeWidth) * scaleOf(ctm);
      const stroke = paint(s.stroke) && +s.strokeOpacity > 0 && sw > 0 ? s.stroke : null;
      const tag = e.localName;
      const kind = BAR_RE.test(cls) || tag === "rect" ? "bar"
        : tag === "circle" || tag === "ellipse" || POINT_RE.test(cls) ? "point" : fill ? "area" : "line";
      const sh = { i: shapes.length, order: orderOf.get(e), tag, kind, role, cls: cls.slice(0, 120), fill, stroke,
        fill_opacity: +s.fillOpacity, stroke_opacity: +s.strokeOpacity, opacity: opacity(e), stroke_width: sw,
        dashed: !!s.strokeDasharray && s.strokeDasharray !== "none", box: vbox, clip, trace: traceOf(e),
        verts: vertexCount(e), pieces: null, under: [] };
      shapes.push(sh);
      els.push(e);
      if (stroke && !fill && role !== "chrome" && kind !== "point") sh.pieces = strokeSamples(e, ctm, clip);
    }

    function vertexCount(e) {  // how many points a stroke bends through; outlines of boxes and dots count 0
      if (e.localName === "line") return 2;
      if (e.localName === "polyline" || e.localName === "polygon") return e.points.numberOfItems;
      if (e.localName === "path") return Math.ceil(((e.getAttribute("d") || "").match(/-?[\d.]+(e[-+]?\d+)?/gi) || []).length / 2);
      return 0;
    }

    function strokeSamples(e, ctm, clip) {  // polyline pieces along the stroke, split at jumps and clip edges
      let len = 0;
      try { len = e.getTotalLength(); } catch (err) { return null; }
      if (!(len > 0)) return null;
      const n = Math.min(MAX_SAMPLES, Math.max(2, Math.ceil(len / STEP)));
      const step = len / (n - 1), pieces = [];
      let cur = [], last = null;
      for (let k = 0; k < n; k++) {
        const p = e.getPointAtLength(k * step).matrixTransform(ctm);
        const [x, y] = rel(p.x, p.y);
        const jump = last && Math.hypot(x - last[0], y - last[1]) > 3 * step * scaleOf(ctm) + 1;
        if (jump || (clip && !has(clip, x, y))) { if (cur.length > 2) pieces.push(cur); cur = []; }
        if (!clip || has(clip, x, y)) cur.push(Math.round(x * 10) / 10, Math.round(y * 10) / 10);
        last = [x, y];
      }
      if (cur.length > 2) pieces.push(cur);
      return pieces;
    }

    function fillsAt(x, y, before) {  // indices of filled shapes painted before `before` that cover canvas point x, y
      const hits = [];
      for (let k = 0; k < shapes.length && shapes[k].order < before; k++) {
        const sh = shapes[k];
        if (!sh.fill || !has(sh.box, x, y)) continue;
        const el = els[k];
        const p = new DOMPoint(x + R.left, y + R.top).matrixTransform(el.getScreenCTM().inverse());
        if (el.isPointInFill && el.isPointInFill(p)) hits.push(k);
      }
      return hits;
    }

    function textRecord(e) {
      const text = e.textContent.replace(/\s+/g, " ").trim();
      if (!text) return null;
      const s = cs(e), ctm = e.getScreenCTM(), scale = scaleOf(ctm);
      // Line boxes in the text's own coordinates: character cells grouped by vertical overlap.
      const lines = [];
      const n = e.getNumberOfChars();
      for (let k = 0; k < n; k++) {
        let b;
        try { b = e.getExtentOfChar(k); } catch (err) { continue; }
        if (!(b.width > 0 && b.height > 0)) continue;
        const cell = [b.x, b.y, b.x + b.width, b.y + b.height];
        const ln = lines.find((l) => Math.min(l[3], cell[3]) - Math.max(l[1], cell[1]) > 0.5 * Math.min(l[3] - l[1], cell[3] - cell[1]));
        if (ln) { ln[0] = Math.min(ln[0], cell[0]); ln[1] = Math.min(ln[1], cell[1]); ln[2] = Math.max(ln[2], cell[2]); ln[3] = Math.max(ln[3], cell[3]); }
        else lines.push(cell);
      }
      if (!lines.length) return null;
      const toCanvas = (x, y) => { const p = new DOMPoint(x, y).matrixTransform(ctm); return rel(p.x, p.y); };
      // Corners in order: top-left, top-right, bottom-right, bottom-left of each line, in canvas px.
      const quads = lines.map(([x0, y0, x1, y1]) => [toCanvas(x0, y0), toCanvas(x1, y0), toCanvas(x1, y1), toCanvas(x0, y1)]);
      // Backdrop samples: an 8 x 3 grid over each line box (inset 1 pt at the sides), with the fills beneath each.
      const order = orderOf.get(e), under = [];
      const inset = PAD / Math.max(scale, 1e-6);
      for (const [x0, y0, x1, y1] of lines) {
        for (let iv = 0; iv < 3; iv++) for (let iu = 0; iu < 8; iu++) {
          const u = 0.05 + 0.9 * iu / 7, v = 0.2 + 0.6 * iv / 2;
          const [x, y] = toCanvas(x0 + inset + (x1 - x0 - 2 * inset) * u, y0 + (y1 - y0) * v);
          under.push(fillsAt(x, y, order));
        }
      }
      const runs = [e, ...e.querySelectorAll("tspan")].filter((r) =>
        [...r.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim()));
      const sizes = (runs.length ? runs : [e]).map((r) => parseFloat(cs(r).fontSize) * scale);
      const cls = classes(e);
      const halo = paint(s.stroke) && parseFloat(s.strokeWidth) * scale >= 1 && +s.strokeOpacity > 0;
      return { order, text, cls: cls.slice(0, 120), kind: (TEXT_KINDS.find(([, re]) => re.test(cls)) || ["text"])[0],
        font_px: Math.min(...sizes), weight: parseInt(s.fontWeight, 10) || 400,
        fill: s.fill, fill_opacity: +s.fillOpacity, opacity: opacity(e), halo: halo ? s.stroke : null,
        angle: Math.atan2(ctm.b, ctm.a) * 180 / Math.PI, quads, clip: clipBox(e), under };
    }

    // A representative point on each mark and the fills beneath it (its backdrop), for mark contrast.
    shapes.forEach((sh, k) => {
      let pt = null;
      if (sh.pieces && sh.pieces.length) {
        const p = sh.pieces[Math.floor(sh.pieces.length / 2)];
        const j = 2 * Math.floor(p.length / 4);
        pt = [p[j], p[j + 1]];
      } else if (sh.kind === "point") {
        pt = [(sh.box[0] + sh.box[2]) / 2, (sh.box[1] + sh.box[3]) / 2];
      } else if (sh.fill) {
        const [x0, y0, x1, y1] = sh.box;
        for (const [u, v] of [[0.5, 0.5], [0.5, 0.9], [0.25, 0.9], [0.75, 0.9], [0.5, 0.75], [0.1, 0.95], [0.9, 0.95]]) {
          const x = x0 + (x1 - x0) * u, y = y0 + (y1 - y0) * v;
          const p = new DOMPoint(x + R.left, y + R.top).matrixTransform(els[k].getScreenCTM().inverse());
          if (els[k].isPointInFill(p)) { pt = [x, y]; break; }
        }
      }
      if (pt) sh.under = fillsAt(pt[0], pt[1], sh.order);
    });

    const legends = [...svg.querySelectorAll("g.legend, g.role-legend, g.ev-legend")]
      .filter((g) => !g.parentNode.closest("g.legend, g.role-legend, g.ev-legend") && visible(g))
      .map((g) => boxOf(g.getBoundingClientRect())).filter((b) => b[2] > b[0] && b[3] > b[1]);
    Object.assign(out, { texts, shapes, legends });
  }
})();
