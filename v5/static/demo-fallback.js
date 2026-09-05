/* Data-only fallback: the existing application owns all screens and graphs. */
(() => {
  "use strict";
  const labels = ["무대응", "비차입 지원 예시", "대환대출 예시", "신규 정책자금 예시"];
  const scenarioLabels = ["하방", "기준", "회복"];
  const scenarioIds = ["downside", "central", "recovery"];
  const policyIds = ["POL_SEOUL_CRISIS_TRACK2_2026H2", "POL_SEMAS_REFINANCE_2026", "POL_SEOUL_FUND_2026"];
  const alternativeIds = ["no_action", "conditional_pol_seoul_crisis_track2_2026h2", "conditional_pol_semas_refinance_2026", "conditional_pol_seoul_fund_2026"];
  function testMode() {
    const query = new URLSearchParams(window.location.search);
    return query.get("demo") === "1" && ["1", "2"].includes(query.get("fallback")) ? query.get("fallback") : "";
  }
  function exampleScenarios(baseline) {
    return scenarioLabels.map((label, index) => ({label, cash: baseline.map((value, week) => value + (index - 1) * 180000 * (week + 1))}));
  }
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

  function buildResults(data, level) {
    if (!valid(data)) throw new Error("invalid fallback data");
    const weeks = cash => cash.map((closing_cash, index) => ({week: index + 1, opening_cash: index ? cash[index - 1] : 5000000, closing_cash}));
    const comparisons = data.scenarios.map((row, index) => ({
      scenario: scenarioIds[index], thirteen_week_percent: (index - 1) * 10, six_month_percent: (index - 1) * 10,
      weekly_13: weeks(row.cash), week13_ending_cash: row.cash[12],
      month6_ending_cash: (data.rows[0].metrics.month6_ending_cash ?? data.rows[0].cash[12] - 5000000) + (index - 1) * 4680000,
    }));
    return Object.fromEntries(scenarioIds.map((scenario, scenarioIndex) => {
      const alternatives = data.rows.map((row, index) => {
        const cash = row.cash.map((value, week) => value + data.scenarios[scenarioIndex].cash[week] - data.rows[0].cash[week]);
        return {
          alternative_id: alternativeIds[index], label: labels[index], ranking_eligible: false,
          items_to_confirm: ["가상 시연 사례 · 실제 지원 조건은 공식 확인 필요"], weekly_13: weeks(cash),
          metrics: {week13_ending_cash: cash[12], week13_minimum_cash: Math.min(...cash),
            month6_remaining_principal: row.metrics.month6_remaining_principal,
            maximum_monthly_debt_service: row.metrics.maximum_monthly_debt_service,
            total_interest_through_maturity: row.metrics.total_interest_through_maturity,
            month6_ending_cash: (row.metrics.month6_ending_cash ?? row.cash[12] - 5000000) + (scenarioIndex - 1) * 4680000,
            net_new_borrowing: row.metrics.net_new_borrowing ?? (index === 3 ? 15000000 : 0), confirmation_item_count: 1},
        };
      });
      const baseline = alternatives[0];
      return [scenario, {
        fallback: {level, sample: true, title: data.title, as_of: data.asOf},
        baseline_input: {opening_cash: 5000000},
        baseline_cashflow: {
          weekly_13: baseline.weekly_13,
          weekly_summary: {ending_cash: baseline.metrics.week13_ending_cash},
          monthly_summary: {ending_cash: baseline.metrics.month6_ending_cash},
          debt_summary: {remaining_principal_at_6_months: baseline.metrics.month6_remaining_principal,
            total_interest_through_maturity: baseline.metrics.total_interest_through_maturity},
        },
        safe_cash: {suggested_amount: 3000000}, intervention_results: alternatives,
        market_scenario_comparison: comparisons, comparison_result: {top_alternative_id: alternativeIds[1]},
        policy_discovery: {situation_labels: ["가상 시연 사례"], candidates: policyIds.map((policy_id, index) => ({
          policy_id, policy_name: labels[index + 1], match_reason: "자동 복구를 위한 고정 가상 사례입니다. 입력한 사업장의 적격성 판단이 아닙니다.",
          application_readiness: {status: "가상 예시 · 공식 확인 필요", conditional_graph_supported: true,
            conditional_graph_status: "available", next_actions: ["실제 조건은 공식 공고에서 확인해 주세요."]},
          preparation_questions: [],
        }))},
        v2: {conditional_policy_ids: policyIds}, review_plan: null, review_order: [],
        metric_order: ["week13_ending_cash", "net_new_borrowing", "maximum_monthly_debt_service"], execution_plan: [],
      }];
    }));
  }
  async function load() {
    let data, level = 2;
    try {
      if (testMode() === "2") throw new Error("Injected fallback snapshot failure");
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 3000);
      try {
        const response = await fetch("/static/fallback-example.json", {signal: controller.signal});
        if (!response.ok) throw new Error("snapshot unavailable");
        data = await response.json();
        if (!valid(data)) throw new Error("invalid snapshot");
      } finally { clearTimeout(timer); }
    } catch (_) { data = fixedExample(); level = 3; }
    return buildResults(data, level);
  }
  window.demoFallback = {load, testMode, buildResults, valid, fixedExample};
})();
