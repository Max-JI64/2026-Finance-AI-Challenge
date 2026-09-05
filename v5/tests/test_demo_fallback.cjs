const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("v5/static/demo-fallback.js", "utf8");
const app = fs.readFileSync("v5/static/app.js", "utf8").replace(/\r\n/g, "\n");
const snapshot = JSON.parse(fs.readFileSync("v5/static/fallback-example.json", "utf8"));
function extract(name) {
  const start = app.search(new RegExp("^(?:async )?function " + name + "\\(", "m"));
  assert.ok(start >= 0, name);
  const lineEnd = app.indexOf("\n", start);
  const end = app.slice(start, lineEnd).endsWith("}") ? lineEnd : app.indexOf("\n}", start) + 2;
  return app.slice(start, end);
}
const functions = ["runComparison", "applyGoalRanking", "scenarioComparison", "scenarioValuesDiffer", "renderResults",
  "renderStoreSignals", "selectedScenarioPercent", "selectedScenarioSummary", "updateScenarioApplicationStatus",
  "renderPolicyDiscovery", "renderPolicyResults", "renderPolicyScenarios", "policyFundingText", "baselineCashNeed",
  "policyFocusCandidates", "policyAlternative", "signedMoney", "v5MetricDelta", "renderPolicyFocus", "renderCharts",
  "alternativeReadiness", "humanizeText", "selectScenario", "showStep", "syncPolicySearchToAlternative",
  "enableSelectedPolicyPreviews"];
async function check(query, fetch, expectedLevel, apiMode = "error") {
  const nodes = new Map(), graphs = new Map();
  const node = id => {
    if (!nodes.has(id)) nodes.set(id, {id, hidden: true, textContent: "", innerHTML: "", options: [], value: "",
      dataset: {}, classList: {toggle(_name, active) { this.active = active; }}, scrollIntoView() {}, focus() {}});
    return nodes.get(id);
  };
  const notices = [node("notice-diagnosis"), node("notice-decision")];
  const screens = ["business", "finance", "diagnosis", "decision"].map(node);
  let calls = 0, marketCalls = 0;
  const context = {
    window: {location: {search: query}, scrollTo() {}, requestAnimationFrame: fn => fn(), setTimeout, clearTimeout},
    fetch, AbortController, URL, URLSearchParams, setTimeout, clearTimeout, console: {warn() {}, error: console.error},
    document: {getElementById: node, documentElement: {}, querySelector: () => node("radio"),
      querySelectorAll: selector => selector === "[data-fallback-notice]" ? notices : selector === ".screen" ? screens : []},
    getComputedStyle: () => ({getPropertyValue: () => "#777"}),
    validateBusiness() {}, validateFinance() {}, comparisonRequest: () => ({}), comparisonCacheKey: () => "key",
    situationContextPayload: () => null, loadMarketScenarios: async () => { marketCalls++; },
    api: async () => {
      calls++;
      if (apiMode === "error") throw new Error("HTTP 503");
      if (apiMode === "malformed") return {};
      const value = JSON.parse(JSON.stringify(context.window.demoFallback.buildResults(snapshot, 2).central));
      delete value.fallback;
      if (apiMode === "partial") value.conditional_policy_fallbacks = [{reason: "failure"}];
      return value;
    },
    showLoading() {}, hideLoading() {}, toast: message => { throw new Error("Unexpected toast: " + message); },
    updateSummary() {}, revenueValues: () => [100, 110], formatPercent: value => String(value),
    drawChart: (canvas, series) => graphs.set(canvas.id, series),
  };
  vm.createContext(context);
  vm.runInContext(source, context);
  vm.runInContext(app.slice(0, app.indexOf("function setPresentationPresetReady")), context);
  vm.runInContext(app.slice(app.indexOf("const v5MetricLabels"), app.indexOf("function v5MetricDelta")), context);
  vm.runInContext(functions.map(extract).join("\n"), context);
  const state = vm.runInContext("state", context);
  assert.equal(await context.runComparison(), true);
  assert.equal(state.data.fallback?.level, expectedLevel);
  assert.equal(node("diagnosis").classList.active, true);
  assert.equal(node("diagnosis-result").hidden, false);
  assert.ok(node("diagnosis-metrics").innerHTML.includes("만원"));
  assert.equal(graphs.get("baseline-chart").length, 3);
  if (expectedLevel) {
    assert.equal(notices[0].hidden, false);
    assert.equal(graphs.get("comparison-chart").length, 4);
    assert.ok(!node("v4-policy-focus-content").innerHTML.includes("효과 미산정"));
    assert.ok(!node("six-month-summary").innerHTML.includes("NaN"));
    const central = state.data.intervention_results[0].metrics.week13_ending_cash;
    await context.selectScenario("downside", false);
    assert.notEqual(state.data.intervention_results[0].metrics.week13_ending_cash, central);
    assert.equal(graphs.get("comparison-chart").length, 4);
    await context.selectScenario("central", false);
    assert.equal(state.data.intervention_results[0].metrics.week13_ending_cash, central);
    context.enableSelectedPolicyPreviews();
    assert.equal(await context.runComparison("decision"), true);
    assert.equal(node("decision").classList.active, true);
    assert.equal(node("decision-result").hidden, false);
    assert.equal(graphs.get("comparison-chart").length, 4);
    for (const result of Object.values(state.scenarioResults)) {
      for (const row of result.intervention_results) {
        assert.equal(row.weekly_13.length, 13);
        assert.equal(row.weekly_13[12].closing_cash, row.metrics.week13_ending_cash);
        assert.ok(Object.values(row.metrics).every(Number.isFinite));
      }
    }
  } else assert.equal(notices[0].hidden, true);
  if (context.window.demoFallback.testMode()) { assert.equal(calls, 0); assert.equal(marketCalls, 0); }
  else assert.ok(calls > 0);
}
(async () => {
  const ok = async () => ({ok:true, json:async () => snapshot});
  await check("?demo=1&fallback=1", ok, 2);
  await check("?demo=1&fallback=2", () => {throw new Error("must not fetch snapshot");}, 3);
  await check("?demo=1", ok, 2);
  await check("", ok, 2, "partial");
  await check("", ok, 2, "malformed");
  await check("", async () => {throw new Error("offline");}, 3);
  await check("", async () => ({ok:true, json:async () => ({rows:[]})}), 3);
  await check("", async (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener("abort", () => reject(new Error("timeout")));
  }), 3);
  await check("?fallback=1", ok, undefined, "normal");
  await check("?demo=1&fallback=invalid", ok, undefined, "normal");
  assert.ok(!source.includes("document.") && !source.includes("<svg") && !source.includes("openDemoFallback"));
  console.log("PASS 10 cases: URL gating, HTTP/partial/malformed/offline/corrupt/timeout; original diagnosis/decision renderers, 3+4 curves, numeric metrics, scenario switching.");
})().catch(error => {console.error(error); process.exitCode=1;});
