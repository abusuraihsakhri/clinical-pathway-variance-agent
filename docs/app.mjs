import { PROTOCOLS, DEFAULT_LOS, analyzeCase } from "./engine.mjs";

const $ = (id) => document.getElementById(id);
const state = { milestoneInputs: new Map(), result: null };
const els = {
  specialty: $("specialty"), expectedLos: $("expectedLos"), dailyRate: $("dailyRate"), complications: $("complications"),
  milestoneList: $("milestoneList"), milestoneCount: $("milestoneCount"), analyze: $("analyzeBtn"), example: $("exampleBtn"), reset: $("resetBtn"),
  theme: $("themeBtn"), export: $("exportBtn"), empty: $("emptyState"), results: $("results"), error: $("errorMessage"), varianceList: $("varianceList"),
};

for (const specialty of Object.keys(PROTOCOLS)) {
  const option = document.createElement("option"); option.value = specialty; option.textContent = titleCase(specialty); els.specialty.append(option);
}

function renderMilestones() {
  state.milestoneInputs.clear(); els.milestoneList.replaceChildren();
  const protocol = PROTOCOLS[els.specialty.value]; els.milestoneCount.textContent = `${protocol.length} items`;
  for (const [id, phase, name, weight] of protocol) {
    const row = document.createElement("div"); row.className = "milestone"; row.dataset.compliant = "true";
    const main = document.createElement("div"); main.className = "milestone-main";
    const checkbox = document.createElement("input"); checkbox.type = "checkbox"; checkbox.checked = true; checkbox.setAttribute("aria-label", `${name} achieved`);
    const label = document.createElement("div"); label.className = "milestone-name"; label.textContent = name;
    const meta = document.createElement("div"); meta.className = "milestone-meta"; meta.textContent = `${phase.replaceAll("_"," ")} · w${weight}`;
    const controls = document.createElement("div"); controls.className = "variance-controls";
    const severity = makeSelect(["MINOR","MODERATE","MAJOR","CRITICAL"], "MODERATE", `${name} severity`);
    const rootCause = makeSelect(["PATIENT_FACTOR","CLINICIAN_PRACTICE","HOSPITAL_SYSTEM","SURGICAL_COMPLICATION"], "CLINICIAN_PRACTICE", `${name} root cause`);
    controls.append(severity, rootCause); main.append(checkbox, label, meta); row.append(main, controls); els.milestoneList.append(row);
    checkbox.addEventListener("change", () => { row.dataset.compliant = String(checkbox.checked); });
    state.milestoneInputs.set(id, { checkbox, severity, rootCause });
  }
}

function makeSelect(values, selected, label) {
  const select = document.createElement("select"); select.setAttribute("aria-label", label);
  for (const value of values) { const option = document.createElement("option"); option.value = value; option.textContent = value.replaceAll("_", " "); option.selected = value === selected; select.append(option); }
  return select;
}

function resetCase() {
  els.expectedLos.value = DEFAULT_LOS[els.specialty.value]; els.dailyRate.value = "2400"; els.complications.value = "0"; renderMilestones(); clearResult();
}

function loadExample() {
  els.specialty.value = "COLORECTAL"; els.expectedLos.value = "3"; els.dailyRate.value = "2400"; els.complications.value = "0"; renderMilestones();
  setVariance("INTRA_GDFT", "MAJOR", "CLINICIAN_PRACTICE");
  setVariance("POD0_MOBILIZATION", "MINOR", "PATIENT_FACTOR");
  setVariance("POD1_SOLID_DIET", "MINOR", "PATIENT_FACTOR");
  setVariance("POD1_FOLEY_REMOVAL", "MODERATE", "CLINICIAN_PRACTICE");
  analyze();
}

function setVariance(id, severity, rootCause) { const input = state.milestoneInputs.get(id); if (!input) return; input.checkbox.checked = false; input.checkbox.dispatchEvent(new Event("change")); input.severity.value = severity; input.rootCause.value = rootCause; }

function collectMilestones() {
  const values = {};
  for (const [id, input] of state.milestoneInputs) values[id] = { status: input.checkbox.checked, severity: input.severity.value, rootCause: input.rootCause.value };
  return values;
}

function analyze() {
  try {
    state.result = analyzeCase({ specialty: els.specialty.value, expectedLos: els.expectedLos.value, dailyRate: els.dailyRate.value, complications: Number(els.complications.value), milestones: collectMilestones() });
    els.error.hidden = true; renderResults(state.result);
  } catch (error) { clearResult(); els.error.textContent = error instanceof Error ? error.message : String(error); els.error.hidden = false; }
}

function renderResults(result) {
  els.empty.hidden = true; els.results.hidden = false; els.export.disabled = false;
  $("cciMetric").textContent = `${result.cumulativeComplianceIndex.toFixed(1)}%`;
  $("complianceMetric").textContent = `${result.compliantMilestones}/${result.totalMilestones}`;
  $("burdenMetric").textContent = result.totalVarianceBurdenScore.toFixed(1);
  $("tierMetric").textContent = result.varianceTier;
  $("losMetric").textContent = `+${result.predictedExcessLosDays.toFixed(2)} d`;
  $("costMetric").textContent = currency(result.estimatedExcessCostUsd);
  $("varianceCount").textContent = `${result.variances.length} recorded`;
  els.varianceList.replaceChildren();
  if (!result.variances.length) { const p = document.createElement("p"); p.className = "milestone-meta"; p.textContent = "No pathway variances were marked."; els.varianceList.append(p); return; }
  for (const variance of result.variances) {
    const item = document.createElement("article"); item.className = "variance-item";
    const title = document.createElement("strong"); title.textContent = variance.name;
    const meta = document.createElement("p"); meta.textContent = `${variance.severity.replaceAll("_"," ")} · ${variance.rootCause.replaceAll("_"," ")} · +${variance.losImpact.toFixed(2)} d illustrative LOS`;
    item.append(title, meta); els.varianceList.append(item);
  }
}

function clearResult() { state.result = null; els.results.hidden = true; els.empty.hidden = false; els.export.disabled = true; els.error.hidden = true; }
function exportJson() { if (!state.result) return; const blob = new Blob([JSON.stringify(state.result, null, 2)], { type: "application/json" }); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = `pathway-variance-${els.specialty.value.toLowerCase()}.json`; a.click(); URL.revokeObjectURL(url); }
function titleCase(value) { return value.toLowerCase().replace(/(^|_)([a-z])/g, (_, p, c) => `${p ? " " : ""}${c.toUpperCase()}`); }
function currency(value) { return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value); }
function setTheme(theme) { document.documentElement.dataset.theme = theme; localStorage.setItem("cpv-theme", theme); els.theme.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme"); }

els.specialty.addEventListener("change", () => { els.expectedLos.value = DEFAULT_LOS[els.specialty.value]; renderMilestones(); clearResult(); });
els.analyze.addEventListener("click", analyze); els.example.addEventListener("click", loadExample); els.reset.addEventListener("click", resetCase); els.export.addEventListener("click", exportJson);
els.theme.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
setTheme(localStorage.getItem("cpv-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")); resetCase();
