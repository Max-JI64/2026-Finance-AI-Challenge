const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("v5/static/demo-fallback.js", "utf8");
const snapshot = JSON.parse(fs.readFileSync("v5/static/fallback-example.json", "utf8"));
async function check(fetch, expectedLevel) {
  let panel;
  let scenarioButtons;
  const context = {
    window: {}, fetch, AbortController, setTimeout, clearTimeout,
    document: {
      getElementById: () => panel,
      createElement: () => ({style: {}, querySelectorAll: selector => {
        if (selector === "[data-demo-scenario]") {
          scenarioButtons = [0,1,2].map(index => ({dataset:{demoScenario:String(index)}}));
          return scenarioButtons;
        }
        return [];
      }, querySelector: () => ({})}),
      body: {append: node => {panel = node;}},
      addEventListener() {},
    },
  };
  vm.createContext(context);
  vm.runInContext(source, context);
  assert.equal(context.window.demoFallbackValidation.valid(snapshot), true);
  assert.equal(context.window.demoFallbackValidation.valid(context.window.demoFallbackValidation.fixedExample()), true);
  assert.equal(await context.window.openDemoFallback(), true);
  assert.ok(panel.innerHTML.includes(expectedLevel + "차 fallback"));
  assert.ok(panel.innerHTML.includes("입력한 사업장의 예측 결과가 아닙니다"));
  assert.equal((panel.innerHTML.match(/<svg /g) || []).length, 2);
  assert.equal((panel.innerHTML.match(/<polyline /g) || []).length, 7);
  assert.equal((panel.innerHTML.match(/data-demo-scenario=/g) || []).length, 3);
  assert.equal((panel.innerHTML.match(/data-demo-row=/g) || []).length, 4);
  assert.ok(panel.innerHTML.includes("6개월 뒤 남은 부채"));
  assert.ok(!panel.innerHTML.includes("NaN"));
  const centralHtml = panel.innerHTML;
  scenarioButtons[0].onclick();
  assert.notEqual(panel.innerHTML, centralHtml);
  assert.ok(panel.innerHTML.includes("하방 예시"));
  assert.equal((panel.innerHTML.match(/<polyline /g) || []).length, 7);
  scenarioButtons[1].onclick();
  assert.equal(panel.innerHTML, centralHtml);
}
(async () => {
  await check(async () => ({ok:true,json:async () => snapshot}), 2);
  await check(async () => {throw new Error("offline");}, 3);
  await check(async () => ({ok:true,json:async () => ({rows:[]})}), 3);
  await check(async (_url, options) => new Promise((_resolve,reject) => {
    options.signal.addEventListener("abort", () => reject(new Error("timeout")));
  }), 3);
  console.log("PASS: snapshot/offline/corrupt/timeout; two graphs, seven curves, scenario switching and numeric tables");
})().catch(error => {console.error(error);process.exitCode=1;});
