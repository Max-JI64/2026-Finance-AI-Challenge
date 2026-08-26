const V4_SESSION_KEY = "buttimaiv4:session:v3";
const v4State = {
  concerns: new Set(),
  currentPolicy: null,
  noticeFieldConfirmations: new Set(),
  plan: null,
  noticeExtractions: new Map(),
  noticeBatchSize: 0,
};

const v4FinanceFields = [
  "opening-cash", "monthly-rent", "monthly-labor", "monthly-purchase",
  "monthly-other-fixed", "loan-balance", "loan-rate", "loan-term",
  "revenue-timing", "expense-timing", "debt-timing",
];

function v4ConcernLabels() {
  const labels = {
    sales_decline: "매출 감소",
    cash_concern: "현금 부족",
    debt_concern: "대출 상환 부담",
    fixed_cost_concern: "고정비 부담",
    policy_search_concern: "정책 탐색 어려움",
  };
  return [...v4State.concerns].map((key) => labels[key]);
}

function syncV4ConcernContext() {
  const supported = [...v4State.concerns].filter((key) => key !== "policy_search_concern");
  state.situationContext = supported.length ? {
    original_text: `걱정 버튼: ${v4ConcernLabels().join(", ")}`,
    confirmed_area_code: state.selectedArea?.code || null,
    confirmed_industry_code: byId("industry-select").value || null,
    signals: supported,
    confirmed_goal: null,
  } : null;
  state.scenarioCacheKey = "";
  document.querySelectorAll("[data-v4-concern]").forEach((button) => {
    const active = v4State.concerns.has(button.dataset.v4Concern);
    button.classList.toggle("is-selected", active);
    button.setAttribute("aria-pressed", String(active));
  });
  byId("v4-concern-status").textContent = v4State.concerns.size
    ? `${v4ConcernLabels().join(" · ")} 선택 · 질문과 설명의 우선순위에만 사용`
    : "선택하지 않아도 진행할 수 있습니다.";
  const guidance = {
    sales_decline: "최근 월매출의 실제 흐름을 먼저 확인합니다.",
    cash_concern: "현재 현금과 앞으로 28일 필수지출을 먼저 확인합니다.",
    debt_concern: "대출 잔액·금리·남은 기간을 먼저 확인합니다.",
    fixed_cost_concern: "임대료·인건비·매입비를 먼저 확인합니다.",
    policy_search_concern: "재무 진단 뒤 관련 정책 후보를 함께 비교합니다.",
  };
  if (v4State.concerns.size) {
    byId("v3-finance-context").hidden = false;
    byId("v3-finance-context-items").innerHTML = [...v4State.concerns].map((key) => `<li>${escapeHtml(guidance[key])}</li>`).join("");
  } else {
    byId("v3-finance-context").hidden = true;
  }
  saveV4Session();
}

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
  syncV4ConcernContext();
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
    ["선택한 걱정", v4ConcernLabels().join(" · ") || "선택 없음", "사용자 선택", "확인됨"],
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
      const extraction = await api("/api/v4/application/notice-extract", { method: "POST", body: JSON.stringify({
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
    const batchSize = Math.max(1, v4State.noticeBatchSize || v4SelectedNoticeCandidates().length);
    return `<section class="v4-notice-ai is-loading" aria-live="polite"><span>공고 핵심정보 불러오는 중</span><h3>선택한 ${batchSize}개 정책의 저장된 분석 결과를 확인하고 있습니다</h3><p>공고가 바뀌었거나 저장된 결과가 없을 때만 Luna가 다시 분석합니다.</p></section>`;
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
  const cacheLabel = extraction.cache_status === "fresh" ? "새 분석 완료·영구 저장" : "저장된 분석 결과 사용";
  return `<section class="v4-notice-ai"><div class="v4-notice-ai-heading"><div><span>AI 공고 분석</span><h3>Luna가 추출한 신청 핵심정보</h3></div><div class="v4-notice-ai-meta"><small>공고 ${Number(extraction.analyzed_chunk_count || 0).toLocaleString("ko-KR")}개 조각 · 저장 기준일 ${escapeHtml(extraction.retrieved_at || "미확인")} · ${cacheLabel}</small><button type="button" class="secondary" data-v4-refresh-notice="${escapeHtml(plan.policy.policy_id)}">공고 다시 분석</button></div></div><p class="v4-notice-ai-guide">저장된 공고에서 찾은 핵심정보입니다. 공고에서 확인되지 않은 값은 채우지 않았습니다.</p><p class="v4-notice-confirm-summary"><strong>${confirmedCount} / ${foundFields.length}개 확인</strong><span>각 항목을 읽은 뒤 해당 카드에서 확인하세요.</span></p><div class="v4-notice-field-grid">${fields}</div><p class="v4-evidence-warning">AI 추출값은 신청 편의를 위한 초안입니다. 현재 접수 여부·잔여 예산·최종 자격은 공식 공고와 신청기관에서 확인해야 합니다.</p></section>`;
}

async function refreshV4NoticeExtraction(policyId) {
  const candidate = v4SelectedNoticeCandidates().find((item) => item.policy_id === policyId) || v4State.currentPolicy;
  if (!candidate) return;
  const extractionKey = v4NoticeExtractionKey(candidate);
  v4State.noticeExtractions.set(extractionKey, { analysis_status: "loading" });
  renderV4Preparation();
  try {
    const extraction = await api("/api/v4/application/notice-extract", { method: "POST", body: JSON.stringify({
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
  byId("v4-notice-review").innerHTML = renderV4NoticeExtraction(plan);
}

function renderV4PolicyConditions(candidate) {
  const container = byId("v4-policy-condition-list");
  if (!container || !candidate) return;
  const readiness = candidate.application_readiness || {};
  const blockers = readiness.blocking_details || [];
  const confirmations = readiness.confirmation_details || [];
  const answerRows = (detail) => {
    const answers = detail.answers || [];
    if (!answers.length) return `<div class="v4-condition-answer"><span>현재 확인값</span><strong>${escapeHtml(humanizeText(detail.current_answer || "공식 확인 필요"))}</strong></div>`;
    return answers.map((answer) => `<div class="v4-condition-answer"><div><span>앞에서 입력한 답변</span><strong>${escapeHtml(answer.question)}</strong><small>${escapeHtml(answer.answer)}</small></div>${answer.editable ? `<button type="button" class="secondary" data-edit-policy-answer="${escapeHtml(answer.field)}" data-policy-id="${escapeHtml(candidate.policy_id)}">답변 수정</button>` : ""}</div>`).join("");
  };
  const blockerHtml = blockers.length
    ? `<div class="v4-condition-group is-blocked"><h3>현재 지원이 어려운 이유</h3>${blockers.map((detail) => `<article><span>${detail.remediation_type === "structural" ? "현재 조건에서 제외" : "보완 가능"}</span><h4>${escapeHtml(humanizeText(detail.condition))}</h4>${answerRows(detail)}<p><strong>다음 확인:</strong> ${escapeHtml(humanizeText(detail.action || "공식기관에서 조건을 확인하세요."))}</p></article>`).join("")}</div>`
    : '<div class="v4-condition-group is-clear"><h3>입력한 답변 기준 제외조건에 해당하지 않음</h3><p>앞에서 입력한 답변으로 확인되는 범위에서는 확정적인 탈락 조건이 없습니다. 아직 확인하지 않은 조건과 공식 심사 결과까지 확정한 뜻은 아닙니다.</p></div>';
  const confirmationHtml = confirmations.length
    ? `<div class="v4-condition-group"><h3>아직 확인할 답변</h3>${confirmations.map((detail) => `<article><h4>${escapeHtml(humanizeText(detail.condition))}</h4>${answerRows(detail)}</article>`).join("")}</div>`
    : '<div class="v4-condition-group is-clear"><h3>추가 답변 확인 없음</h3><p>현재 입력 기준으로 남은 사용자 답변은 없습니다. 접수 상태와 서류는 공식 공고에서 다시 확인하세요.</p></div>';
  container.innerHTML = `${blockerHtml}${confirmationHtml}`;
}

function saveV4Session() {
  try {
    const finance = Object.fromEntries(v4FinanceFields.map((id) => [id, byId(id)?.value ?? ""]));
    finance.revenues = [...document.querySelectorAll(".revenue-input")].map((node) => node.value);
    sessionStorage.setItem(V4_SESSION_KEY, JSON.stringify({
      concerns: [...v4State.concerns], finance,
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
  try { snapshot = JSON.parse(sessionStorage.getItem(V4_SESSION_KEY) || "null"); } catch { return; }
  if (!snapshot) return;
  v4State.concerns = new Set(snapshot.concerns || []);
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
  toggleNoLoan(); syncV4ConcernContext(); updateSummary();
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
  const concern = event.target.closest("[data-v4-concern]");
  if (concern) {
    const key = concern.dataset.v4Concern;
    if (v4State.concerns.has(key)) v4State.concerns.delete(key);
    else if (v4State.concerns.size >= 2) return toast("걱정은 최대 두 가지까지 선택할 수 있습니다.");
    else v4State.concerns.add(key);
    syncV4ConcernContext();
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
  }
  const refreshNotice = event.target.closest("[data-v4-refresh-notice]");
  if (refreshNotice) await refreshV4NoticeExtraction(refreshNotice.dataset.v4RefreshNotice);
});

document.addEventListener("change", () => window.queueMicrotask(saveV4Session));
document.addEventListener("input", () => window.queueMicrotask(saveV4Session));
document.addEventListener("focusout", (event) => {
  if (event.target.matches(".revenue-input, #opening-cash, #monthly-rent, #monthly-labor, #monthly-purchase, #monthly-other-fixed, #loan-balance, #loan-rate, #loan-term")) renderV4FieldMessages();
});
byId("v4-no-loan").addEventListener("change", toggleNoLoan);
byId("v4-ledger-close").addEventListener("click", () => byId("v4-input-ledger").close());
byId("v4-ledger-edit").addEventListener("click", () => byId("v4-input-ledger").close());
byId("v4-ledger-confirm").addEventListener("click", () => { byId("v4-input-ledger").close(); saveV4Session(); runComparison("diagnosis"); });
restoreV4Session();
