const V5_SESSION_KEY = "buttimaiv5:session:v1";
const v4State = {
  currentPolicy: null,
  noticeFieldConfirmations: new Set(),
  plan: null,
  noticeExtractions: new Map(),
  noticeBatchSize: 0,
};

const v5ReviewLensLabels = {
  cash_runway: "이번 달 현금이 버틸지 확인",
  debt_relief: "대출 상환 부담 줄이기",
  fixed_cost: "고정비를 줄일 방법 찾기",
  policy_choice: "지원금과 융자 중 무엇을 볼지 비교",
  unsure: "무엇부터 확인할지 모르겠음",
};

const v5SignalLabels = {
  cash_gap_28d: "28일 필요현금 부족",
  negative_cash_within_13w: "13주 안의 현금 부족",
  sales_direction: "최근 매출 방향",
  high_interest_debt_present: "대환 검토가 필요한 금리",
  fixed_cost_pressure: "고정비 부담",
  new_debt_sensitivity: "새로 생기는 부채",
  policy_route_uncertainty: "답변이 필요한 정책 조건",
};

const v4FinanceFields = [
  "opening-cash", "monthly-rent", "monthly-labor", "monthly-purchase",
  "monthly-other-fixed", "loan-balance", "loan-rate", "loan-term",
  "revenue-timing", "expense-timing", "debt-timing",
];

function syncV5ReviewLensContext() {
  const signalByLens = { cash_runway: "cash_concern", debt_relief: "debt_concern", fixed_cost: "fixed_cost_concern" };
  const signal = signalByLens[state.reviewLens];
  state.situationContext = state.reviewLens ? {
    original_text: `해결 목적: ${v5ReviewLensLabels[state.reviewLens]}`,
    confirmed_area_code: state.selectedArea?.code || null,
    confirmed_industry_code: byId("industry-select").value || null,
    signals: signal ? [signal] : [],
    confirmed_goal: null,
  } : null;
  state.scenarioCacheKey = "";
  document.querySelectorAll("[data-v5-review-lens]").forEach((button) => {
    const active = state.reviewLens === button.dataset.v5ReviewLens;
    button.classList.toggle("is-selected", active);
    button.setAttribute("aria-checked", String(active));
    button.tabIndex = active || !state.reviewLens ? 0 : -1;
  });
  byId("v5-lens-status").textContent = state.reviewLens
    ? `${v5ReviewLensLabels[state.reviewLens]} 선택 · 자격, 금액, 효과와 기존 순위는 바뀌지 않습니다.`
    : "목적 한 개를 선택해야 다음 단계로 진행할 수 있습니다.";
  const guidance = {
    cash_runway: "현재 현금과 앞으로 28일 필수지출을 먼저 확인합니다.",
    debt_relief: "대출 잔액·금리·남은 기간을 먼저 확인합니다.",
    fixed_cost: "임대료·인건비·매입비를 먼저 확인합니다.",
    policy_choice: "지원 방식과 신규 부채 차이를 함께 비교합니다.",
    unsure: "진단 결과를 본 뒤 검토 기준을 제안합니다.",
  };
  if (state.reviewLens) {
    byId("v3-finance-context").hidden = false;
    byId("v3-finance-context-items").innerHTML = `<li>${escapeHtml(guidance[state.reviewLens])}</li>`;
  } else {
    byId("v3-finance-context").hidden = true;
  }
  saveV4Session();
}

function setV5ReviewLens(reviewLens, source = "user") {
  if (!Object.hasOwn(v5ReviewLensLabels, reviewLens)) return;
  state.reviewLens = reviewLens;
  state.confirmedReviewLens = null;
  state.reviewLensSource = source;
  syncV5ReviewLensContext();
}

window.renderV5ReviewPlan = function renderV5ReviewPlan() {
  const section = byId("v5-review-plan");
  const plan = state.reviewPlan;
  if (!section || !plan) return;
  section.hidden = false;
  const detected = (state.data?.detected_signals || []).filter((item) => item.status === "present");
  const detectedText = detected.length
    ? detected.map((item) => escapeHtml(item.display_text || v5SignalLabels[item.key] || "추가 재무 신호")).join(" · ")
    : "뚜렷한 우선 신호 없음";
  byId("v5-review-plan-content").innerHTML = `<p class="v5-review-plan-summary">${escapeHtml(plan.summary)}</p><dl><div><dt>검토 기준</dt><dd>${escapeHtml(plan.goal_label)}</dd></div><div><dt>확인한 재무 상태</dt><dd>${detectedText}</dd></div><div><dt>먼저 볼 효과</dt><dd>${escapeHtml(plan.first_effect)}</dd></div></dl>`;
  const actions = byId("v5-review-plan-actions");
  if (plan.requires_confirmation) {
    const suggestion = plan.suggested_review_lens;
    actions.hidden = false;
    actions.innerHTML = `<p><strong>${escapeHtml(v5ReviewLensLabels[suggestion])}</strong> 기준을 제안합니다. 자동으로 확정하지 않습니다.</p><button type="button" class="primary" data-v5-confirm-lens="${escapeHtml(suggestion)}" data-v5-confirm-suggestion="true">이 기준으로 검토</button><button type="button" class="secondary" data-v5-show-lens-options>다른 기준 선택</button>`;
  } else {
    actions.hidden = true;
    actions.innerHTML = "";
  }
};

function v4MoneyWarning(id, value, averageRevenue) {
  if (value == null) return "필수 입력 누락";
  if (value < 0) return "계산 불가";
  if (id === "loan-rate" && value > 30) return "확인 권장";
  if (["monthly-rent", "monthly-labor", "monthly-purchase", "monthly-other-fixed"].includes(id) && averageRevenue > 0 && value > averageRevenue * 2) return "확인 권장";
  return "확인됨";
}

function renderV4FieldMessages() {
  const fields = ["opening-cash", "monthly-rent", "monthly-labor", "monthly-purchase", "monthly-other-fixed", "loan-balance", "loan-rate", "loan-term"];
  fields.forEach((id) => {
    const input = byId(id);
    if (!input) return;
    input.closest("label")?.querySelector(".v4-field-message")?.remove();
    let message = "";
    let kind = "";
    if (!input.disabled && input.value === "" && (["loan-rate", "loan-term"].includes(id) ? Number(byId("loan-balance").value || 0) > 0 : true)) {
      message = "필수 값을 입력해 주세요."; kind = "error";
    } else if (!input.disabled && Number(input.value) < 0) {
      message = "0 이상의 값을 입력해 주세요."; kind = "error";
    } else if (id === "loan-rate" && Number(input.value) > 30) {
      message = "일반적인 입력 범위보다 높습니다. 계산은 가능하지만 확인을 권장합니다."; kind = "warning";
    }
    input.setAttribute("aria-invalid", String(kind === "error"));
    if (message) input.closest("label")?.insertAdjacentHTML("beforeend", `<small class="v4-field-message is-${kind}">${escapeHtml(message)}</small>`);
  });
  document.querySelectorAll(".revenue-input").forEach((input) => {
    input.closest("label")?.querySelector(".v4-field-message")?.remove();
    if (input.value !== "" && Number(input.value) >= 0) { input.setAttribute("aria-invalid", "false"); return; }
    input.setAttribute("aria-invalid", "true");
    input.closest("label")?.insertAdjacentHTML("beforeend", '<small class="v4-field-message is-error">0 이상의 월매출을 입력해 주세요.</small>');
  });
}

window.openV4InputLedger = function openV4InputLedger() {
  renderV4FieldMessages();
  try { validateBusiness(); validateFinance(); } catch (error) { toast(error.message); return; }
  syncV5ReviewLensContext();
  const revenueInputs = [...document.querySelectorAll(".revenue-input")];
  const revenueValuesInTenThousandWon = revenueInputs.map((input) => Number(input.value));
  const averageRevenue = revenueValuesInTenThousandWon.reduce((sum, value) => sum + value, 0) / revenueValuesInTenThousandWon.length;
  const monthlyRevenueRows = revenueInputs.map((input) => ({
    month: input.closest("label")?.childNodes[0]?.textContent.trim() || "월매출",
    amount: `${Number(input.value).toLocaleString("ko-KR")}만원`,
  }));
  const rows = [
    ["사업장", `${state.selectedArea.district} ${state.selectedArea.name}`, "사용자 선택", "확인됨"],
    ["업종", state.industries.find((item) => item.code === byId("industry-select").value)?.name || "", "사용자 선택", "확인됨"],
    ["주된 해결 목적", v5ReviewLensLabels[state.reviewLens] || "선택 없음", "사용자 선택", "확인됨"],
    ["최근 월매출", monthlyRevenueRows, "사용자 입력", "확인됨"],
    ["현재 보유 현금", `${byId("opening-cash").value}만원`, "사용자 입력", v4MoneyWarning("opening-cash", Number(byId("opening-cash").value), averageRevenue)],
    ["월 필수지출", `${["monthly-rent", "monthly-labor", "monthly-purchase", "monthly-other-fixed"].reduce((sum, id) => sum + Number(byId(id).value || 0), 0).toLocaleString("ko-KR")}만원`, "사용자 입력", "확인됨"],
    ["대출", byId("v4-no-loan").checked ? "없음" : `잔액 ${byId("loan-balance").value}만원 · 연 ${byId("loan-rate").value}% · ${byId("loan-term").value}개월`, "사용자 입력", v4MoneyWarning("loan-rate", Number(byId("loan-rate").value), averageRevenue)],
    ["시기 가정", `매출 ${byId("revenue-timing").selectedOptions[0].text} · 비용 ${byId("expense-timing").selectedOptions[0].text} · 상환 ${byId("debt-timing").selectedOptions[0].text}`, "계산 가정", "확인됨"],
  ];
  byId("v4-ledger-content").innerHTML = `<div class="v4-ledger-table">${rows.map(([label, value, source, status]) => {
    const valueHtml = Array.isArray(value)
      ? `<dl class="v4-monthly-ledger">${value.map((item) => `<div><dt>${escapeHtml(item.month)}</dt><dd>${escapeHtml(item.amount)}</dd></div>`).join("")}</dl>`
      : `<span>${escapeHtml(value)}</span>`;
    return `<div class="${status === "확인 권장" ? "needs-review" : ""}"><strong>${escapeHtml(label)}</strong>${valueHtml}<small>${escapeHtml(source)} · ${escapeHtml(status)}</small></div>`;
  }).join("")}</div>`;
  const dialog = byId("v4-input-ledger");
  if (typeof dialog.showModal === "function") dialog.showModal();
};

function toggleNoLoan() {
  const checked = byId("v4-no-loan").checked;
  ["loan-balance", "loan-rate", "loan-term", "debt-timing"].forEach((id) => { byId(id).disabled = checked; });
  if (checked) {
    byId("loan-balance").value = 0;
    byId("loan-rate").value = 0;
    byId("loan-term").value = 36;
  }
  updateSummary();
  saveV4Session();
}

async function loadV4ApplicationPlan(policyId = v4State.currentPolicy?.policy_id) {
  const candidate = (state.data?.policy_discovery?.candidates || []).find((item) => item.policy_id === policyId) || v4State.currentPolicy;
  if (!candidate) return;
  v4State.currentPolicy = candidate;
  const readiness = candidate.application_readiness || {};
  v4State.plan = {
    policy: {
      policy_id: candidate.policy_id,
      policy_name: candidate.policy_name,
      policy_version: candidate.policy_version || null,
      official_url: candidate.official_url,
      readiness_status: readiness.status || candidate.eligibility_readiness || "공식 확인 필요",
    },
    notice: "AI가 저장 공고에서 정리한 항목을 직접 확인하세요. 이 확인은 자격 확정이나 승인 가능성을 뜻하지 않습니다.",
  };
  const extractionKey = v4NoticeExtractionKey(candidate);
  if (!v4State.noticeExtractions.has(extractionKey)) {
    v4State.noticeExtractions.set(extractionKey, { analysis_status: "loading" });
  }
  renderV4Preparation(); saveV4Session();
}

function v4NoticeExtractionKey(policy) {
  return `${policy.policy_id}:${policy.policy_version || "current"}`;
}

function v4NoticeFieldConfirmationKey(policy, extraction, fieldKey) {
  return `${v4NoticeExtractionKey(policy)}:${extraction?.source_digest || "unknown"}:${fieldKey}`;
}

function v4SelectedNoticeCandidates() {
  const selected = typeof policyFocusCandidates === "function" ? policyFocusCandidates() : [];
  const candidates = [...selected];
  if (v4State.currentPolicy && !candidates.some((item) => item.policy_id === v4State.currentPolicy.policy_id)) {
    candidates.push(v4State.currentPolicy);
  }
  return candidates.slice(0, 3);
}

async function loadV4NoticeExtractions() {
  const candidates = v4SelectedNoticeCandidates();
  if (!candidates.length) return;
  v4State.noticeBatchSize = candidates.length;
  const pending = candidates.filter((candidate) => {
    const extraction = v4State.noticeExtractions.get(v4NoticeExtractionKey(candidate));
    return !extraction || extraction.analysis_status !== "completed";
  });
  pending.forEach((candidate) => {
    v4State.noticeExtractions.set(v4NoticeExtractionKey(candidate), { analysis_status: "loading" });
  });
  renderV4Preparation();
  await Promise.all(pending.map(async (candidate) => {
    const extractionKey = v4NoticeExtractionKey(candidate);
    try {
      const extraction = await api("/api/v5/application/notice-extract", { method: "POST", body: JSON.stringify({
        policy_id: candidate.policy_id,
        policy_name: candidate.policy_name,
        policy_version: candidate.policy_version || null,
        official_url: candidate.official_url,
        force_refresh: false,
      }) });
      v4State.noticeExtractions.set(extractionKey, extraction);
    } catch (error) {
      console.error(error);
      v4State.noticeExtractions.set(extractionKey, {
        analysis_status: "unavailable",
        external_ai_used: false,
        fallback_reason: "request_failed",
        fields: [],
        notice: "AI 공고 분석을 완료하지 못했습니다. 공식 공고에서 필요한 값을 직접 확인해 주세요.",
      });
    }
    renderV4Preparation();
  }));
  renderV4Preparation();
}

function renderV4NoticeExtraction(plan) {
  const extraction = v4State.noticeExtractions.get(v4NoticeExtractionKey(plan.policy));
  if (!extraction || extraction.analysis_status === "loading") {
    return `<section class="v4-notice-ai is-loading" aria-live="polite" aria-busy="true"><div class="v5-notice-loading"><span class="v5-inline-spinner" aria-hidden="true"></span><div><span>AI가 공고를 확인하는 중</span><h3>신청에 필요한 내용을 정리하고 있습니다</h3><p>저장된 공고에서 신청 기간, 지원 조건과 필요 서류를 찾고 있습니다.</p></div></div></section>`;
  }
  if (extraction.analysis_status !== "completed") {
    return `<section class="v4-notice-ai is-unavailable"><span>AI 분석 불가</span><h3>공고 핵심정보를 자동으로 정리하지 못했습니다</h3><p>${escapeHtml(extraction.notice || "공식 공고에서 필요한 값을 직접 확인해 주세요.")}</p><a href="${safeUrl(plan.policy.official_url)}" target="_blank" rel="noreferrer">공식 공고에서 직접 확인</a></section>`;
  }
  const fields = (extraction.fields || []).map((field) => {
    if (field.status !== "found") {
      const failedValidation = field.validation_status === "evidence_validation_failed";
      return `<article class="v4-notice-field is-missing"><span>${escapeHtml(field.label)}</span><strong>${failedValidation ? "AI 추출값 확인 필요" : "공고에서 확인되지 않음"}</strong><p>${failedValidation ? "저장 공고 내용과 일치 여부를 자동 확인하지 못했습니다." : "AI가 저장 공고에서 이 값을 찾지 못했습니다."}</p><a href="${safeUrl(plan.policy.official_url)}" target="_blank" rel="noreferrer">공식 공고에서 직접 확인</a></article>`;
    }
    const value = field.value ? `<strong>${escapeHtml(field.value)}</strong>` : "";
    const items = field.items?.length ? `<ul>${field.items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : "";
    const confirmationKey = v4NoticeFieldConfirmationKey(plan.policy, extraction, field.key);
    const confirmed = v4State.noticeFieldConfirmations.has(confirmationKey);
    return `<article class="v4-notice-field is-found${confirmed ? " is-confirmed" : ""}"><span>${escapeHtml(field.label)}</span>${value}${items}<button type="button" class="secondary v4-field-confirm${confirmed ? " is-confirmed" : ""}" data-v4-confirm-notice-field="${escapeHtml(field.key)}">${confirmed ? "확인 완료" : "이 내용 확인"}</button></article>`;
  }).join("");
  const foundFields = (extraction.fields || []).filter((field) => field.status === "found");
  const confirmedCount = foundFields.filter((field) => v4State.noticeFieldConfirmations.has(v4NoticeFieldConfirmationKey(plan.policy, extraction, field.key))).length;
  const cacheLabel = extraction.cache_status === "fresh" ? "방금 다시 정리함" : "저장된 분석 결과 사용";
  return `<section class="v4-notice-ai"><div class="v4-notice-ai-heading"><div><span>AI 공고 분석</span><h3>저장 공고에서 정리한 신청 핵심정보</h3></div><div class="v4-notice-ai-meta"><small>공고 저장 기준일 ${escapeHtml(extraction.retrieved_at || "미확인")} · ${cacheLabel}</small><button type="button" class="secondary" data-v4-refresh-notice="${escapeHtml(plan.policy.policy_id)}">공고 다시 분석</button></div></div><p class="v4-notice-ai-guide">저장된 공고에서 찾은 핵심정보입니다. 공고에서 확인되지 않은 값은 채우지 않았습니다.</p><p class="v4-notice-confirm-summary"><strong>이 정책의 공고 항목 ${confirmedCount} / ${foundFields.length}개 확인</strong><span>정책 개수가 아니라, 선택한 정책 한 건에서 확인할 신청정보 개수입니다.</span></p><div class="v4-notice-field-grid">${fields}</div><p class="v4-evidence-warning">AI 추출값은 신청 편의를 위한 초안입니다. 현재 접수 여부·잔여 예산·최종 자격은 공식 공고와 신청기관에서 확인해야 합니다.</p></section>`;
}

function v5NoticeFieldCard(plan, extraction, field, isNext = false) {
  const confirmationKey = v4NoticeFieldConfirmationKey(plan.policy, extraction, field.key);
  const confirmed = v4State.noticeFieldConfirmations.has(confirmationKey);
  const failedValidation = field.validation_status === "evidence_validation_failed";
  const statusText = field.status === "found"
    ? "저장 공고에서 찾음"
    : failedValidation ? "원문 근거 검증 실패" : "공고에서 확인되지 않음";
  const value = field.value ? `<strong>${escapeHtml(field.value)}</strong>` : "";
  const items = field.items?.length ? `<ul>${field.items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : "";
  const missing = field.status !== "found"
    ? `<p>${failedValidation ? "추출값을 자동 확정하지 않았습니다." : "찾지 못한 값을 채우지 않았습니다."}</p><a href="${safeUrl(plan.policy.official_url)}" target="_blank" rel="noreferrer">공식 공고에서 직접 확인</a>`
    : "";
  return `<article class="v5-notice-field${isNext ? " is-next" : ""}${confirmed ? " is-confirmed" : ""}"><span>${escapeHtml(field.label)}</span><small>${escapeHtml(statusText)}</small>${value}${items}${missing}<button type="button" class="secondary v4-field-confirm${confirmed ? " is-confirmed" : ""}" data-v4-confirm-notice-field="${escapeHtml(field.key)}">${confirmed ? "확인 완료" : field.status === "found" ? "이 내용 확인" : "공식 공고에서 확인함"}</button></article>`;
}

function renderV5NoticeExtraction(plan) {
  const extraction = v4State.noticeExtractions.get(v4NoticeExtractionKey(plan.policy));
  if (!extraction || extraction.analysis_status !== "completed") return renderV4NoticeExtraction(plan);
  const defaultOrder = ["application_period", "financing_terms", "application_path", "required_documents", "contact", "publication_date"];
  const priority = (state.noticeFieldPriority || []).length
    ? [...state.noticeFieldPriority].sort((left, right) => left.position - right.position).map((item) => item.key)
    : defaultOrder;
  const byKey = new Map((extraction.fields || []).map((field) => [field.key, field]));
  const orderedFields = priority.map((key) => byKey.get(key)).filter(Boolean);
  const isConfirmed = (field) => v4State.noticeFieldConfirmations.has(v4NoticeFieldConfirmationKey(plan.policy, extraction, field.key));
  const nextField = orderedFields.find((field) => !isConfirmed(field)) || null;
  const remaining = orderedFields.filter((field) => field !== nextField);
  const confirmedCount = orderedFields.filter(isConfirmed).length;
  const cacheLabel = extraction.cache_status === "fresh" ? "방금 다시 정리함" : "저장된 분석 결과 사용";
  const nextHtml = nextField
    ? `<section class="v5-next-notice" aria-labelledby="v5-next-notice-title"><p class="eyebrow">다음 확인 1개</p><h3 id="v5-next-notice-title" tabindex="-1">${escapeHtml(nextField.label)}부터 확인하세요</h3>${v5NoticeFieldCard(plan, extraction, nextField, true)}</section>`
    : `<section class="v5-next-notice is-complete"><p class="eyebrow">이 화면의 확인 완료</p><h3 id="v5-next-notice-title" tabindex="-1">여기서 확인할 내용은 모두 끝났습니다</h3><p>앞에서 확인한 자격조건과 공고 핵심정보를 모두 읽었습니다. 신청이 완료된 것은 아닙니다.</p><ol><li>공식 공고에서 현재 접수 여부와 잔여 예산 확인</li><li>신청기관에서 최종 자격과 확정 지원조건 확인</li><li>공식 신청 경로에서 접수 준비</li></ol><div class="v5-completion-actions"><a class="primary" href="${safeUrl(plan.policy.official_url)}" target="_blank" rel="noreferrer">현재 접수 여부 확인</a><button type="button" class="secondary" data-v5-return-comparison>다른 정책과 다시 비교</button></div></section>`;
  const remainingHtml = remaining.length
    ? `<details class="v5-remaining-notice"><summary>남은 확인 ${remaining.filter((field) => !isConfirmed(field)).length}개와 확인한 항목 보기</summary><div class="v4-notice-field-grid">${remaining.map((field) => v5NoticeFieldCard(plan, extraction, field)).join("")}</div></details>`
    : "";
  return `<section class="v4-notice-ai v5-notice-ai"><div class="v4-notice-ai-heading"><div><span>AI 공고 분석</span><h3>저장 공고에서 정리한 신청 핵심정보</h3></div><div class="v4-notice-ai-meta"><small>공고 저장 기준일 ${escapeHtml(extraction.retrieved_at || "미확인")} · ${cacheLabel}</small><button type="button" class="secondary" data-v4-refresh-notice="${escapeHtml(plan.policy.policy_id)}">공고 다시 분석</button></div></div><p class="v4-notice-confirm-summary"><strong>이 정책의 공고 항목 ${confirmedCount} / ${orderedFields.length}개 확인</strong><span>${nextField ? "정책 개수가 아닙니다. 한 항목을 확인하면 다음 신청정보가 올라옵니다." : "선택한 정책 한 건에서 확인할 신청정보를 모두 읽었습니다."}</span></p>${nextHtml}${remainingHtml}<p class="v4-evidence-warning">저장 공고 기준의 구조화 결과입니다. 현재 접수 여부·잔여 예산·최종 자격은 공식 공고와 신청기관에서 확인해야 합니다.</p></section>`;
}

async function refreshV4NoticeExtraction(policyId) {
  const candidate = v4SelectedNoticeCandidates().find((item) => item.policy_id === policyId) || v4State.currentPolicy;
  if (!candidate) return;
  const extractionKey = v4NoticeExtractionKey(candidate);
  v4State.noticeExtractions.set(extractionKey, { analysis_status: "loading" });
  renderV4Preparation();
  try {
    const extraction = await api("/api/v5/application/notice-extract", { method: "POST", body: JSON.stringify({
      policy_id: candidate.policy_id,
      policy_name: candidate.policy_name,
      policy_version: candidate.policy_version || null,
      official_url: candidate.official_url,
      force_refresh: true,
    }) });
    v4State.noticeExtractions.set(extractionKey, extraction);
  } catch (error) {
    console.error(error);
    v4State.noticeExtractions.set(extractionKey, { analysis_status: "unavailable", fields: [], notice: "공고를 다시 분석하지 못했습니다. 잠시 후 다시 시도해 주세요." });
  }
  renderV4Preparation();
}

function renderV4Preparation() {
  const plan = v4State.plan;
  if (!plan) return;
  byId("v4-preparation-empty").hidden = true;
  byId("v4-preparation-result").hidden = false;
  byId("v4-policy-name").textContent = plan.policy.policy_name;
  byId("v4-readiness-status").textContent = plan.policy.readiness_status;
  byId("v4-official-link").href = plan.policy.official_url;
  byId("v4-preparation-notice").textContent = plan.notice;
  renderV4PolicyConditions(v4State.currentPolicy);
  const chatPolicy = byId("qa-policy");
  if (chatPolicy && [...chatPolicy.options].some((option) => option.value === plan.policy.policy_id)) chatPolicy.value = plan.policy.policy_id;
  byId("qa-policy-scope").textContent = `현재 상담 정책: ${plan.policy.policy_name}`;
  byId("v4-notice-review").innerHTML = renderV5NoticeExtraction(plan);
}

function renderV5PolicyAnswerControl(question, policyId) {
  const current = state.eligibilityAnswers[question.field] ?? "unknown";
  if (["tri_state", "select"].includes(question.input_type)) {
    const options = (question.options || []).map((option) => `<button type="button" class="question-choice ${String(option.value) === String(current) ? "is-selected" : ""}" data-v5-policy-answer="${escapeHtml(question.field)}" data-v5-policy-answer-value="${escapeHtml(option.value)}" data-policy-id="${escapeHtml(policyId)}" aria-pressed="${String(option.value) === String(current)}">${escapeHtml(option.label)}</button>`).join("");
    return `<div class="question-choice-grid ${question.input_type === "tri_state" ? "is-three-way" : ""}" role="group" aria-label="${escapeHtml(question.label)} 선택">${options}</div>`;
  }
  const type = question.input_type === "number" ? "number" : "date";
  const attributes = type === "number" ? 'min="0" step="1" inputmode="numeric"' : "";
  const value = current === "unknown" ? "" : current;
  return `<div class="question-value-entry"><input type="${type}" ${attributes} data-v5-policy-answer-entry="${escapeHtml(question.field)}" value="${escapeHtml(value)}"><button type="button" class="secondary" data-v5-policy-answer-unknown="${escapeHtml(question.field)}" data-policy-id="${escapeHtml(policyId)}">모름</button><button type="button" class="primary" data-v5-policy-answer-apply="${escapeHtml(question.field)}" data-policy-id="${escapeHtml(policyId)}">반영</button></div>`;
}

function renderV4PolicyConditions(candidate) {
  const container = byId("v4-policy-condition-list");
  if (!container || !candidate) return;
  const readiness = candidate.application_readiness || {};
  const blockers = readiness.blocking_details || [];
  const questions = candidate.preparation_questions || [];
  questions.forEach((question) => { state.questionCatalog[question.field] = question; });
  const choiceHtml = questions.length
    ? `<section class="v5-policy-answer-panel"><h3>내 조건 선택</h3><p>이 정책에 해당하는 값을 모두 선택하세요. 선택할 때마다 결과를 다시 계산합니다.</p><div class="v5-policy-answer-list">${questions.map((question) => `<article class="v5-policy-answer-card"><strong>${escapeHtml(question.label)}</strong>${renderV5PolicyAnswerControl(question, candidate.policy_id)}</article>`).join("")}</div></section>`
    : '<section class="v5-policy-answer-panel is-empty"><h3>화면에서 선택할 조건 없음</h3><p>이 정책은 현재 화면에서 추가로 입력할 자격조건이 없습니다.</p></section>';
  const blockerHtml = blockers.length
    ? `<div class="v4-condition-group is-blocked"><h3>현재 선택으로 지원이 어려운 이유</h3>${blockers.map((detail) => `<article><span>${detail.remediation_type === "structural" ? "현재 조건에서 제외" : "보완 가능"}</span><h4>${escapeHtml(humanizeText(detail.condition))}</h4><p><strong>다음 확인:</strong> ${escapeHtml(humanizeText(detail.action || "공식기관에서 조건을 확인하세요."))}</p></article>`).join("")}</div>`
    : '<div class="v4-condition-group is-clear"><h3>현재 선택에서 확인된 제외조건 없음</h3><p>화면에서 선택한 값만 기준으로 확인한 결과입니다. 공식 심사 결과가 확정된 것은 아닙니다.</p></div>';
  const officialChecks = readiness.official_checks || [];
  const officialHtml = officialChecks.length
    ? `<div class="v4-condition-group"><h3>기관에서 확인할 항목</h3><ul>${officialChecks.map((item) => `<li>${escapeHtml(humanizeText(item))}</li>`).join("")}</ul></div>`
    : "";
  container.innerHTML = `${choiceHtml}${blockerHtml}${officialHtml}`;
}

async function applyV5PreparationAnswer(policyId, field, value) {
  const previous = state.eligibilityAnswers[field];
  state.eligibilityAnswers[field] = value || "unknown";
  state.scenarioCacheKey = "";
  state.actionBrief = null;
  showLoading("선택한 답변으로 정책 조건과 그래프를 다시 계산하고 있습니다.");
  try {
    const success = await runComparison("preparation", false, false);
    if (!success) {
      if (previous === undefined) delete state.eligibilityAnswers[field];
      else state.eligibilityAnswers[field] = previous;
      state.scenarioCacheKey = "";
      return;
    }
    await loadV4ApplicationPlan(policyId);
    showStep("preparation");
    saveV4Session();
    window.setTimeout(() => document.querySelector(`[data-v5-policy-answer="${CSS.escape(field)}"][aria-pressed="true"], [data-v5-policy-answer-entry="${CSS.escape(field)}"]`)?.focus({ preventScroll: true }), 0);
  } finally {
    hideLoading();
  }
}

function saveV4Session() {
  try {
    const finance = Object.fromEntries(v4FinanceFields.map((id) => [id, byId(id)?.value ?? ""]));
    finance.revenues = [...document.querySelectorAll(".revenue-input")].map((node) => node.value);
    sessionStorage.setItem(V5_SESSION_KEY, JSON.stringify({
      reviewLens: state.reviewLens,
      confirmedReviewLens: state.confirmedReviewLens,
      reviewLensSource: state.reviewLensSource,
      questionTraces: state.questionTraces,
      askedFields: state.v3AskedFields,
      questionRound: state.questionBatchRound,
      focusedPolicyId: state.focusedPolicyId,
      scenario: state.scenario,
      whatIf: { pending: state.pendingWhatIf, undo: state.whatIfUndo },
      finance,
      noLoan: byId("v4-no-loan")?.checked || false,
      areaCode: state.selectedArea?.code || null,
      industryCode: byId("industry-select")?.value || null,
      eligibilityAnswers: state.eligibilityAnswers,
      selectedPolicyIds: [...state.selectedPolicyIds],
      application: v4State.currentPolicy ? { currentPolicy: v4State.currentPolicy, noticeFieldConfirmations: [...v4State.noticeFieldConfirmations] } : null,
    }));
  } catch { /* Session persistence is best-effort and never blocks calculation. */ }
}

function restoreV4Session() {
  let snapshot;
  try { snapshot = JSON.parse(sessionStorage.getItem(V5_SESSION_KEY) || "null"); } catch { return; }
  if (!snapshot) return;
  state.reviewLens = Object.hasOwn(v5ReviewLensLabels, snapshot.reviewLens) ? snapshot.reviewLens : "";
  state.confirmedReviewLens = snapshot.confirmedReviewLens || null;
  state.reviewLensSource = snapshot.reviewLensSource || "user";
  state.questionTraces = snapshot.questionTraces || [];
  state.v3AskedFields = snapshot.askedFields || [];
  state.questionBatchRound = Math.min(2, Number(snapshot.questionRound || 0));
  state.focusedPolicyId = snapshot.focusedPolicyId || "";
  state.scenario = ["downside", "central", "recovery"].includes(snapshot.scenario) ? snapshot.scenario : "central";
  state.pendingWhatIf = snapshot.whatIf?.pending || null;
  state.whatIfUndo = snapshot.whatIf?.undo || null;
  Object.entries(snapshot.finance || {}).forEach(([id, value]) => { if (id !== "revenues" && byId(id)) byId(id).value = value; });
  if (Array.isArray(snapshot.finance?.revenues) && snapshot.finance.revenues.length >= 3) {
    state.revenueMonths = snapshot.finance.revenues.length;
    renderRevenueMonths(snapshot.finance.revenues);
  }
  byId("v4-no-loan").checked = Boolean(snapshot.noLoan);
  state.eligibilityAnswers = snapshot.eligibilityAnswers || {};
  state.selectedPolicyIds = new Set(snapshot.selectedPolicyIds || []);
  if (snapshot.application) {
    v4State.currentPolicy = snapshot.application.currentPolicy;
    v4State.noticeFieldConfirmations = new Set(snapshot.application.noticeFieldConfirmations || []);
    window.setTimeout(async () => {
      try {
        await loadV4ApplicationPlan();
        await loadV4NoticeExtractions();
      } catch { /* Restoring an old tab must not block the rest of the page. */ }
    }, 0);
  }
  toggleNoLoan(); syncV5ReviewLensContext(); updateSummary();
  let attempts = 0;
  const restoreCatalogSelection = window.setInterval(() => {
    attempts += 1;
    if (snapshot.areaCode && state.areaPoints.some((item) => item.code === snapshot.areaCode)) selectArea(snapshot.areaCode, false, false, true, false);
    if (snapshot.industryCode && state.industries.some((item) => item.code === snapshot.industryCode)) {
      const major = industryMajor(snapshot.industryCode);
      byId("industry-major-select").value = major;
      populateIndustries(major, snapshot.industryCode);
    }
    if (attempts >= 20 || ((!snapshot.areaCode || state.selectedArea) && (!snapshot.industryCode || byId("industry-select").value))) window.clearInterval(restoreCatalogSelection);
  }, 150);
}

document.addEventListener("click", async (event) => {
  const policyAnswer = event.target.closest("[data-v5-policy-answer]");
  if (policyAnswer) {
    await applyV5PreparationAnswer(policyAnswer.dataset.policyId, policyAnswer.dataset.v5PolicyAnswer, policyAnswer.dataset.v5PolicyAnswerValue);
    return;
  }
  const policyAnswerUnknown = event.target.closest("[data-v5-policy-answer-unknown]");
  if (policyAnswerUnknown) {
    await applyV5PreparationAnswer(policyAnswerUnknown.dataset.policyId, policyAnswerUnknown.dataset.v5PolicyAnswerUnknown, "unknown");
    return;
  }
  const policyAnswerApply = event.target.closest("[data-v5-policy-answer-apply]");
  if (policyAnswerApply) {
    const field = policyAnswerApply.dataset.v5PolicyAnswerApply;
    const input = policyAnswerApply.closest(".question-value-entry")?.querySelector(`[data-v5-policy-answer-entry="${CSS.escape(field)}"]`);
    if (!input?.value) {
      toast("값을 입력하거나 모름을 선택해 주세요.");
      return;
    }
    await applyV5PreparationAnswer(policyAnswerApply.dataset.policyId, field, input.value);
    return;
  }
  const reviewLens = event.target.closest("[data-v5-review-lens]");
  if (reviewLens) {
    setV5ReviewLens(reviewLens.dataset.v5ReviewLens, state.data ? "changed" : "user");
  }
  const showLensOptions = event.target.closest("[data-v5-show-lens-options], #v5-change-review-lens");
  if (showLensOptions) {
    const actions = byId("v5-review-plan-actions");
    actions.hidden = false;
    actions.innerHTML = `<p>다른 기준을 선택하면 먼저 보여줄 정책과 재무 숫자가 바뀝니다.</p><div class="v5-plan-lens-options">${["cash_runway", "debt_relief", "fixed_cost", "policy_choice"].map((key) => `<button type="button" class="secondary" data-v5-confirm-lens="${key}">${escapeHtml(v5ReviewLensLabels[key])}</button>`).join("")}</div>`;
  }
  const confirmLens = event.target.closest("[data-v5-confirm-lens]");
  if (confirmLens) {
    const lens = confirmLens.dataset.v5ConfirmLens;
    if (confirmLens.dataset.v5ConfirmSuggestion === "true" && state.reviewLens === "unsure") {
      state.confirmedReviewLens = lens;
      state.reviewLensSource = "confirmed_suggestion";
      syncV5ReviewLensContext();
    } else {
      setV5ReviewLens(lens, "changed");
    }
    state.questionWizardMode = "full";
    state.questionWizardOrder = [];
    state.questionWizardComplete = false;
    state.questionWizardResultsVisible = false;
    if (await runComparison("diagnosis", false)) {
      byId("v5-review-plan").focus({ preventScroll: true });
      byId("v5-review-plan").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
  const start = event.target.closest("[data-v4-start-application]");
  if (start) {
    start.disabled = true;
    try {
      await loadV4ApplicationPlan(start.dataset.v4StartApplication);
      showStep("preparation");
      await loadV4NoticeExtractions();
    } catch (error) {
      console.error(error);
      toast("신청 준비 내용을 불러오지 못했습니다. 화면을 새로고침한 뒤 다시 시도해 주세요.");
    } finally {
      start.disabled = false;
    }
  }
  const confirmField = event.target.closest("[data-v4-confirm-notice-field]");
  if (confirmField) {
    const extraction = v4State.noticeExtractions.get(v4NoticeExtractionKey(v4State.plan.policy));
    const key = v4NoticeFieldConfirmationKey(v4State.plan.policy, extraction, confirmField.dataset.v4ConfirmNoticeField);
    if (v4State.noticeFieldConfirmations.has(key)) v4State.noticeFieldConfirmations.delete(key);
    else v4State.noticeFieldConfirmations.add(key);
    saveV4Session();
    renderV4Preparation();
    window.setTimeout(() => byId("v5-next-notice-title")?.focus({ preventScroll: true }), 0);
  }
  const refreshNotice = event.target.closest("[data-v4-refresh-notice]");
  if (refreshNotice) await refreshV4NoticeExtraction(refreshNotice.dataset.v4RefreshNotice);
  const returnComparison = event.target.closest("[data-v5-return-comparison]");
  if (returnComparison) showStep("decision");
});

document.addEventListener("change", () => window.queueMicrotask(saveV4Session));
document.addEventListener("input", () => window.queueMicrotask(saveV4Session));
document.addEventListener("focusout", (event) => {
  if (event.target.matches(".revenue-input, #opening-cash, #monthly-rent, #monthly-labor, #monthly-purchase, #monthly-other-fixed, #loan-balance, #loan-rate, #loan-term")) renderV4FieldMessages();
});
document.addEventListener("keydown", (event) => {
  const current = event.target.closest("[data-v5-review-lens]");
  if (!current || !["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(event.key)) return;
  event.preventDefault();
  const buttons = [...document.querySelectorAll("[data-v5-review-lens]")];
  const direction = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1;
  const next = buttons[(buttons.indexOf(current) + direction + buttons.length) % buttons.length];
  setV5ReviewLens(next.dataset.v5ReviewLens, state.data ? "changed" : "user");
  next.focus();
});
byId("v4-no-loan").addEventListener("change", toggleNoLoan);
byId("v4-ledger-close").addEventListener("click", () => byId("v4-input-ledger").close());
byId("v4-ledger-edit").addEventListener("click", () => byId("v4-input-ledger").close());
byId("v4-ledger-confirm").addEventListener("click", () => { byId("v4-input-ledger").close(); saveV4Session(); runComparison("diagnosis"); });
if (new URLSearchParams(window.location.search).get("demo") === "1") byId("presentation-presets").hidden = false;
restoreV4Session();
