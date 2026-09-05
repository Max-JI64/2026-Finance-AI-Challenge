/* Independent recovery UI: no API, model, chart library, or app state required. */
(() => {
  "use strict";
  const notice = "가상 시연 데이터 · 입력한 사업장의 예측 결과가 아닙니다. 정책 승인·지원금액을 의미하지 않습니다.";
  const labels = ["무대응", "비차입 지원 예시", "대환대출 예시", "신규 정책자금 예시"];
  const colors = ["#64748b", "#0284c7", "#a855f7", "#059669"];
  const money = value => Math.round(value).toLocaleString("ko-KR") + "원";
  const escape = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  let activeData;
  let level;
  let active = 0;
  let activeScenario = 1;
  const scenarioLabels = ["하방", "기준", "회복"];
  function exampleScenarios(baseline) {
    return scenarioLabels.map((label, index) => ({
      label,
      cash: baseline.map((value, week) => value + (index - 1) * 180000 * (week + 1)),
    }));
  }
  let loading;
  function fixedExample() {
    const data = {title: "브라우저 내장 가상 시연 사례", asOf: "2026-09-01", rows: labels.map((label, index) => {
      const cash = Array.from({length: 13}, (_, week) => {
        const baseline = 5000000 - (week + 1) * 700000;
        return baseline + (index === 1 && week >= 7 ? 3000000 : index === 2 ? (week + 1) * 120000 : index === 3 && week >= 3 ? 15000000 - (week - 3) * 150000 : 0);
      });
      return {id: String(index), label, cash, metrics: {
        week13_ending_cash: cash[12], month6_remaining_principal: [27000000,27000000,28500000,41000000][index],
        maximum_monthly_debt_service: [800000,800000,400000,1100000][index],
        total_interest_through_maturity: [9000000,9000000,11000000,12500000][index]
      }};
    })};
    data.scenarios = exampleScenarios(data.rows[0].cash);
    return data;
  }
  function valid(data) {
    const keys = ["week13_ending_cash", "month6_remaining_principal", "maximum_monthly_debt_service", "total_interest_through_maturity"];
    return data && Array.isArray(data.scenarios) && data.scenarios.length === 3 &&
      data.scenarios.every((row, index) => row.label === scenarioLabels[index] &&
        Array.isArray(row.cash) && row.cash.length === 13 && row.cash.every(Number.isFinite)) &&
      Array.isArray(data.rows) && data.rows.length === 4 && data.rows.every(row =>
      Array.isArray(row.cash) && row.cash.length === 13 && row.cash.every(Number.isFinite) &&
      row.metrics && keys.every(key => Number.isFinite(row.metrics[key])) &&
      row.cash[12] === row.metrics.week13_ending_cash) &&
      data.scenarios[1].cash.every((value, index) => value === data.rows[0].cash[index]);
  }
  function chart(rows, selected = active, title = "가상 예시 무대응 및 세 정책의 13주 현금 그래프") {
    const values = rows.flatMap(row => row.cash);
    const low = Math.min(0, ...values), high = Math.max(1, ...values), span = Math.max(1, high-low);
    const y = value => 230 - (value-low)/span*200;
    const lines = rows.map((row,index) => '<polyline fill="none" stroke="'+colors[index]+'" stroke-width="'+(index===selected?4:2)+'" points="'+row.cash.map((value,week)=>(55+week*55)+','+y(value)).join(' ')+'"/>').join("");
    return '<svg viewBox="0 0 760 270" role="img" aria-label="'+escape(title)+'"><line x1="55" x2="715" y1="'+y(0)+'" y2="'+y(0)+'" stroke="#94a3b8"/><text x="4" y="'+y(0)+'" fill="currentColor">0원</text>'+lines+'<text x="55" y="260" fill="currentColor">1주</text><text x="680" y="260" fill="currentColor">13주</text></svg>';
  }
  function render() {
    let panel = document.getElementById("demo-recovery-panel");
    if (!panel) {
      panel = document.createElement("section");
      panel.id = "demo-recovery-panel";
      panel.style.cssText = "position:fixed;inset:0;z-index:10000;overflow:auto;background:#f8fafc;color:#172033;padding:clamp(16px,4vw,48px);font:16px/1.6 system-ui";
      document.body.append(panel);
    }
    const rows = activeData.rows.map(item => {
      const cash = item.cash.map((value, week) => value + activeData.scenarios[activeScenario].cash[week] - activeData.rows[0].cash[week]);
      return {...item, cash, metrics: {...item.metrics, week13_ending_cash: cash[12]}};
    });
    const row = rows[active], baseline = rows[0];
    panel.innerHTML = '<div style="max-width:1050px;margin:auto"><p role="status" style="background:#fff0c2;padding:16px;border:2px solid #b77900">'+notice+'</p><h1>가상 사례로 정책 효과 비교</h1><p>'+escape(activeData.title)+' · '+escape(activeData.asOf)+' · '+level+'차 fallback</p><div style="display:flex;gap:8px;flex-wrap:wrap">'+rows.map((r,i)=>'<button data-demo-row="'+i+'" aria-pressed="'+(i===active)+'" style="padding:12px;border:2px solid '+colors[i]+';background:'+(i===active?'#e2e8f0':'white')+'">'+escape(labels[i])+'</button>').join("")+'</div><h2>2. 정책별 13주 현금 비교 · '+scenarioLabels[activeScenario]+' 예시</h2>'+chart(rows)+'<h2>'+escape(labels[active])+'</h2><p>무대응 대비 13주 현금 차이: <strong>'+money(row.metrics.week13_ending_cash-baseline.metrics.week13_ending_cash)+'</strong></p><div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse"><caption>고정 가상 사례의 금액 비교</caption><thead><tr><th>지표</th>'+labels.map(label=>'<th>'+escape(label)+'</th>').join("")+'</tr></thead><tbody>'+[["13주 뒤 현금","week13_ending_cash"],["6개월 뒤 남은 부채","month6_remaining_principal"],["월 최대 상환액","maximum_monthly_debt_service"],["만기까지 총이자","total_interest_through_maturity"]].map(([label,key])=>'<tr><th style="padding:12px;border-bottom:1px solid #cbd5e1">'+label+'</th>'+rows.map(r=>'<td style="padding:12px;border-bottom:1px solid #cbd5e1;white-space:nowrap">'+money(r.metrics[key])+'</td>').join("")+'</tr>').join("")+'</tbody></table></div><p>세 정책은 각각 별도로 적용한 예시입니다. 실제 신청 조건은 공식 공고에서 확인해 주세요.</p><button data-demo-close style="padding:12px;margin-top:16px">입력 화면으로 돌아가기 · 다시 계산</button></div>';
    const scenarioSection = '<section style="margin:24px 0;padding:16px;border:1px solid #cbd5e1"><h2>1. 하방·기준·회복의 13주 현금 비교</h2><p>시연용으로 구성한 매출 경로입니다. 범위를 선택하면 아래 정책 그래프와 13주 현금 금액도 같은 기준으로 바뀝니다.</p><div style="display:flex;gap:12px;flex-wrap:wrap">'+activeData.scenarios.map((item,index)=>'<button data-demo-scenario="'+index+'" aria-pressed="'+(index===activeScenario)+'" style="padding:12px;border:2px solid '+colors[index]+';background:'+(index===activeScenario?'#e2e8f0':'white')+'">'+escape(item.label)+' · 13주 '+money(item.cash[12])+'</button>').join("")+'</div>'+chart(activeData.scenarios,activeScenario,"가상 예시 하방 기준 회복의 13주 현금 그래프")+'</section>';
    panel.innerHTML = panel.innerHTML.replace('<div style="display:flex;gap:8px;flex-wrap:wrap">', scenarioSection+'<div style="display:flex;gap:8px;flex-wrap:wrap">');
    panel.querySelectorAll("[data-demo-scenario]").forEach(button => button.onclick = () => {activeScenario=Number(button.dataset.demoScenario);render();});
    panel.querySelectorAll("[data-demo-row]").forEach(button => button.onclick = () => {active=Number(button.dataset.demoRow);render();});
    panel.querySelector("[data-demo-close]").onclick = () => {panel.remove();};
  }
  async function open() {
    if (loading) return loading;
    loading = (async () => {
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 3000);
        try {
          const response = await fetch("/static/fallback-example.json", {signal:controller.signal});
          if (!response.ok) throw new Error("snapshot unavailable");
          const data = await response.json();
          if (!valid(data)) throw new Error("invalid snapshot");
          activeData = data; level = 2;
        } finally { clearTimeout(timer); }
      } catch (_) {activeData = fixedExample();level = 3;}
      active = 0;
      activeScenario = 1;
      render();
      return true;
    })();
    try {return await loading;} finally {loading = null;}
  }
  window.openDemoFallback = open;
  window.demoFallbackValidation = {valid, fixedExample};
  document.addEventListener("DOMContentLoaded", () => {
    const button = document.createElement("button");
    button.textContent = "시연이 멈췄나요? 가상 예시로 계속";
    button.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:9999;padding:12px;border:1px solid #b77900;border-radius:8px;background:#fff0c2;color:#172033;cursor:pointer";
    button.addEventListener("click", open);
    document.body.append(button);
  });
})();
