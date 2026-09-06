const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const {DatabaseSync} = require("node:sqlite");
const {createHash} = require("node:crypto");
const snapshot = JSON.parse(fs.readFileSync("v5/static/notice-fallback-results.json", "utf8"));
const provider = fs.readFileSync("v5/static/notice-fallback.js", "utf8");
const extension = fs.readFileSync("v5/static/v5-extension.js", "utf8").replace(/\r\n/g, "\n");
const ids = ["POL_SEMAS_STABILITY_VOUCHER_2026", "POL_SEOUL_CLOSURE_2026", "POL_SEMAS_RECHALLENGE_2026"];
assert.deepEqual(Object.keys(snapshot.policies).sort(), [...ids].sort());
const clone = x => JSON.parse(JSON.stringify(x));
function extract(name) {
  const start = extension.search(new RegExp(`^(?:async )?function ${name}\\(`, "m"));
  assert.ok(start >= 0, name);
  return extension.slice(start, extension.indexOf("\n}", start) + 2);
}
const names = ["requestV5NoticeExtraction", "v5NoticeProvenance", "v4NoticeExtractionKey", "v4NoticeFieldConfirmationKey",
  "loadV4NoticeExtractions", "refreshV4NoticeExtraction", "renderV4NoticeExtraction", "v5NoticeFieldCard", "renderV5NoticeExtraction"];
function setup(query = "?demo=1", apiMode = "error", fileMode = "ok") {
  let apiCalls = 0, fileCalls = 0;
  const context = {URLSearchParams, AbortController,
    window: {location: {search: query}, setTimeout: fn => setTimeout(fn, 10), clearTimeout},
    console: {warn() {}, error() {}},
    state: {noticeFieldPriority: []},
    v4State: {noticeExtractions: new Map(), noticeFieldConfirmations: new Set(), currentPolicy: snapshot.policies[ids[0]].request},
    escapeHtml: s => String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;"),
    safeUrl: s => s,
    v4SelectedNoticeCandidates: () => ids.map(id => snapshot.policies[id].request),
    renderV4Preparation() {},
    api: async (_path, options) => {
      apiCalls++;
      const policy = JSON.parse(options.body);
      const response = clone(snapshot.policies[policy.policy_id].response);
      if (apiMode === "ok") return response;
      if (apiMode === "unavailable") return {...response, analysis_status: "unavailable", fields: []};
      if (apiMode === "empty") return {...response, fields: []};
      if (apiMode === "timeout") throw new Error("AbortError");
      throw new Error("HTTP 503");
    },
    fetch: async (_url, options) => {
      fileCalls++;
      if (fileMode === "offline") throw new Error("offline");
      if (fileMode === "timeout") return new Promise((_resolve, reject) => options.signal.addEventListener("abort", () => reject(new Error("AbortError"))));
      return {ok: true, json: async () => fileMode === "corrupt" ? {} : clone(snapshot)};
    },
  };
  vm.createContext(context);
  vm.runInContext(provider, context);
  vm.runInContext(names.map(extract).join("\n"), context);
  return {context, counts: () => ({apiCalls, fileCalls})};
}

// Verify the stored successful response identity and each quoted source without calling GPT.
const db = new DatabaseSync("rag/index/policy_re8.sqlite3", {readOnly: true});
const canonical = s => s.replace(/\s+/g, "").normalize("NFKC");
for (const id of ids) {
  const record = snapshot.policies[id], response = record.response;
  assert.equal(response.model, "gpt-5.6-luna");
  assert.equal(response.external_ai_used, true);
  assert.equal(response.cache_status, "fresh");
  assert.equal(record.request.force_refresh, true);
  assert.ok(record.captured_at && record.service_url.endsWith(".run.app"));
  const chunks = db.prepare("SELECT * FROM policy_chunks WHERE policy_id=? AND policy_version=? ORDER BY chunk_id").all(id, response.policy_version);
  assert.equal(response.source_digest, createHash("sha256").update(chunks.map(c => `${c.chunk_id}:${c.content_hash}`).join("|")).digest("hex"));
  for (const field of response.fields) {
    if (field.status === "found") {
      assert.equal(field.validation_status, "verified");
      assert.ok(field.evidence.length);
      for (const e of field.evidence) assert.ok(canonical(chunks.find(c => c.chunk_id === e.chunk_id).text).includes(canonical(e.quote)), `${id}:${field.key}`);
    } else {
      assert.equal(field.value, "");
      assert.equal(field.items.length, 0);
    }
  }
}
db.close();

async function check(query, apiMode, fileMode, level) {
  const {context: c, counts} = setup(query, apiMode, fileMode);
  await c.loadV4NoticeExtractions();
  for (const id of ids) {
    const record = snapshot.policies[id], policy = record.request;
    const result = c.v4State.noticeExtractions.get(c.v4NoticeExtractionKey(policy));
    assert.equal(result.analysis_status, "completed");
    assert.equal(result.fallback?.level, level);
    assert.deepEqual(clone(result.fields), record.response.fields); // exact GPT response, including missing fields
    const plan = {policy};
    let html = c.renderV5NoticeExtraction(plan);
    assert.ok(html.includes("v5-next-notice") && html.includes("접수기간부터 확인하세요"));
    if (level) assert.ok(html.includes("실제 GPT 분석 저장본") && html.includes("새 AI 응답 아님"));
    for (const field of result.fields) {
      assert.ok(html.includes(field.label));
      c.v4State.noticeFieldConfirmations.add(c.v4NoticeFieldConfirmationKey(policy, result, field.key));
    }
    html = c.renderV5NoticeExtraction(plan);
    assert.ok(html.includes("여기서 확인할 내용은 모두 끝났습니다"));
  }
  if (c.window.v5NoticeFallback.testMode()) assert.equal(counts().apiCalls, 0);
  else assert.equal(counts().apiCalls, 3);
}
async function main() {
  await check("?demo=1", "ok", "ok", undefined);
  for (const mode of ["error", "unavailable", "empty", "timeout"]) await check("?demo=1", mode, "ok", 2);
  await check("", "error", "ok", 2);
  for (const fileMode of ["offline", "corrupt", "timeout"]) await check("?demo=1", "error", fileMode, 3);
  await check("?demo=1&notice_fallback=1", "ok", "ok", 2);
  await check("?demo=1&notice_fallback=2", "ok", "ok", 3);
  await check("?notice_fallback=1", "ok", "ok", undefined);
  await check("?demo=1&fallback=1", "ok", "ok", undefined);
  const {context: c} = setup();
  const policy = snapshot.policies[ids[0]].request;
  await c.loadV4NoticeExtractions();
  const before = c.v4State.noticeExtractions.get(c.v4NoticeExtractionKey(policy));
  await c.refreshV4NoticeExtraction(policy.policy_id);
  const after = c.v4State.noticeExtractions.get(c.v4NoticeExtractionKey(policy));
  assert.equal(after.fallback.kind, "retained");
  assert.deepEqual(clone(after.fields), clone(before.fields));
  for (const wrong of [{...policy, policy_version: "future"}, {...policy, policy_id: "unknown"}]) {
    await assert.rejects(() => c.window.v5NoticeFallback.load(wrong));
  }
  await assert.rejects(() => c.window.v5NoticeFallback.load(policy, {sourceDigest: "f".repeat(64)}));
  await checkNavigation();
  console.log("PASS: 3 exact live GPT records and source evidence; 13 recovery scenarios; original cards/confirmations; refresh retention; policy/version/digest isolation");
}

async function checkNavigation() {
  const app = fs.readFileSync("v5/static/app.js", "utf8").replace(/\r\n/g, "\n");
  function appFunction(name) {
    const start = app.indexOf(`function ${name}(`);
    return app.slice(start, app.indexOf("\n}", start) + 2);
  }
  const policies = ids.map(id => snapshot.policies[id].request);
  for (const returnSelector of ["[data-v5-return-comparison]", "[data-step]:footer", "[data-step]:nav"]) {
    const {context: c} = setup("?demo=1&notice_fallback=1");
    const nodes = new Map(), listeners = [];
    c.byId = id => {
      if (!nodes.has(id)) nodes.set(id, {hidden: false, textContent: "", focus() {}, classList: {toggle() {}}});
      return nodes.get(id);
    };
    c.document = {querySelectorAll: () => [], addEventListener: (type, handler) => {if (type === "click") listeners.push(handler);}};
    c.window.scrollTo = () => {};
    c.window.requestAnimationFrame = fn => fn();
    c.state.data = {policy_discovery: {candidates: policies}};
    c.state.focusedPolicyId = ids[0];
    c.policyFocusCandidates = () => policies;
    c.policyAlternative = () => null;
    c.syncPolicySearchToAlternative = () => {};
    c.renderPolicyFocus = () => {};
    c.renderCharts = () => {};
    c.saveV4Session = () => {};
    c.renderV4Preparation = () => {
      if (c.v4State.plan) c.rendered = {id: c.v4State.plan.policy.policy_id, html: c.renderV5NoticeExtraction(c.v4State.plan)};
    };
    vm.runInContext(["loadV4ApplicationPlan", "syncV5PreparationPolicy"].map(extract).join("\n"), c);
    vm.runInContext(appFunction("showStep") + "\n" + appFunction("focusPolicy"), c);
    for (const source of [app, extension]) {
      const start = source.indexOf('document.addEventListener("click", async (event) => {');
      vm.runInContext(source.slice(start, source.indexOf("\n});", start) + 4), c);
    }
    async function click(selector, dataset) {
      const element = {dataset};
      await Promise.all(listeners.map(fn => fn({preventDefault() {}, target: {
        closest: s => s === selector ? element : null,
      }})));
      // Let batch fallback promises settle without timers or external requests.
      for (let i = 0; i < 15; i++) await Promise.resolve();
    }
    await c.loadV4NoticeExtractions();
    await click("[data-v4-start-application]", {v4StartApplication: ids[0]});
    for (const field of snapshot.policies[ids[0]].response.fields) await click("[data-v4-confirm-notice-field]", {v4ConfirmNoticeField: field.key});
    assert.ok(c.rendered.html.includes("6 / 6개 확인"));
    await click(returnSelector.startsWith("[data-step]") ? "[data-step]" : returnSelector, {step: "decision"});
    await click("[data-focus-policy]", {focusPolicy: ids[1]});
    await click("[data-step]", {step: "preparation"});
    assert.equal(c.rendered.id, ids[1]);
    assert.ok(c.rendered.html.includes("0 / 6개 확인"), returnSelector);
    await click("[data-v4-confirm-notice-field]", {v4ConfirmNoticeField: "application_period"});
    assert.ok(c.rendered.html.includes("1 / 6개 확인"));
    await click("[data-step]", {step: "decision"});
    await click("[data-focus-policy]", {focusPolicy: ids[0]});
    await click("[data-step]", {step: "preparation"});
    assert.equal(c.rendered.id, ids[0]);
    assert.ok(c.rendered.html.includes("6 / 6개 확인"));
    await click("[data-v4-start-application]", {v4StartApplication: ids[1]});
    assert.equal(c.rendered.id, ids[1]);
    assert.ok(c.rendered.html.includes("1 / 6개 확인"));
    await c.loadV4ApplicationPlan("unknown-policy");
    assert.equal(c.v4State.plan.policy.policy_id, ids[1]);
    c.policyFocusCandidates = () => [];
    await click("[data-step]", {step: "preparation"});
    assert.equal(c.v4State.plan, null);
    assert.equal(c.byId("v4-preparation-result").hidden, true);
  }
  console.log("PASS: all 3 return routes, both preparation entry routes, A=6/6 B=0/6 then 1/6 isolation and restoration, empty selection");
}
main().catch(error => {console.error(error); process.exitCode = 1;});
