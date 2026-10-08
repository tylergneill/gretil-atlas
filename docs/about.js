// about.html's scripted behaviour: the theme toggle, the figures in the prose,
// the Data Quality lists, and the growth chart.
//
// The figures come from data/tree.json and data/changelog.json, never from the
// markup -- a number typed into the page is a number that goes stale. Each
// <span data-stat="key"> is filled from deriveStats(); an absent figure renders
// as an em dash rather than a zero. The sibling Atlases have their audit
// pipeline rewrite the digits in place (`audit --update-about`); this Atlas has
// no audit stage yet, so the page derives them itself from the two published
// files, which is also all the Data Quality lists are allowed to read.
//
// The theme icons and handler are duplicated from app.js rather than shared,
// because about.html deliberately doesn't load app.js (which expects a sidebar
// and a tree). Both pages read/write the same localStorage "theme" key.

const SUN_ICON = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 3v2"/><path d="M12 19v2"/><path d="M5 5l1.4 1.4"/><path d="M17.6 17.6L19 19"/><path d="M3 12h2"/><path d="M19 12h2"/><path d="M5 19l1.4-1.4"/><path d="M17.6 6.4L19 5"/></svg>`;
const MOON_ICON = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z"/></svg>`;

function updateThemeToggleLabel() {
  const btn = document.getElementById("themeToggle");
  if (!btn) return;
  const theme = document.documentElement.getAttribute("data-theme") || "dark";
  const icon = theme === "dark" ? SUN_ICON : MOON_ICON;
  const label = theme === "dark" ? "Light" : "Dark";
  btn.innerHTML = `${icon}<span class="toggle-label">${label}</span>`;
}

const themeToggle = document.getElementById("themeToggle");
if (themeToggle) {
  updateThemeToggleLabel();
  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateThemeToggleLabel();
  });
}

const TREE_URL = "./data/tree.json";
const CHANGELOG_URL = "./data/changelog.json";

// Where a work's files are served from -- the same root app.js links to.
const MIRROR_ROOT = "https://tylergneill.github.io/gretil-mirror/gretil";

// The one domain the Atlas invents: TEI files whose header names no legacy
// file, and which therefore have no directory to take a category from.
const NO_LEGACY_DOMAIN = "TEI without a legacy source";

// ---------------------------------------------------------------------------
// Figures in the prose
// ---------------------------------------------------------------------------

const nf = new Intl.NumberFormat("en-US");

function fillStats(stats) {
  for (const el of document.querySelectorAll("[data-stat]")) {
    const unit = el.dataset.unit;
    let v = stats[el.dataset.stat];
    if (typeof v === "number" && unit === "mb") v = (v / 1e6).toFixed(0);
    else if (typeof v === "number" && unit === "kb") v = (v / 1e3).toFixed(0);
    else if (typeof v === "number") v = nf.format(v);
    el.textContent = v == null || v === "" ? "—" : String(v);
  }
}

const bytesOf = (w) => (w.sizes || {}).transliterated_bytes || 0;
const pct = (n, d) => (d ? (n / d * 100).toFixed(0) : null);
const hasLegacyFile = (w) => (w.files || []).some((f) => f.startsWith("1_sanskr/"));

// "Kṣemendra" and "Ksemendra" fold to the same key: decompose, drop the
// combining marks, lowercase. Used only to *find* names the two layers spell
// differently; nothing is merged, here or in the tree.
function foldName(s) {
  return s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().trim();
}

function authorVariants(works) {
  const groups = new Map();
  for (const w of works) {
    if (!w.author) continue;
    const key = foldName(w.author);
    if (!groups.has(key)) groups.set(key, new Map());
    const spellings = groups.get(key);
    spellings.set(w.author, (spellings.get(w.author) || 0) + 1);
  }
  return [...groups.values()].filter((s) => s.size > 1);
}

function deriveStats(tree, log) {
  const works = tree.works || [];
  const stats = { ...(tree.all_stats || {}) };
  const tei = works.filter((w) => w.tei);
  const legacy = works.filter((w) => !w.tei);
  const sum = (ws) => ws.reduce((s, w) => s + bytesOf(w), 0);

  stats.tei_with_legacy = tei.filter(hasLegacyFile).length;
  stats.tei_without_legacy = tei.length - stats.tei_with_legacy;
  stats.tei_bytes = sum(tei);
  stats.legacy_only_bytes = sum(legacy);
  stats.legacy_only_files = legacy.reduce((s, w) => s + (w.files || []).length, 0);
  stats.legacy_multi_rendering = legacy.filter((w) => (w.renderings || []).length > 1).length;

  const gretilDomains = new Set(works.map((w) => w.domain).filter((d) => d !== NO_LEGACY_DOMAIN));
  stats.categories = gretilDomains.size;
  stats.subcategories = new Set(works.filter((w) => w.sub_domain)
    .map((w) => `${w.domain}\u0000${w.sub_domain}`)).size;

  const anonymous = works.filter((w) => !w.author).length;
  stats.no_author = anonymous;
  stats.no_author_pct = pct(anonymous, works.length);
  stats.authors_distinct = new Set(works.map((w) => w.author).filter(Boolean)).size;
  const variants = authorVariants(works);
  stats.author_variant_groups = variants.length;
  stats.author_variant_works = variants.reduce(
    (s, sp) => s + [...sp.values()].reduce((a, b) => a + b, 0), 0);

  const sizes = works.map(bytesOf).sort((a, b) => a - b);
  if (sizes.length) {
    const mid = sizes.length >> 1;
    stats.median_bytes = sizes.length % 2 ? sizes[mid] : (sizes[mid - 1] + sizes[mid]) / 2;
    const total = sizes.reduce((a, b) => a + b, 0);
    let run = 0, n = 0;
    for (const b of [...sizes].reverse()) { run += b; n += 1; if (run >= total / 2) break; }
    stats.half_bytes_works = n;
  }

  const years = (y) => tei.filter((w) => (w.tei_date || "").startsWith(y)).length;
  stats.tei_date_2019 = years("2019");
  stats.tei_date_2020 = years("2020");

  const dated = works.filter((w) => w.added);
  stats.dated_works = dated.length;
  stats.dated_tei = dated.filter((w) => w.tei).length;
  stats.dated_legacy = dated.length - stats.dated_tei;
  stats.undated_tei = tei.length - stats.dated_tei;
  stats.undated_legacy = legacy.length - stats.dated_legacy;
  stats.dated_tei_pct = pct(stats.dated_tei, tei.length);
  stats.dated_bytes = sum(dated);
  stats.dated_bytes_pct = pct(stats.dated_bytes, sum(works));

  if (log) {
    const periods = log.periods || [];
    stats.changelog_first = periods[0]?.date?.slice(0, 7);
    stats.changelog_last = periods[periods.length - 1]?.date?.slice(0, 7);
    stats.undated_works = log.undated_works;
    stats.updates_read = log.updates_read;
    stats.anchors_on_main_page = log.anchors_on_main_page;
  }
  return stats;
}

// ---------------------------------------------------------------------------
// Data Quality
// ---------------------------------------------------------------------------
// Each finding is a collapsed <details> in the siblings' audit markup. Rows are
// built as DOM nodes, never as HTML strings: the titles come out of tree.json.

function h(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
  for (const c of children) node.append(c);
  return node;
}

function primaryUrl(work) {
  const files = work.files || [];
  const xml = files.find((f) => f.endsWith(".xml"));
  const htm = files.find((f) => f.endsWith(".htm") && !f.includes("/transformations/"));
  return `${MIRROR_ROOT}/${xml || htm || files[0] || ""}`;
}

function workLink(work) {
  return h("a", { href: primaryUrl(work), target: "_blank", rel: "noopener" }, work.title);
}

function auditItem(summary, intro, rows) {
  const details = h("details", {},
    h("summary", { class: "audit-summary" }, h("span", {}, summary)));
  if (intro) details.append(h("p", { style: "margin-left: 1.6em;" }, intro));
  const list = h("ul", { style: "margin-left: 1.6em;" });
  for (const row of rows) list.append(row.tagName === "LI" ? row : h("li", {}, row));
  details.append(list);
  return h("li", { class: "audit-item" }, details);
}

// Works bucketed by top-level category, largest bucket first.
function byDomain(works) {
  const groups = new Map();
  for (const w of works) {
    if (!groups.has(w.domain)) groups.set(w.domain, []);
    groups.get(w.domain).push(w);
  }
  return [...groups.entries()].sort((a, b) => b[1].length - a[1].length);
}

function renderAudit(tree) {
  const list = document.getElementById("auditList");
  if (!list) return;
  const works = tree.works || [];
  list.innerHTML = "";

  const variants = authorVariants(works)
    .map((sp) => [...sp.entries()].sort((a, b) => b[1] - a[1]))
    .sort((a, b) => a[0][0].localeCompare(b[0][0]));
  list.append(auditItem(
    `Authors spelled two ways across the two layers (${variants.length} names)`,
    "A legacy file's <title> is plain ASCII; the TEI header carries diacritics. " +
    "Where an author has works in both layers the two spellings never meet, so the " +
    "author axis lists the same person twice. Works under each spelling in parentheses.",
    variants.map((sp) => sp.map(([name, n]) => `${name} (${n})`).join(" · "))));

  const orphans = works.filter((w) => w.tei && !hasLegacyFile(w))
    .sort((a, b) => a.title.localeCompare(b.title));
  list.append(auditItem(
    `TEI files that name no legacy source (${orphans.length} files)`,
    "Every other TEI header points at the legacy file it was converted from, which is " +
    "also where the Atlas reads a category. These carry no such reference, whether " +
    "because they were born in TEI or because the reference was lost, and so sit " +
    `outside GRETIL's categories under "${NO_LEGACY_DOMAIN}".`,
    orphans.map((w) => h("span", {}, workLink(w), " — ", h("code", {}, w.id)))));

  const legacy = works.filter((w) => !w.tei);
  const legacyGroups = byDomain(legacy).map(([domain, ws]) => {
    const inner = h("ul", { style: "margin-left: 1.6em;" });
    for (const w of ws.sort((a, b) => a.title.localeCompare(b.title))) {
      const n = (w.renderings || []).length;
      inner.append(h("li", {}, workLink(w),
        w.author ? ` — ${w.author}` : "", n > 1 ? ` (${n} renderings)` : ""));
    }
    return h("li", { class: "audit-item" }, h("details", {},
      h("summary", { class: "audit-summary" }, h("span", {}, `${domain} (${ws.length})`)), inner));
  });
  const legacyItem = auditItem(
    `Texts never converted to TEI (${legacy.length} texts)`,
    "Present in the legacy HTML tree only. Their titles and authors are whatever the " +
    "file's <title> says, without diacritics.",
    legacyGroups);
  legacyItem.querySelector("ul").style.cssText = "margin-left: 1.6em; list-style: none; padding-left: 0;";
  list.append(legacyItem);

  const undated = works.filter((w) => !w.added);
  const total = new Map(byDomain(works).map(([d, ws]) => [d, ws.length]));
  list.append(auditItem(
    `Works the update history never names (${undated.length} works)`,
    "GRETIL's history page announces additions by linking the main page's entry for a " +
    "text. A work lands here when no update links an entry that leads to its files.",
    byDomain(undated).map(([domain, ws]) =>
      `${domain} — ${nf.format(ws.length)} of ${nf.format(total.get(domain))}`)));
}

// ---------------------------------------------------------------------------
// Growth over time
// ---------------------------------------------------------------------------
// docs/data/changelog.json is built by pipeline/build_changelog.py from
// GRETIL's own update history (hist.html) joined to the main page's anchors.
// It publishes only the months in which something was added, as running
// totals; this file fills the silent months in (so the x axis is time, not
// "months with news") and takes differences for the per-period view.
//
// One band, where E-bhāratīsampat's chart stacks three: every GRETIL work is
// text, so there is no format mix to show.

const BANDS = [
  { key: "text", label: "works", cls: "gb-text" },
];

// `granularity` is months per group: 1 monthly, 3 quarterly, 12 yearly. Year
// is the default because two hundred monthly bars is a texture, not a reading.
const growthState = { mode: "cumulative", metric: "count", granularity: 12 };

// What one published period says, as running totals per band.
function readPeriod(p) {
  return {
    count: { text: p.cumulative_text_count || 0 },
    bytes: { text: p.cumulative_iast_bytes_total || 0 },
  };
}

const ZERO = { count: { text: 0 }, bytes: { text: 0 } };

function diffBands(now, before) {
  const out = {};
  for (const b of BANDS) out[b.key] = Math.max(0, (now[b.key] || 0) - (before[b.key] || 0));
  return out;
}

// Every calendar month from the first published period to the last. A month
// with no period carries the previous totals forward and adds nothing.
function monthlySeries(log) {
  const src = log.periods || [];
  if (!src.length) return [];
  const byMonth = new Map(src.map((p) => [p.date.slice(0, 7), p]));
  const last = src[src.length - 1].date.slice(0, 7);
  let [y, m] = src[0].date.slice(0, 7).split("-").map(Number);
  const out = [];
  let prev = ZERO;
  for (;;) {
    const key = `${y}-${String(m).padStart(2, "0")}`;
    const cum = byMonth.has(key) ? readPeriod(byMonth.get(key)) : prev;
    out.push({
      period: key,
      cum,
      add: { count: diffBands(cum.count, prev.count), bytes: diffBands(cum.bytes, prev.bytes) },
    });
    prev = cum;
    if (key === last) break;
    m += 1;
    if (m > 12) { m = 1; y += 1; }
  }
  return out;
}

// "2006" at year grouping, "2006-Q3" at quarter -- named for the calendar
// period the group covers, as in the sibling charts.
function groupLabel(first, size) {
  const year = first.period.slice(0, 4);
  if (size >= 12) return year;
  return `${year}-Q${Math.floor((Number(first.period.slice(5, 7)) - 1) / 3) + 1}`;
}

// Calendar chunks of `size` months. Running totals take the chunk's last
// month; additions sum. Mixing those two rules up is the one way this can go
// quietly wrong.
function groupSeries(series, size) {
  if (size <= 1) return series;
  const groups = [];
  let chunk = [], chunkKey = null;
  const flush = () => {
    if (!chunk.length) return;
    const sumBands = (metric) => {
      const out = {};
      for (const b of BANDS) out[b.key] = chunk.reduce((s, p) => s + (p.add[metric][b.key] || 0), 0);
      return out;
    };
    groups.push({
      period: groupLabel(chunk[0], size),
      cum: chunk[chunk.length - 1].cum,
      add: { count: sumBands("count"), bytes: sumBands("bytes") },
    });
    chunk = [];
  };
  for (const p of series) {
    const month = Number(p.period.slice(5, 7)) - 1;
    const key = `${p.period.slice(0, 4)}:${Math.floor(month / size)}`;
    if (key !== chunkKey) flush();
    chunkKey = key;
    chunk.push(p);
  }
  flush();
  return groups;
}

// Bytes, abbreviated, in decimal units (1 MB = 1e6 bytes).
function fmtSize(n) {
  if (n >= 1e9) return `${Number((n / 1e9).toFixed(2))} GB`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(0)} MB`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)} KB`;
  return `${n} B`;
}

function fmtValue(n) {
  return growthState.metric === "size" ? fmtSize(n) : n.toLocaleString();
}

function bandValues(p) {
  const side = growthState.mode === "cumulative" ? p.cum : p.add;
  return side[growthState.metric === "size" ? "bytes" : "count"];
}

// A round number at or above `n`, and the step between gridlines, so the
// tallest bar stops at a labelled tick. Whole steps only: these are counts of
// works or of bytes.
function niceScale(n) {
  const pow = Math.pow(10, Math.floor(Math.log10(n)));
  for (const mult of [0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10]) {
    const step = mult * pow;
    if (!Number.isInteger(step)) continue;
    const intervals = Math.ceil(n / step);
    if (intervals >= 3 && intervals <= 5) return { top: intervals * step, step };
  }
  return { top: Math.ceil(n / pow) * pow, step: pow };
}

function drawGrowth(series, chartEl) {
  const periods = groupSeries(series, growthState.granularity);
  const totalOf = (p) => BANDS.reduce((s, b) => s + (bandValues(p)[b.key] || 0), 0);
  const { top: max, step } = niceScale(Math.max(...periods.map(totalOf), 1));

  chartEl.innerHTML = "";
  const chart = document.createElement("div");
  const dense = periods.length > 30;
  chart.className = "gb-chart" + (dense ? " gb-dense" : "");
  // Label about a dozen columns, whatever the granularity; the tooltip still
  // names every period exactly.
  const labelEvery = Math.max(1, Math.round(periods.length / 12));

  const axis = document.createElement("div");
  axis.className = "gb-axis";
  const grid = document.createElement("div");
  grid.className = "gb-grid";
  grid.setAttribute("aria-hidden", "true");
  for (let v = 0; v <= max; v += step) {
    const tick = document.createElement("div");
    tick.className = "gb-tick";
    tick.style.bottom = `${(v / max) * 100}%`;
    tick.textContent = fmtValue(v);
    axis.prepend(tick);
    const line = document.createElement("div");
    line.className = "gb-line";
    line.style.bottom = `${(v / max) * 100}%`;
    grid.appendChild(line);
  }
  chart.append(axis, grid);

  periods.forEach((p, i) => {
    const col = document.createElement("div");
    col.className = "gb-col";
    const stack = document.createElement("div");
    stack.className = "gb-stack";
    const values = bandValues(p);
    for (const band of [...BANDS].reverse()) {
      const v = values[band.key] || 0;
      if (!v) continue;
      const seg = document.createElement("div");
      seg.className = `gb-seg ${band.cls}`;
      seg.style.height = `${(v / max) * 100}%`;
      stack.appendChild(seg);
    }
    col.appendChild(stack);

    const lbl = document.createElement("div");
    lbl.className = "gb-year";
    const showTick = i % labelEvery === 0
      || (i === periods.length - 1 && (periods.length - 1) % labelEvery > labelEvery / 2);
    if (showTick) lbl.textContent = p.period;
    col.appendChild(lbl);

    const unit = growthState.metric === "size" ? "" : " works";
    col.title = `${p.period} — ${growthState.mode === "cumulative" ? "total" : "added"}: ` +
      `${fmtValue(totalOf(p))}${unit}`;
    chart.appendChild(col);
  });
  chartEl.appendChild(chart);
}

function renderGrowth(series, chartEl) {
  drawGrowth(series, chartEl);
  for (const btn of document.querySelectorAll("#growthControls button")) {
    // String(...) on both sides: granularity is a number in state and a
    // string in the DOM.
    const on = String(growthState[btn.dataset.axis]) === btn.dataset.value;
    btn.classList.toggle("gb-on", on);
    btn.setAttribute("aria-pressed", String(on));
  }
}

function initGrowth(log) {
  const chartEl = document.getElementById("growthChart");
  if (!chartEl) return;
  const series = log ? monthlySeries(log) : [];
  if (!series.length) {
    chartEl.textContent = "Growth data unavailable.";
    return;
  }
  const controls = document.getElementById("growthControls");
  if (controls) {
    controls.addEventListener("click", (ev) => {
      const btn = ev.target.closest("button[data-value]");
      if (!btn) return;
      const { axis, value } = btn.dataset;
      growthState[axis] = axis === "granularity" ? Number(value) : value;
      renderGrowth(series, chartEl);
    });
  }
  renderGrowth(series, chartEl);
}

// ---------------------------------------------------------------------------

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.json();
}

(async () => {
  // The changelog is optional to everything but the chart: without it the
  // prose's growth figures show a dash and the rest of the page still fills.
  let log = null;
  try {
    log = await fetchJson(CHANGELOG_URL);
  } catch (e) {
    console.log("about: could not load changelog", e);
  }
  initGrowth(log);
  try {
    const tree = await fetchJson(TREE_URL);
    fillStats(deriveStats(tree, log));
    renderAudit(tree);
  } catch (e) {
    console.log("about: could not load tree", e);
    fillStats({});
    const list = document.getElementById("auditList");
    if (list) list.textContent = "Data unavailable.";
  }
})();

// The About page's one outbound link to the parent project. The markup carries
// the production URL; when this Atlas is served from localhost the parent is
// too, on the port its own serve_docs.py uses.
const PARENT_LOCAL_PORT = 8000;

// Host test copied from the parent's local-links.js, deliberately identical.
function isLocal(hostname) {
  return hostname === "localhost"
      || hostname === "127.0.0.1"
      || hostname === "[::1]"
      || hostname === "::1"
      || hostname.endsWith(".localhost");
}

if (isLocal(location.hostname)) {
  const parentLink = document.getElementById("parentLink");
  if (parentLink) {
    parentLink.href = `http://${location.hostname}:${PARENT_LOCAL_PORT}/`;
    parentLink.dataset.localized = "true";  // visible in devtools, as in the parent
  }
}
