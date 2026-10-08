// about.html's scripted behaviour: the theme toggle and the headline figures.
//
// The figures come from data/tree.json's `all_stats` and data/changelog.json,
// never from the markup -- a number typed into the page is a number that goes
// stale. Each <span data-stat="key"> is filled from the stats block; an absent
// figure renders as an em dash rather than a zero.

const SUN_ICON = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 3v2"/><path d="M12 19v2"/><path d="M5 5l1.4 1.4"/><path d="M17.6 17.6L19 19"/><path d="M3 12h2"/><path d="M19 12h2"/><path d="M5 19l1.4-1.4"/><path d="M17.6 6.4L19 5"/></svg>`;
const MOON_ICON = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z"/></svg>`;

function updateThemeToggleLabel() {
  const btn = document.getElementById("themeToggle");
  if (!btn) return;
  const dark = document.documentElement.getAttribute("data-theme") === "dark";
  btn.innerHTML = dark ? SUN_ICON : MOON_ICON;
  btn.title = dark ? "Switch to light theme" : "Switch to dark theme";
}

const themeToggle = document.getElementById("themeToggle");
if (themeToggle) {
  updateThemeToggleLabel();
  themeToggle.addEventListener("click", () => {
    const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateThemeToggleLabel();
  });
}

const nf = new Intl.NumberFormat("en-US");

function fill(stats) {
  for (const span of document.querySelectorAll("[data-stat]")) {
    const key = span.dataset.stat;
    const unit = span.dataset.unit;
    let v = stats[key];
    if (typeof v === "number" && unit === "mb") v = (v / 1e6).toFixed(0);
    else if (typeof v === "number" && unit === "gb") v = (v / 1e9).toFixed(2);
    else if (typeof v === "number") v = nf.format(v);
    span.textContent = v == null || v === "" ? "—" : String(v);
  }
}

(async () => {
  try {
    const tree = await (await fetch("./data/tree.json")).json();
    const stats = { ...(tree.all_stats || {}) };
    try {
      const log = await (await fetch("./data/changelog.json")).json();
      const last = (log.periods || []).slice(-1)[0] || {};
      stats.changelog_months = (log.periods || []).length;
      stats.changelog_first = (log.periods || [])[0]?.date?.slice(0, 7);
      stats.changelog_last = last.date?.slice(0, 7);
      stats.undated_works = log.undated_works;
    } catch (e) { /* no changelog: the spans show a dash */ }
    fill(stats);
  } catch (e) {
    console.log("about: could not load data", e);
    fill({});
  }
})();
