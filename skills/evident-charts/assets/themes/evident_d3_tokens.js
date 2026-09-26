// evident-charts tokens for D3 (ES module). type and strokes mirror ../presets.json (% of canvas width); margins are fractions of width.
export const EV = {
  accent: "#D55E00", accentText: "#C15500", alt: "#0072B2", gray: "#BDBDBD",
  ink: "#333333", dark: "#595959", muted: "#767676", grid: "#E6E6E6", spine: "#8C8C8C",
  okabeIto: ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"],
  presets: {
    blog: { width: 800, height: 600, scale: 2, type: { title: 3.2, subtitle: 2.2, label: 1.9, annotation: 2.0, source: 1.6 },
      strokes: { line: 0.28, accent_line: 0.55, marker: 1.4, grid: 0.14 }, margins: { left: 0.05, right: 0.04, top: 0.05, bottom: 0.03 } },
    social: { width: 1080, height: 1080, scale: 2, type: { title: 4.6, subtitle: 3.0, label: 2.8, annotation: 2.9, source: 2.2 },
      strokes: { line: 0.28, accent_line: 0.58, marker: 1.6, grid: 0.13 }, margins: { left: 0.07, right: 0.05, top: 0.05, bottom: 0.03 } },
    social_portrait: { width: 1080, height: 1350, scale: 2, type: { title: 4.6, subtitle: 3.0, label: 2.8, annotation: 2.9, source: 2.2 },
      strokes: { line: 0.28, accent_line: 0.58, marker: 1.6, grid: 0.13 }, margins: { left: 0.07, right: 0.05, top: 0.05, bottom: 0.03 } },
    slide: { width: 1920, height: 1080, scale: 2, type: { title: 3.75, subtitle: 2.5, label: 2.1, annotation: 2.3, source: 1.6 },
      strokes: { line: 0.22, accent_line: 0.45, marker: 1.2, grid: 0.1 }, margins: { left: 0.05, right: 0.04, top: 0.045, bottom: 0.03 } },
    report: { width: 600, height: 450, scale: 4, type: { title: 2.9, subtitle: 2.35, label: 2.0, annotation: 2.1, source: 2.0 },
      strokes: { line: 0.3, accent_line: 0.6, marker: 1.6, grid: 0.15 }, margins: { left: 0.02, right: 0.02, top: 0.02, bottom: 0.015 } },
    mobile: { width: 360, height: 450, scale: 3, type: { title: 5.6, subtitle: 3.9, label: 3.6, annotation: 3.6, source: 3.4 },
      strokes: { line: 0.4, accent_line: 0.8, marker: 2.2, grid: 0.2 }, margins: { left: 0.05, right: 0.04, top: 0.05, bottom: 0.035 } },
  },
};

// Size in SVG units (viewBox width = preset width) of a type role (font size) or stroke role (line, accent_line, marker, grid).
export const evSize = (role, dest = "blog") => {
  const p = EV.presets[dest];
  return Math.round((p.type[role] ?? p.strokes[role]) * p.width) / 100;
};

// Apply a preset's sizes to an <svg class="ev-chart"> (CSS custom properties from evident_d3.css).
export function evApply(svg, dest = "blog") {
  const p = EV.presets[dest];
  svg.attr("viewBox", `0 0 ${p.width} ${p.height}`);
  for (const role of Object.keys(p.type)) svg.style(`--ev-${role}`, `${evSize(role, dest)}px`);
  svg.style("--ev-line", `${evSize("line", dest)}px`).style("--ev-accent-line", `${evSize("accent_line", dest)}px`)
     .style("--ev-hair", `${evSize("grid", dest)}px`);
  return svg;
}

// Highlight + gray color accessor: evColor(["US"])(d.name).
export const evColor = (highlight = [], accents = [EV.accent, EV.alt]) => (name) => {
  const i = highlight.indexOf(name);
  return i >= 0 && i < accents.length ? accents[i] : EV.gray;
};

// Diverging color with a symmetric domain so 0 sits at the neutral midpoint.
// d3.interpolateRdBu runs red (0) to blue (1): domain [-m, 0, m] maps negatives red, positives blue.
export const evDiverging = (d3, values) => {
  const m = d3.max(values, (v) => Math.abs(v));
  return d3.scaleDiverging(d3.interpolateRdBu).domain([-m, 0, m]);
};
