const state = {
  data: null, areaPoints: [], industries: [], selectedArea: null, selectedDong: "",
  marketScenarios: null, scenario: "central", goal: "최소부채", selectedAlternative: null, focusedPolicyId: "",
  scenarioResults: {}, scenarioCacheKey: "", hoveredScenario: null, hoveredAlternative: null,
  revenueMonths: 6, mapLevel: "district", map: null, circleLayer: null, circles: new Map(),
  visibleDongDistrict: "", visibleAreaScope: "", policies: [], chatMessages: [], chatTurns: 0,
  eligibilityAnswers: {}, policyScenarioValues: {}, selectedPolicyIds: new Set(), conditionalPolicyIds: new Set(), policySelectionInitialized: false, questionCatalog: {}, actionBrief: null,
  questionWizardOrder: [], questionWizardAllOrder: [], questionWizardIndex: 0, questionWizardKey: "", questionWizardComplete: false, questionWizardResultsVisible: false, questionWizardMode: "full", questionWizardReturnPolicyId: "", questionBatchRound: 0, v3AskedFields: [],
  policyScenarioEditorPolicyId: "", costReductionEditorOpen: false,
  situationInterpretation: null, situationContext: null,
  pendingWhatIf: null, whatIfUndo: null, whatIfOriginalPrompt: "", whatIfClarificationAttempts: 0,
};

const byId = (id) => document.getElementById(id);
const cloneData = (value) => value == null ? value : JSON.parse(JSON.stringify(value));
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
const compactMoney = (value) => {
  if (value == null) return "확인 필요";
  const amount = Math.round(value);
  if (Math.abs(amount) >= 100000000) return `${(amount / 100000000).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}억원`;
  if (Math.abs(amount) >= 10000) return `${Math.round(amount / 10000).toLocaleString("ko-KR")}만원`;
  return `${amount.toLocaleString("ko-KR")}원`;
};
const safeUrl = (value) => { try { const parsed = new URL(value); return ["https:", "http:"].includes(parsed.protocol) ? escapeHtml(parsed.href) : "#"; } catch { return "#"; } };
const scenarioLabels = { downside: "하방 범위", central: "기준 범위", recovery: "회복 범위" };
const financialPolicyNeeds = {
  POL_SEOUL_FUND_2026: "현금 확보",
  POL_SEOUL_CRISIS_TRACK2_2026H2: "현금 확보",
  POL_SEMAS_STABILITY_VOUCHER_2026: "현금 확보",
  POL_SEMAS_REFINANCE_2026: "대출 부담 완화",
  POL_SEMAS_RECHALLENGE_2026: "대출 부담 완화",
  POL_SEMAS_EMPLOYMENT_INSURANCE_2026: "운영비 절감",
  POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026: "운영비 절감",
  POL_SEOUL_DIGITAL_MIDLIFE_2026H2: "운영비 절감",
  POL_SEOUL_ZERO_MARKET_2026_2: "운영비 절감",
  POL_SEOUL_CLOSURE_2026: "재기·전환",
  POL_SEOUL_RESTART_2026: "재기·전환",
};
const policyCardSummaries = {
  POL_SEOUL_FUND_2026: "운전자금과 시설자금을 융자해 사업 운영에 필요한 자금을 마련합니다.",
  POL_SEOUL_CRISIS_TRACK2_2026H2: "경영진단과 맞춤 컨설팅, 개선 또는 정리 비용을 최대 300만원 지원합니다.",
  POL_SEMAS_STABILITY_VOUCHER_2026: "공과금과 4대 보험료 등 고정비에 사용할 수 있는 바우처를 지원합니다.",
  POL_SEMAS_REFINANCE_2026: "고금리 대출을 장기 저금리 정책자금으로 전환해 상환 부담을 낮춥니다.",
  POL_SEMAS_RECHALLENGE_2026: "재창업 또는 채무조정 소상공인에게 사업 재도전용 정책자금을 융자합니다.",
  POL_SEMAS_EMPLOYMENT_INSURANCE_2026: "자영업자 고용보험료의 50~80%를 최대 5년간 지원합니다.",
  POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026: "육아휴직·출산휴가 요건을 충족한 기업의 사업주 부담을 지원합니다.",
  POL_SEOUL_DIGITAL_MIDLIFE_2026H2: "디지털 교육과 컨설팅, 솔루션 도입비를 최대 300만원 지원합니다.",
  POL_SEOUL_ZERO_MARKET_2026_2: "다회용기와 무포장 운영에 필요한 물품, 홍보, 시설 임차비를 지원합니다.",
  POL_SEOUL_CLOSURE_2026: "폐업 예정 점포에 사업정리 컨설팅, 비용지원, 전직 연계를 제공합니다.",
  POL_SEOUL_RESTART_2026: "재도전 소상공인에게 교육, 컨설팅, 저금리 대출보증과 재도전 자금을 지원합니다.",
};
const policyFundingGuidance = {
  POL_SEOUL_FUND_2026: { terms: "운전자금·시설자금 융자입니다. 한도와 금리는 신청 유형별 공식 공고에서 확인해야 합니다." },
  POL_SEOUL_CRISIS_TRACK2_2026H2: { terms: "개선 또는 정리 비용을 공고상 최대 300만원까지 지원합니다.", maximumAmount: 3000000 },
  POL_SEMAS_STABILITY_VOUCHER_2026: { terms: "공과금과 4대 보험료 등에 쓰는 바우처입니다. 실제 지급액은 공고와 심사 결과를 확인해야 합니다." },
  POL_SEMAS_REFINANCE_2026: { terms: "기존 고금리 대출을 정책자금으로 전환하는 융자입니다. 전환 가능 원금과 금리는 공식 심사 전 확정되지 않습니다." },
  POL_SEMAS_RECHALLENGE_2026: { terms: "재창업·채무조정 소상공인을 위한 융자입니다. 실제 한도와 실행일은 공식 심사 전 확정되지 않습니다." },
  POL_SEMAS_EMPLOYMENT_INSURANCE_2026: { terms: "자영업자 고용보험료의 50~80%를 등급에 따라 지원하며, 납부 확인 후 환급됩니다." },
  POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026: { terms: "근로자 1인당 월 최대 30만원, 3개월, 기업당 5인 범위입니다.", maximumAmount: 4500000 },
  POL_SEOUL_DIGITAL_MIDLIFE_2026H2: { terms: "교육·컨설팅과 솔루션 도입비를 공고상 최대 300만원까지 지원합니다.", maximumAmount: 3000000 },
  POL_SEOUL_ZERO_MARKET_2026_2: { terms: "다회용기·무포장 운영에 필요한 물품과 시설 비용 지원입니다. 인정 품목과 금액은 공고 확인이 필요합니다." },
  POL_SEOUL_CLOSURE_2026: { terms: "폐업 예정 점포의 정리 컨설팅과 비용 지원입니다. 인정 비용과 지급 시점은 공식 확인이 필요합니다." },
  POL_SEOUL_RESTART_2026: { terms: "교육·컨설팅과 저금리 대출보증·재도전 자금입니다. 실제 금융조건은 공식 심사 전 확정되지 않습니다." },
};
const policyScenarioSupported = new Set([
  "POL_SEOUL_CRISIS_TRACK2_2026H2",
  "POL_SEMAS_EMPLOYMENT_INSURANCE_2026",
  "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026",
]);
const industryMajorLabels = { CS1: "외식업", CS2: "서비스업", CS3: "소매업" };
const policyNames = {
  POL_SEOUL_CRISIS_TRACK2_2026H2: "위기 소상공인 지원",
  POL_SEMAS_STABILITY_VOUCHER_2026: "소상공인 경영안정 바우처",
  POL_SEMAS_REFINANCE_2026: "소상공인 대환대출",
  POL_SEMAS_RECHALLENGE_2026: "소상공인 재도전특별자금",
  POL_SEOUL_FUND_2026: "서울시 중소기업육성자금",
};
const policyByAlternative = {
  track2_reimbursement: "POL_SEOUL_CRISIS_TRACK2_2026H2", refinance: "POL_SEMAS_REFINANCE_2026",
  emergency_loan: "POL_SEOUL_FUND_2026", combined_safe_cash: "POL_SEOUL_CRISIS_TRACK2_2026H2",
  conditional_pol_seoul_fund_2026: "POL_SEOUL_FUND_2026",
  conditional_pol_seoul_crisis_track2_2026h2: "POL_SEOUL_CRISIS_TRACK2_2026H2",
  conditional_pol_semas_rechallenge_2026: "POL_SEMAS_RECHALLENGE_2026",
  conditional_pol_semas_refinance_2026: "POL_SEMAS_REFINANCE_2026",
  dynamic_pol_semas_stability_voucher_2026: "POL_SEMAS_STABILITY_VOUCHER_2026",
};
const conditionalAlternativeByPolicy = {
  POL_SEOUL_FUND_2026: "conditional_pol_seoul_fund_2026",
  POL_SEOUL_CRISIS_TRACK2_2026H2: "conditional_pol_seoul_crisis_track2_2026h2",
  POL_SEMAS_RECHALLENGE_2026: "conditional_pol_semas_rechallenge_2026",
  POL_SEMAS_REFINANCE_2026: "conditional_pol_semas_refinance_2026",
  POL_SEMAS_STABILITY_VOUCHER_2026: "dynamic_pol_semas_stability_voucher_2026",
};
const goalPresentations = {
  최소부채: { label: "빚을 덜 늘리기", metric: "새로 생기는 빚" },
  최장생존: { label: "현금을 오래 유지하기", metric: "6개월 생존 기간" },
  최소상환: { label: "매달 갚는 돈 줄이기", metric: "월 최대 상환액" },
  빠른실행: { label: "효과가 빨리 반영되는 안", metric: "효과 시작 시점" },
};
const mapPalette = {
  halo: "#ffffff",
  district: { stroke: "#173a72", fill: "#2f6feb" },
  dong: { stroke: "#1d4ed8", fill: "#60a5fa" },
  area: { stroke: "#1d4ed8", fill: "#60a5fa" },
  selected: { stroke: "#102a56", fill: "#2563eb" },
};
const presentationPresets = {
  "cash-rich": { areaCode: "3001496", revenues: [1800, 1780, 1760, 1740, 1710, 1680], cash: 3000, rent: 200, labor: 450, purchase: 400, other: 90, loan: 1000, rate: 4, term: 48 },
  stable: { areaCode: "3120012", revenues: [1200, 1190, 1210, 1180, 1200, 1190], cash: 1200, rent: 180, labor: 350, purchase: 300, other: 70, loan: 1500, rate: 5, term: 36 },
  "sales-down": { areaCode: "3001491", revenues: [700, 760, 820, 880, 940, 1000], cash: 500, rent: 180, labor: 350, purchase: 280, other: 80, loan: 2000, rate: 6.5, term: 36 },
  "high-fixed": { areaCode: "3110131", revenues: [1000, 1020, 1040, 1060, 1080, 1100], cash: 400, rent: 300, labor: 500, purchase: 250, other: 180, loan: 1500, rate: 6, term: 30 },
  "debt-heavy": { areaCode: "3120153", revenues: [1100, 1120, 1140, 1160, 1180, 1200], cash: 300, rent: 180, labor: 300, purchase: 250, other: 100, loan: 5000, rate: 9, term: 24 },
};
const situationSignalGuidance = {
  sales_decline: "최근 6개월 월매출을 실제 금액으로 확인합니다.",
  debt_concern: "대출 잔액·금리·남은 상환기간을 먼저 확인합니다.",
  fixed_cost_concern: "임대료·인건비·필수 매입비를 먼저 확인합니다.",
  cash_concern: "현재 보유 현금과 다음 28일 필수지출을 먼저 확인합니다.",
};

function toast(message) {
  const node = byId("toast"); node.textContent = message; node.classList.add("is-visible");
  window.setTimeout(() => node.classList.remove("is-visible"), 3000);
}

let loadingDepth = 0, loadingStartedAt = 0, loadingTimer = null;
function updateLoadingElapsed() {
  const elapsedSeconds = Math.max(0, Math.floor((Date.now() - loadingStartedAt) / 1000));
  byId("global-loading-elapsed").textContent = `경과 시간 ${elapsedSeconds.toLocaleString("ko-KR")}초`;
}
function showLoading(message = "잠시만 기다려 주세요.") {
  if (loadingDepth === 0) {
    loadingStartedAt = Date.now();
    updateLoadingElapsed();
    loadingTimer = window.setInterval(updateLoadingElapsed, 1000);
  }
  loadingDepth += 1;
  byId("global-loading-message").textContent = message;
  byId("global-loading").hidden = false;
  document.body.setAttribute("aria-busy", "true");
}
function hideLoading() {
  loadingDepth = Math.max(0, loadingDepth - 1);
  if (loadingDepth) return;
  window.clearInterval(loadingTimer); loadingTimer = null; loadingStartedAt = 0;
  byId("global-loading").hidden = true;
  document.body.removeAttribute("aria-busy");
}

async function api(path, options = {}) {
  const headers = options.body ? { "Content-Type": "application/json", ...(options.headers || {}) } : options.headers;
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || "요청을 처리하지 못했습니다.");
  return payload;
}

function showStep(id) {
  const order = ["business", "finance", "diagnosis", "decision", "preparation"];
  if (id === "decision" && state.data && !state.questionWizardResultsVisible) {
    toast("확인 질문을 먼저 완료해 주세요.");
    return;
  }
  document.querySelectorAll(".screen").forEach((node) => node.classList.toggle("is-active", node.id === id));
  document.querySelectorAll(".step-button").forEach((node) => node.classList.toggle("is-active", node.dataset.step === id));
  byId("summary-progress").textContent = `${order.indexOf(id) + 1} / 5`;
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (id === "business" && state.map) window.setTimeout(() => state.map.invalidateSize(), 80);
  if (state.data && ["diagnosis", "decision"].includes(id)) window.requestAnimationFrame(renderCharts);
}

function updateSummary() {
  byId("summary-area").textContent = state.selectedArea ? `${state.selectedArea.district} ${state.selectedArea.name}` : "선택 전";
  const industry = state.industries.find((item) => item.code === byId("industry-select").value);
  byId("summary-industry").textContent = industry?.name || "선택 전";
  const revenues = revenueValues(false);
  byId("summary-revenue").textContent = revenues.length ? compactMoney(revenues.reduce((a, b) => a + b, 0) / revenues.length) : "입력 전";
  const cash = moneyInputValue("opening-cash", null);
  byId("summary-cash").textContent = cash == null ? "입력 전" : compactMoney(cash);
  byId("summary-scenario").textContent = scenarioLabels[state.scenario];
}

function aggregateAreas(items, key) {
  const groups = new Map();
  items.forEach((item) => { const name = item[key]; if (!groups.has(name)) groups.set(name, []); groups.get(name).push(item); });
  return [...groups.entries()].map(([name, group]) => {
    const weight = group.reduce((sum, item) => sum + Math.max(1, item.area_m2), 0);
    return {
      name, count: group.length,
      latitude: group.reduce((sum, item) => sum + item.latitude * Math.max(1, item.area_m2), 0) / weight,
      longitude: group.reduce((sum, item) => sum + item.longitude * Math.max(1, item.area_m2), 0) / weight,
    };
  }).sort((a, b) => a.name.localeCompare(b.name, "ko"));
}

function aggregateDongs(items) {
  const groups = new Map();
  items.forEach((item) => {
    const key = `${item.district}::${item.administrative_dong}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  });
  return [...groups.values()].map((group) => {
    const weight = group.reduce((sum, item) => sum + Math.max(1, item.area_m2), 0);
    return {
      district: group[0].district,
      name: group[0].administrative_dong,
      count: group.length,
      latitude: group.reduce((sum, item) => sum + item.latitude * Math.max(1, item.area_m2), 0) / weight,
      longitude: group.reduce((sum, item) => sum + item.longitude * Math.max(1, item.area_m2), 0) / weight,
    };
  }).sort((a, b) => `${a.district} ${a.name}`.localeCompare(`${b.district} ${b.name}`, "ko"));
}

function addPointHalo(position, radius) {
  L.circleMarker(position, { radius: radius + 2, color: mapPalette.halo, weight: 4, opacity: .9, fill: false, interactive: false }).addTo(state.circleLayer);
}

function addAreaHalo(position, radius, selected) {
  L.circle(position, { radius, color: mapPalette.halo, weight: selected ? 7 : 4, opacity: .86, fill: false, interactive: false }).addTo(state.circleLayer);
}

function addCircleLabel(group, level) {
  const district = level === "district";
  const size = district ? [70, 42] : [64, 38];
  const label = L.divIcon({
    className: `map-circle-label map-circle-label--${level}`,
    html: `<strong>${escapeHtml(group.name)}</strong><small>상권 ${group.count.toLocaleString("ko-KR")}개</small>`,
    iconSize: size,
    iconAnchor: [size[0] / 2, size[1] / 2],
  });
  L.marker([group.latitude, group.longitude], { icon: label, interactive: false, keyboard: false }).addTo(state.circleLayer);
}

function addAreaLabel(item) {
  const size = [76, 36];
  const label = L.divIcon({
    className: "map-circle-label map-circle-label--area",
    html: `<strong title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</strong>`,
    iconSize: size,
    iconAnchor: [size[0] / 2, size[1] / 2],
  });
  L.marker([item.latitude, item.longitude], { icon: label, interactive: false, keyboard: false }).addTo(state.circleLayer);
}

function initMap() {
  if (!window.L) { byId("map-caption").textContent = "지도를 불러오지 못했습니다. 왼쪽 목록에서 상권을 선택할 수 있습니다."; return; }
  state.map = L.map("area-map", { preferCanvas: true, zoomControl: true }).setView([37.5665, 126.978], 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors" }).addTo(state.map);
  state.circleLayer = L.layerGroup().addTo(state.map);
  state.map.on("zoomend", handleMapZoomEnd);
  state.map.on("moveend", handleMapMoveEnd);
  renderDistrictCircles();
}

function clearMap() {
  if (!state.map || !state.circleLayer) return false;
  state.circleLayer.clearLayers(); state.circles.clear(); return true;
}
function fitMap(bounds, maxZoom) { if (bounds.length) state.map.fitBounds(bounds, { padding: [36, 36], maxZoom }); }

function renderDistrictCircles(fit = false) {
  state.mapLevel = "district"; state.visibleDongDistrict = ""; state.visibleAreaScope = ""; updateMapLevel(); if (!clearMap()) return;
  const bounds = [];
  aggregateAreas(state.areaPoints, "district").forEach((group) => {
    const content = `<strong>${escapeHtml(group.name)}</strong><br>포함 상권 ${group.count.toLocaleString("ko-KR")}개<br><small>눌러서 행정동 보기</small>`;
    const position = [group.latitude, group.longitude], radius = Math.min(40, 26 + Math.sqrt(group.count) * 1.1);
    addPointHalo(position, radius);
    const circle = L.circleMarker(position, { radius, color: mapPalette.district.stroke, weight: 2.5, fillColor: mapPalette.district.fill, fillOpacity: .58 }).bindTooltip(content, { sticky: true }).bindPopup(content);
    circle.on("click", () => chooseDistrict(group.name, true)); circle.addTo(state.circleLayer); addCircleLabel(group, "district"); bounds.push(position);
  });
  if (fit) fitMap(bounds, 11);
}

function renderDongCircles(fit = true, viewDistrict = "") {
  const district = viewDistrict || byId("district-select").value;
  if (!district) return renderDistrictCircles(fit);
  state.mapLevel = "dong"; state.visibleDongDistrict = district; state.visibleAreaScope = ""; updateMapLevel(); if (!clearMap()) return;
  const focusBounds = [];
  const items = state.areaPoints.filter((item) => item.district === district);
  aggregateDongs(items).forEach((group) => {
    const content = `<strong>${escapeHtml(group.district)} ${escapeHtml(group.name)}</strong><br>포함 상권 ${group.count.toLocaleString("ko-KR")}개<br><small>눌러서 개별 상권 보기</small>`;
    const position = [group.latitude, group.longitude], radius = Math.min(30, 23 + Math.sqrt(group.count) * 1.6);
    addPointHalo(position, radius);
    const circle = L.circleMarker(position, { radius, color: mapPalette.dong.stroke, weight: 2.25, fillColor: mapPalette.dong.fill, fillOpacity: .56, dashArray: "5 3" }).bindTooltip(content, { sticky: true }).bindPopup(content);
    circle.on("click", () => chooseDong(group.district, group.name, true)); circle.addTo(state.circleLayer); addCircleLabel(group, "dong");
    if (group.district === district) focusBounds.push(position);
  });
  if (fit) fitMap(focusBounds, 13);
}

function areaPopup(item) {
  return `<strong>${escapeHtml(item.name)}</strong><br>${escapeHtml(item.district)} · ${escapeHtml(item.administrative_dong)}<br>${escapeHtml(item.category)} · ${Math.round(item.area_m2).toLocaleString("ko-KR")}㎡`;
}

function renderAreaCircles(focusItems = filteredAreas(), fit = true) {
  state.mapLevel = "area"; updateMapLevel(); if (!clearMap()) return;
  const bounds = focusItems.map((item) => [item.latitude, item.longitude]);
  const first = focusItems[0];
  state.visibleAreaScope = first ? `${first.district}::${first.administrative_dong}` : "";
  focusItems.forEach((item) => {
    const selected = state.selectedArea?.code === item.code;
    const position = [item.latitude, item.longitude], radius = Math.max(105, item.radius_m);
    addAreaHalo(position, radius, selected);
    const colors = selected ? mapPalette.selected : mapPalette.area;
    const circle = L.circle(position, { radius, color: colors.stroke, weight: selected ? 4 : 2, fillColor: colors.fill, fillOpacity: selected ? .64 : .3 }).bindTooltip(areaPopup(item), { sticky: true }).bindPopup(areaPopup(item));
    circle.on("click", () => selectArea(item.code, true)); circle.addTo(state.circleLayer); addAreaLabel(item); state.circles.set(item.code, circle);
  });
  if (fit) fitMap(bounds, 15);
}

function nearestAreaToMapCenter() {
  if (!state.map || !state.areaPoints.length) return null;
  const center = state.map.getCenter(), longitudeScale = Math.cos(center.lat * Math.PI / 180);
  return state.areaPoints.reduce((best, item) => {
    const latitudeDistance = item.latitude - center.lat;
    const longitudeDistance = (item.longitude - center.lng) * longitudeScale;
    const distance = latitudeDistance * latitudeDistance + longitudeDistance * longitudeDistance;
    return !best || distance < best.distance ? { item, distance } : best;
  }, null)?.item || null;
}

function handleMapZoomEnd() {
  if (!state.map || byId("area-search").value.trim()) return;
  const zoom = state.map.getZoom(), nearest = nearestAreaToMapCenter();
  if (!nearest) return;
  if (zoom <= 12) {
    if (state.mapLevel !== "district" || byId("district-select").value) resetMapToSeoul(false);
    return;
  }
  if (zoom <= 14) {
    if (state.mapLevel !== "dong" || byId("district-select").value !== nearest.district) chooseDistrict(nearest.district, false);
    return;
  }
  if (zoom <= 16) {
    if (state.mapLevel !== "area" || byId("dong-select").value !== nearest.administrative_dong || byId("district-select").value !== nearest.district) chooseDong(nearest.district, nearest.administrative_dong, false);
    return;
  }
  if (state.selectedArea?.code !== nearest.code) selectArea(nearest.code, false, true, false);
}

function handleMapMoveEnd() {
  if (!state.map || byId("area-search").value.trim()) return;
  const nearest = nearestAreaToMapCenter();
  if (!nearest) return;
  if (state.mapLevel === "dong" && nearest.district !== state.visibleDongDistrict) {
    renderDongCircles(false, nearest.district);
    return;
  }
  const scope = `${nearest.district}::${nearest.administrative_dong}`;
  if (state.mapLevel === "area" && scope !== state.visibleAreaScope) {
    const nearby = state.areaPoints.filter((item) => item.district === nearest.district && item.administrative_dong === nearest.administrative_dong);
    renderAreaCircles(nearby, false);
  }
}

function updateMapLevel() {
  const district = byId("district-select").value, dong = byId("dong-select").value;
  const buttons = [...byId("map-level").querySelectorAll("button")];
  buttons[0].textContent = "서울 전체";
  buttons[1].textContent = district || "자치구"; buttons[1].disabled = !district;
  buttons[2].textContent = dong || "행정동"; buttons[2].disabled = !dong;
  buttons.forEach((button) => button.classList.toggle("is-current", button.dataset.mapLevel === state.mapLevel));
}

function populateDongs(district, selected = "") {
  const dongs = [...new Set(state.areaPoints.filter((item) => item.district === district).map((item) => item.administrative_dong))].sort((a, b) => a.localeCompare(b, "ko"));
  byId("dong-select").disabled = !district;
  byId("dong-select").innerHTML = district ? `<option value="">${escapeHtml(district)} 전체</option>${dongs.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("")}` : '<option value="">자치구를 먼저 선택</option>';
  byId("dong-select").value = selected; state.selectedDong = selected;
}

function filteredAreas() {
  const district = byId("district-select").value, dong = byId("dong-select").value;
  const query = byId("area-search").value.trim().toLocaleLowerCase("ko-KR");
  if (query) return state.areaPoints.filter((item) => `${item.name} ${item.district} ${item.administrative_dong}`.toLocaleLowerCase("ko-KR").includes(query));
  return state.areaPoints.filter((item) => (!district || item.district === district) && (!dong || item.administrative_dong === dong));
}

function refreshAreaList() {
  const district = byId("district-select").value, query = byId("area-search").value.trim();
  const items = district || query ? filteredAreas() : [];
  byId("area-select").innerHTML = items.map((item) => `<option value="${escapeHtml(item.code)}">${escapeHtml(item.name)} · ${escapeHtml(item.administrative_dong)}</option>`).join("");
  byId("area-count").textContent = district || query ? `${items.length.toLocaleString("ko-KR")}개 상권` : "지도에서 자치구를 선택해 주세요.";
  if (state.selectedArea && items.some((item) => item.code === state.selectedArea.code)) byId("area-select").value = state.selectedArea.code;
}

function clearSelectedArea() {
  state.selectedArea = null; byId("selected-location").textContent = "지도 또는 목록에서 상권을 선택해 주세요."; updateSummary();
}

function chooseDistrict(name, fit = true) {
  byId("district-select").value = name; byId("area-search").value = ""; populateDongs(name); clearSelectedArea(); refreshAreaList(); renderDongCircles(fit);
}
function chooseDong(district, name, fit = true) {
  byId("district-select").value = district; populateDongs(district, name); byId("area-search").value = "";
  state.selectedDong = name; clearSelectedArea(); refreshAreaList(); renderAreaCircles(filteredAreas(), fit);
}
function resetMapToSeoul(fit = true) {
  byId("district-select").value = ""; byId("area-search").value = ""; populateDongs(""); clearSelectedArea(); refreshAreaList(); renderDistrictCircles(fit);
}

function selectArea(code, fromMap = false, refreshResults = true, focusMap = true, loadScenario = true) {
  const item = state.areaPoints.find((area) => area.code === String(code));
  if (!item) return;
  state.selectedArea = item; byId("district-select").value = item.district; populateDongs(item.district, item.administrative_dong); byId("area-search").value = "";
  refreshAreaList(); byId("area-select").value = item.code;
  byId("selected-location").innerHTML = `<strong>${escapeHtml(item.name)}</strong><br>${escapeHtml(item.district)} ${escapeHtml(item.administrative_dong)} · ${escapeHtml(item.category)} · ${Math.round(item.area_m2).toLocaleString("ko-KR")}㎡`;
  renderAreaCircles(filteredAreas(), false);
  const circle = state.circles.get(item.code);
  if (focusMap && state.map && circle) { state.map.flyTo([item.latitude, item.longitude], 17, { duration: fromMap ? .35 : .6 }); if (fromMap) circle.openPopup(); }
  updateSummary();
  if (refreshResults) refreshComparisonForMarketChange(); else if (loadScenario) loadMarketScenarios();
}

function industryMajor(code) { return String(code || "").slice(0, 3); }
function populateIndustries(major, selected = "") {
  const items = state.industries.filter((item) => industryMajor(item.code) === major);
  byId("industry-select").disabled = !major;
  byId("industry-select").innerHTML = major ? `<option value="">세부 업종 선택</option>${items.map((item) => `<option value="${escapeHtml(item.code)}">${escapeHtml(item.name)}</option>`).join("")}` : '<option value="">대분류를 먼저 선택</option>';
  byId("industry-select").value = selected;
}

async function loadCatalogs() {
  const [areas, industries, policies] = await Promise.all([api("/api/v1/catalog/area-map"), api("/api/v1/catalog/industries"), api("/api/v1/catalog/policies")]);
  state.areaPoints = areas.items; state.industries = industries.items; state.policies = policies.items.filter((item) => Object.hasOwn(financialPolicyNeeds, item.policy_id));
  state.policies.forEach((item) => { policyNames[item.policy_id] = item.policy_name; });
  byId("qa-policy").innerHTML = `<option value="">전체 정책에서 찾기</option>${state.policies.map((item) => `<option value="${escapeHtml(item.policy_id)}">${escapeHtml(item.policy_name)}</option>`).join("")}`;
  const districts = [...new Set(state.areaPoints.map((item) => item.district))].sort((a, b) => a.localeCompare(b, "ko"));
  byId("district-select").innerHTML = `<option value="">서울 전체</option>${districts.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("")}`;
  const majors = [...new Set(state.industries.map((item) => industryMajor(item.code)))].filter(Boolean);
  byId("industry-major-select").innerHTML = `<option value="">대분류 선택</option>${majors.map((code) => `<option value="${escapeHtml(code)}">${escapeHtml(industryMajorLabels[code] || "기타 업종")}</option>`).join("")}`;
  populateDongs(""); populateIndustries(""); refreshAreaList(); initMap();
}

function monthLabel(index) {
  const date = new Date(); date.setDate(1); date.setMonth(date.getMonth() - index);
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월`;
}
function renderRevenueMonths(values = null) {
  const existing = values || [...document.querySelectorAll(".revenue-input")].map((node) => node.value);
  byId("revenue-months").innerHTML = Array.from({ length: state.revenueMonths }, (_, index) => `<label class="month-entry">${monthLabel(index)}<span class="money-input"><input class="revenue-input" type="number" min="0" step="1" inputmode="numeric" placeholder="예: 1,200" value="${escapeHtml(existing[index] ?? "")}" required><b>만원</b></span>${state.revenueMonths > 3 && index === state.revenueMonths - 1 ? '<button class="remove-month" type="button" aria-label="가장 오래된 달 삭제">×</button>' : ""}</label>`).join("");
  byId("add-revenue-month").disabled = state.revenueMonths >= 12;
  document.querySelectorAll(".revenue-input").forEach((node) => node.addEventListener("input", updateSummary));
  document.querySelector(".remove-month")?.addEventListener("click", () => { state.revenueMonths -= 1; renderRevenueMonths(); updateSummary(); });
}

function numericValue(id, fallback = 0) { const raw = byId(id).value; return raw === "" ? fallback : Number(raw); }
function moneyInputValue(id, fallback = 0) { const raw = byId(id).value; return raw === "" ? fallback : Math.round(Number(raw) * 10000); }
function revenueValues(strict = true) {
  const raw = [...document.querySelectorAll(".revenue-input")].map((node) => node.value);
  if (strict && raw.some((value) => value === "")) throw new Error("최근 월매출을 모두 입력해 주세요.");
  return raw.filter((value) => value !== "").map((value) => Math.round(Number(value) * 10000));
}
function validateBusiness() {
  if (!state.selectedArea) throw new Error("상권을 선택해 주세요.");
  if (!byId("industry-major-select").value) throw new Error("업종 대분류를 선택해 주세요.");
  if (!byId("industry-select").value) throw new Error("세부 업종을 선택해 주세요.");
}
function validateFinance() {
  revenueValues(true);
  ["opening-cash", "monthly-rent", "monthly-labor", "monthly-purchase", "monthly-other-fixed", "loan-balance"].forEach((id) => { if (byId(id).value === "" || Number(byId(id).value) < 0) throw new Error("현재 현금과 월 지출을 빠짐없이 입력해 주세요."); });
  if (moneyInputValue("loan-balance") > 0 && numericValue("loan-rate", null) == null) throw new Error("대출 이자율을 입력해 주세요.");
}
function referenceDate() {
  const date = new Date(); date.setDate(1); date.setMonth(date.getMonth() + 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-01`;
}

const coreEligibilityFields = new Set(["business_scale", "opening_date", "employee_count", "is_operating", "rented_exclusive_place", "self_owned_place", "sales_decreased", "disaster_document", "tax_paid", "fund_restricted_industry", "policy_loan_restricted_industry", "prior_crisis_support", "prior_closure_support", "prior_digital_support", "subfund_selected", "zero_market_operation", "eligible_business_registration", "shared_office_only", "consignment_only", "duplicate_public_support", "safety_product_business", "ncb_919_or_below", "maturity_extension_difficulty", "common_loan_restriction"]);

function eligibilityProfilePayload() {
  const profile = { policy_answers: {} };
  Object.entries(state.eligibilityAnswers).forEach(([field, value]) => {
    if (value === "" || value == null || value === "unknown") return;
    if (coreEligibilityFields.has(field)) profile[field] = field === "employee_count" ? Number(value) : value;
    else profile.policy_answers[field] = value;
  });
  return profile;
}

function policyScenarioPayload() {
  const scenarios = [];
  const employment = state.policyScenarioValues.POL_SEMAS_EMPLOYMENT_INSURANCE_2026 || {};
  if (state.selectedPolicyIds.has("POL_SEMAS_EMPLOYMENT_INSURANCE_2026") && employment.grade && ["true", "false"].includes(employment.inBaseline)) scenarios.push({
    policy_id: "POL_SEMAS_EMPLOYMENT_INSURANCE_2026",
    employment_insurance_grade: Number(employment.grade),
    expense_already_in_baseline: employment.inBaseline === "true",
  });
  const family = state.policyScenarioValues.POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026 || {};
  if (state.selectedPolicyIds.has("POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026") && family.amount && family.paymentDate) scenarios.push({
    policy_id: "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026",
    approved_support_amount: Math.round(Number(family.amount) * 10000),
    payment_date: family.paymentDate,
  });
  const crisis = state.policyScenarioValues.POL_SEOUL_CRISIS_TRACK2_2026H2 || {};
  if (state.selectedPolicyIds.has("POL_SEOUL_CRISIS_TRACK2_2026H2") && crisis.amount && crisis.expenseAmount && crisis.expenseDate && crisis.paymentDate) scenarios.push({
    policy_id: "POL_SEOUL_CRISIS_TRACK2_2026H2",
    approved_support_amount: Math.round(Number(crisis.amount) * 10000),
    expense_amount: Math.round(Number(crisis.expenseAmount) * 10000),
    expense_date: crisis.expenseDate,
    payment_date: crisis.paymentDate,
  });
  return scenarios;
}

function costReductionPayload() {
  const fields = [
    ["rent", "reduce-rent", "monthly-rent", "임대료"],
    ["labor", "reduce-labor", "monthly-labor", "인건비"],
    ["purchase", "reduce-purchase", "monthly-purchase", "필수 매입비"],
    ["other_fixed", "reduce-other", "monthly-other-fixed", "기타 고정비"],
  ];
  const payload = {};
  fields.forEach(([key, reductionId, sourceId, label]) => {
    const reduction = moneyInputValue(reductionId);
    if (reduction > moneyInputValue(sourceId)) throw new Error(`${label} 절감액은 현재 입력한 비용보다 클 수 없습니다.`);
    payload[key] = reduction;
  });
  return Object.values(payload).some((value) => value > 0) ? payload : null;
}

function updateConfirmedReduction() {
  const total = ["reduce-rent", "reduce-labor", "reduce-purchase", "reduce-other"].reduce((sum, id) => sum + moneyInputValue(id), 0);
  byId("confirmed-reduction").textContent = `확정 절감액 월 ${compactMoney(total)}`;
}

async function loadMarketScenarios() {
  if (!state.selectedArea || !byId("industry-select").value) return;
  try {
  const payload = await api(`/api/v4/market-scenarios/${encodeURIComponent(state.selectedArea.code)}/${encodeURIComponent(byId("industry-select").value)}`);
    state.marketScenarios = payload.market_scenario;
    const nodes = document.querySelectorAll("#scenario-options label");
    if (state.marketScenarios.available) {
      ["downside", "central", "recovery"].forEach((name, index) => { const item = state.marketScenarios.scenarios[name]; nodes[index].querySelector("b").textContent = `13주 ${formatPercent(item.thirteen_week_percent)} · 6개월 ${formatPercent(item.six_month_percent)}`; });
    } else { nodes.forEach((node) => node.querySelector("b").textContent = "집계자료 없음"); }
  } catch {
    state.marketScenarios = null;
    document.querySelectorAll("#scenario-options label").forEach((node) => { node.querySelector("b").textContent = "변화 범위 불러오기 실패"; });
  }
  updateScenarioApplicationStatus();
}
function formatPercent(value) { return `${Number(value) > 0 ? "+" : ""}${Number(value).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}%`; }

function selectedScenarioSummary() {
  const modelScenario = state.marketScenarios?.scenarios?.[state.scenario];
  const comparedScenario = scenarioComparison().find((item) => item.scenario === state.scenario);
  const percent = modelScenario?.thirteen_week_percent ?? comparedScenario?.thirteen_week_percent;
  return `${scenarioLabels[state.scenario]}${percent == null ? "" : ` · 13주 ${formatPercent(percent)}`}`;
}

function updateScenarioApplicationStatus() {
  const summary = selectedScenarioSummary();
  byId("scenario-application-status").textContent = `${summary}를 적용했습니다. 아래 진단과 4단계 대안 비교가 이 범위로 계산됩니다.`;
  byId("decision-scenario-status").textContent = summary;
  byId("decision-scenario-help").textContent = state.data ? "3단계에서 선택한 범위로 모든 대안을 계산했습니다." : "선택한 범위가 3단계 진단과 4단계 대안에 적용됩니다.";
}

async function refreshComparisonForMarketChange() {
  await loadMarketScenarios();
  if (state.data) await runComparison("diagnosis", false);
}

function comparisonRequest(scenario = state.scenario) {
  const loanBalance = moneyInputValue("loan-balance");
  return {
    area_code: state.selectedArea.code, industry_code: byId("industry-select").value, market_scenario: scenario,
    direct_shock_13_week_percent: 0, direct_shock_6_month_percent: 0, safe_cash_override: null,
    goal: state.goal, assume_conditional: true, v2_mode: true,
    selected_policy_ids: [...state.selectedPolicyIds], conditional_policy_ids: [...state.conditionalPolicyIds], cost_reduction_plan: costReductionPayload(),
    quick_input: {
      reference_date: referenceDate(), opening_cash: moneyInputValue("opening-cash"), safe_cash_threshold: 0,
      recent_monthly_revenues: revenueValues(true), revenue_timing: byId("revenue-timing").value,
      monthly_rent: moneyInputValue("monthly-rent"), monthly_labor_cost: moneyInputValue("monthly-labor"),
      monthly_variable_cost: moneyInputValue("monthly-purchase"), expense_timing: byId("expense-timing").value,
      monthly_other_fixed_cost: moneyInputValue("monthly-other-fixed"),
      total_loan_balance: loanBalance, annual_interest_rate_percent: loanBalance ? numericValue("loan-rate") : 0,
      remaining_term_months: loanBalance ? numericValue("loan-term") : 1, debt_timing: byId("debt-timing").value,
    },
    existing_loan_rate_percent: loanBalance ? numericValue("loan-rate") : 0,
    existing_loan_term_months: loanBalance ? numericValue("loan-term") : 1,
    eligibility_profile: eligibilityProfilePayload(),
    policy_scenarios: policyScenarioPayload(),
  };
}

function comparisonCacheKey(body) {
  return JSON.stringify({ ...body, market_scenario: "all", goal: "all", situation_context: situationContextPayload() });
}

function situationContextPayload() {
  return state.situationContext ? { ...state.situationContext, signals: [...state.situationContext.signals] } : null;
}

function applyGoalRanking(data, goal = state.goal) {
  const ranking = data?.comparison_result?.goal_rankings?.[goal];
  if (!ranking) return data;
  Object.assign(data.comparison_result, ranking, { selected_goal: goal });
  return data;
}

async function runComparison(next = "diagnosis", navigate = true, manageLoading = true) {
  try { validateBusiness(); validateFinance(); } catch (error) { toast(error.message); return false; }
  const body = comparisonRequest();
  const cacheKey = comparisonCacheKey(body);
  const button = next === "diagnosis" ? byId("run-diagnosis") : byId("diagnosis-next");
  const original = button.textContent; button.disabled = true; button.textContent = "3개 범위 계산 중";
  if (manageLoading) showLoading("세 가지 매출 변화 범위의 현금흐름을 계산하고 있습니다.");
  try {
    await loadMarketScenarios();
    if (state.scenarioCacheKey !== cacheKey || !state.scenarioResults[state.scenario]) {
      const entries = await Promise.all(Object.keys(scenarioLabels).map(async (scenario) => [
        scenario,
        await api("/api/v4/orchestrate", { method: "POST", body: JSON.stringify({ comparison: { ...body, market_scenario: scenario }, answered_fields: Object.keys(state.eligibilityAnswers), asked_fields: state.v3AskedFields, situation_context: situationContextPayload(), question_round: state.questionBatchRound }) }),
      ]));
      state.scenarioResults = Object.fromEntries(entries.map(([scenario, result]) => [scenario, applyGoalRanking(result)]));
      state.scenarioCacheKey = cacheKey;
    }
    state.data = applyGoalRanking(state.scenarioResults[state.scenario]);
    state.conditionalPolicyIds = new Set(state.data?.v2?.conditional_policy_ids || []);
    if (state.questionWizardMode === "full") {
      const nextQuestions = state.data?.v3?.next_questions || (state.data?.v3?.next_question ? [state.data.v3.next_question] : []);
      state.questionWizardOrder = [];
      state.questionWizardIndex = 0;
      state.questionWizardComplete = !nextQuestions.length;
      state.questionWizardResultsVisible = !nextQuestions.length;
    }
    state.selectedAlternative = state.data.comparison_result.top_alternative_id;
    syncPolicySearchToAlternative(state.selectedAlternative);
    renderResults(); updateSummary(); if (navigate) showStep(next); return true;
  } catch (error) { toast(error.message); return false; }
  finally { if (manageLoading) hideLoading(); button.disabled = false; button.textContent = original; }
}

async function applyPreset(id) {
  const preset = presentationPresets[id];
  const area = state.areaPoints.find((item) => item.code === preset?.areaCode);
  const industry = state.industries.find((item) => item.code === "CS100001") || state.industries[0];
  if (!preset || !area || !industry) return toast("준비된 가게 상황을 불러오지 못했습니다.");
  state.data = null; state.marketScenarios = null; state.scenarioResults = {}; state.scenarioCacheKey = ""; state.selectedAlternative = null; state.focusedPolicyId = ""; state.selectedPolicyIds = new Set(); state.conditionalPolicyIds = new Set(); state.policySelectionInitialized = false; state.questionCatalog = {}; state.eligibilityAnswers = {}; state.policyScenarioValues = {}; state.actionBrief = null; state.questionWizardOrder = []; state.questionWizardAllOrder = []; state.questionWizardIndex = 0; state.questionWizardKey = ""; state.questionWizardComplete = false; state.questionWizardResultsVisible = false; state.questionWizardMode = "full"; state.questionWizardReturnPolicyId = ""; state.questionBatchRound = 0; state.v3AskedFields = []; state.policyScenarioEditorPolicyId = ""; state.costReductionEditorOpen = false; state.situationInterpretation = null; state.situationContext = null; state.pendingWhatIf = null; state.whatIfUndo = null; state.whatIfOriginalPrompt = ""; state.whatIfClarificationAttempts = 0;
  byId("v3-undo-what-if").hidden = true;
  byId("diagnosis-empty").hidden = false; byId("diagnosis-result").hidden = true; byId("decision-empty").hidden = false; byId("decision-result").hidden = true; byId("diagnosis-next").disabled = true;
  document.querySelectorAll("[data-goal-top]").forEach((node) => { node.textContent = "계산 전"; });
  document.querySelectorAll("[data-goal-value]").forEach((node) => { node.textContent = ""; });
  document.querySelectorAll("#scenario-options label b").forEach((node) => { node.textContent = "확인 중"; });
  selectArea(area.code, false, false, true, false);
  const major = industryMajor(industry.code); byId("industry-major-select").value = major; populateIndustries(major, industry.code);
  state.revenueMonths = preset.revenues.length; renderRevenueMonths(preset.revenues);
  [["opening-cash", preset.cash], ["monthly-rent", preset.rent], ["monthly-labor", preset.labor], ["monthly-purchase", preset.purchase], ["monthly-other-fixed", preset.other], ["loan-balance", preset.loan], ["loan-rate", preset.rate], ["loan-term", preset.term], ["reduce-rent", 0], ["reduce-labor", 0], ["reduce-purchase", 0], ["reduce-other", 0]].forEach(([field, value]) => { byId(field).value = value; });
  byId("revenue-timing").value = "daily"; byId("expense-timing").value = "early"; byId("debt-timing").value = "late";
  state.scenario = "central"; document.querySelector('input[name="market-scenario"][value="central"]').checked = true;
  document.querySelectorAll("[data-preset]").forEach((node) => node.classList.toggle("is-selected", node.dataset.preset === id));
  document.querySelectorAll("[data-situation-example]").forEach((node) => node.classList.remove("is-selected"));
  byId("v3-situation-text").value = "";
  byId("v3-situation-review").hidden = true;
  byId("v3-finance-context").hidden = true;
  byId("v3-situation-status").textContent = "발표용 빠른 시연은 준비된 숫자 입력을 사용합니다.";
  byId("preset-status").textContent = `${area.name} 상권과 6개월 재무정보를 채웠습니다. 2단계에서 현금 진단 보기를 누르면 계산을 시작합니다.`;
  updateConfirmedReduction(); updateScenarioApplicationStatus(); updateSummary();
  toast("6개월 입력을 채웠습니다. 재무 입력에서 현금 진단을 시작하세요.");
}

async function runCsvBaseline() {
  const events = byId("events-file").files[0], loans = byId("loans-file").files[0];
  if (!events) return toast("거래내역 파일을 선택해 주세요.");
  if (!byId("csv-reference").value || byId("csv-opening").value === "") return toast("파일 기준일과 현재 현금을 입력해 주세요.");
  try {
    const payload = await api("/api/v1/cashflow/csv", { method: "POST", body: JSON.stringify({ reference_date: byId("csv-reference").value, opening_cash: moneyInputValue("csv-opening"), safe_cash_threshold: 0, events_csv: await events.text(), loans_csv: loans ? await loans.text() : "" }) });
    const baseline = payload.baseline_cashflow;
    byId("csv-status").textContent = `파일 계산 완료: 13주 뒤 ${compactMoney(baseline.weekly_summary.ending_cash)}, 6개월 뒤 ${compactMoney(baseline.monthly_summary.ending_cash)}. 정책 대안 비교에는 위 간편 입력도 완료해 주세요.`;
  } catch (error) { byId("csv-status").textContent = error.message; }
}

function scenarioComparison() { return state.data?.market_scenario_comparison || []; }
function scenarioValuesDiffer(selector) { const values = scenarioComparison().map(selector); return new Set(values.map((value) => String(value))).size > 1; }
function renderResults() {
  byId("diagnosis-empty").hidden = true; byId("diagnosis-result").hidden = false; byId("decision-empty").hidden = true; byId("decision-result").hidden = false; byId("diagnosis-next").disabled = !state.questionWizardResultsVisible;
  const inputBaseline = state.data.baseline_cashflow;
  const baselineAlternative = state.data.intervention_results.find((item) => item.alternative_id === "no_action" && item.metrics);
  const week13EndingCash = baselineAlternative?.metrics?.week13_ending_cash ?? inputBaseline.weekly_summary.ending_cash;
  const month6EndingCash = baselineAlternative?.metrics?.month6_ending_cash ?? inputBaseline.monthly_summary.ending_cash;
  const safeCash = state.data.safe_cash.suggested_amount;
  renderStoreSignals();
  updateScenarioApplicationStatus();
  const week13Changes = scenarioValuesDiffer((item) => item.week13_ending_cash);
  const month6Changes = scenarioValuesDiffer((item) => item.month6_ending_cash);
  const metrics = [
    ["현재 보유 현금", compactMoney(inputBaseline.weekly_13[0]?.opening_cash ?? state.data.baseline_input.opening_cash), "", false],
    ["앞으로 28일 필요현금", compactMoney(safeCash), "", false],
    ["13주 뒤 현금", compactMoney(week13EndingCash), "", week13Changes],
  ];
  byId("diagnosis-metrics").innerHTML = metrics.map(([label, value, note, changes]) => `<div class="metric ${changes ? "is-scenario-sensitive" : "is-fixed"}"><span>${label}</span><strong>${escapeHtml(value)}</strong>${note ? `<small>${escapeHtml(note)}</small>` : ""}</div>`).join("");
  byId("six-month-summary").innerHTML = `<dt>현금 잔액</dt><dd class="${month6Changes ? "is-scenario-sensitive" : ""}">${compactMoney(month6EndingCash)}</dd><dt>남은 대출</dt><dd>${compactMoney(inputBaseline.debt_summary.remaining_principal_at_6_months)}</dd><dt>만기까지 총이자</dt><dd>${compactMoney(baselineAlternative?.metrics?.total_interest_through_maturity ?? inputBaseline.debt_summary.total_interest_through_maturity)}</dd>`;
  renderPolicyFocus(); renderPolicyDiscovery(); renderCharts();
}

function renderStoreSignals() {
  const revenues = revenueValues(false);
  let storeText = "추세 확인 필요";
  if (revenues.length >= 2 && revenues[revenues.length - 1] > 0) {
    const change = (revenues[0] - revenues[revenues.length - 1]) / revenues[revenues.length - 1] * 100;
    const direction = change <= -10 ? "감소 흐름" : change >= 10 ? "증가 흐름" : "대체로 보합";
    storeText = `${direction} · ${formatPercent(change)}`;
  }
  byId("store-trend-value").textContent = storeText;
  byId("market-outlook-value").textContent = selectedScenarioSummary();
}

function orderedQuestionOptions(question) {
  const options = [...(question.options || [])];
  if (question.input_type !== "tri_state") return options;
  const order = new Map([["no", 0], ["unknown", 1], ["yes", 2]]);
  return options.sort((left, right) => (order.get(left.value) ?? 9) - (order.get(right.value) ?? 9));
}

function initializeQuestionWizard(questions) {
  questions.forEach((item) => { state.questionCatalog[item.field] = item; });
  const adaptiveBatch = state.data?.v3?.next_questions || (state.data?.v3?.next_question ? [state.data.v3.next_question] : []);
  if (state.data?.v3 && state.questionWizardMode === "full") {
    if (!adaptiveBatch.length) {
      state.questionWizardOrder = [];
      state.questionWizardComplete = true;
      state.questionWizardResultsVisible = true;
      return;
    }
    adaptiveBatch.forEach((question) => { state.questionCatalog[question.field] = question; });
    const fields = adaptiveBatch.map((question) => question.field);
    state.questionWizardKey = `v3:${state.questionBatchRound}:${fields.join("|")}`;
    state.questionWizardOrder = fields;
    fields.forEach((field) => { if (!state.questionWizardAllOrder.includes(field)) state.questionWizardAllOrder.push(field); });
    state.questionWizardIndex = 0;
    state.questionWizardComplete = false;
    state.questionWizardResultsVisible = false;
    return;
  }
  if (state.questionWizardOrder.length) return;
  const ordered = [...questions].sort((left, right) => {
    const coverage = (right.policy_ids || []).length - (left.policy_ids || []).length;
    if (coverage) return coverage;
    const typeOrder = { tri_state: 0, select: 1, date: 2, number: 3 };
    return (typeOrder[left.input_type] ?? 9) - (typeOrder[right.input_type] ?? 9);
  });
  const key = ordered.map((item) => item.field).join("|");
  if (state.questionWizardKey === key) return;
  state.questionWizardKey = key;
  state.questionWizardOrder = ordered.map((item) => item.field);
  state.questionWizardAllOrder = [...state.questionWizardOrder];
  state.questionWizardIndex = 0;
  state.questionWizardComplete = false;
}

function currentWizardQuestion() {
  return state.questionCatalog[state.questionWizardOrder[state.questionWizardIndex]] || null;
}

function wizardQuestionControl(question) {
  const current = state.eligibilityAnswers[question.field] ?? "unknown";
  if (["tri_state", "select"].includes(question.input_type)) {
    const options = orderedQuestionOptions(question).map((item) => `<button type="button" class="question-choice ${item.value === current ? "is-selected" : ""}" data-question-choice="${escapeHtml(question.field)}" data-question-value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</button>`).join("");
    return `<div class="question-choice-grid ${question.input_type === "tri_state" ? "is-three-way" : ""}" role="group" aria-label="${escapeHtml(question.label)} 답변">${options}</div>`;
  }
  const type = question.input_type === "number" ? "number" : "date";
  const attributes = type === "number" ? 'min="0" step="1" inputmode="numeric"' : "";
  const value = current === "unknown" ? "" : current;
  const nextLabel = state.questionWizardIndex >= state.questionWizardOrder.length - 1 ? "이 묶음 답변 반영" : "다음 질문";
  return `<div class="question-value-entry"><input type="${type}" ${attributes} data-question-entry="${escapeHtml(question.field)}" value="${escapeHtml(value)}"><button type="button" class="secondary" data-question-unknown="${escapeHtml(question.field)}">모름</button><button type="button" class="primary" data-question-next>${nextLabel}</button></div>`;
}

function renderQuestionWizard() {
  const form = byId("policy-question-form");
  const complete = byId("policy-question-complete");
  const progress = byId("policy-question-progress");
  const back = byId("policy-question-back");
  const total = state.questionWizardOrder.length;
  if (!total || state.questionWizardComplete) {
    form.hidden = true;
    complete.hidden = false;
    progress.textContent = total ? `질문 ${total}개 응답 완료` : "추가 질문 없음";
    back.disabled = true;
    byId("policy-question-complete-summary").textContent = total ? `답변 ${total}개를 한꺼번에 반영해 정책 후보를 다시 확인합니다.` : "현재 입력에서 추가로 확인할 질문이 없습니다.";
    return;
  }
  const question = currentWizardQuestion();
  if (!question) return;
  form.hidden = false;
  complete.hidden = true;
  const roundLabel = state.questionWizardMode === "targeted" ? "답변 수정" : state.questionBatchRound === 0 ? "1차 핵심 질문" : "추가 질문";
  progress.textContent = `${roundLabel} ${state.questionWizardIndex + 1} / ${total}`;
  back.disabled = state.questionWizardIndex === 0;
  form.innerHTML = `<article class="question-wizard-card" aria-labelledby="current-policy-question"><p class="question-wizard-kicker">질문은 하나씩 보여주고, 이 묶음의 답변은 마지막에 한 번만 반영합니다</p><h3 id="current-policy-question">${escapeHtml(question.label)}</h3><p>${escapeHtml(question.reason)}</p><small>${escapeHtml(question.selection_reason || question.impact)}</small>${wizardQuestionControl(question)}</article>`;
  form.querySelector("button:not([disabled]), input")?.focus({ preventScroll: true });
}

async function finishQuestionWizard() {
  const returnToDecision = state.questionWizardMode === "targeted";
  const returnPolicyId = state.questionWizardReturnPolicyId;
  state.questionWizardComplete = true;
  renderQuestionWizard();
  const previousRound = state.questionBatchRound;
  if (!returnToDecision) state.questionBatchRound = Math.min(2, state.questionBatchRound + 1);
  const success = await runComparison("diagnosis", false);
  if (!success) {
    state.questionBatchRound = previousRound;
    state.questionWizardComplete = false;
    renderQuestionWizard();
    return;
  }
  const nextBatch = state.data?.v3?.next_questions || (state.data?.v3?.next_question ? [state.data.v3.next_question] : []);
  if (!returnToDecision && nextBatch.length) {
    state.questionWizardComplete = false;
    renderPolicyDiscovery();
    byId("policy-questionnaire").scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  state.questionWizardResultsVisible = true;
  if (returnToDecision) {
    const previousConditionalIds = new Set(state.conditionalPolicyIds);
    enableSelectedPolicyPreviews();
    const addedPreview = [...state.conditionalPolicyIds].some((id) => !previousConditionalIds.has(id));
    if (addedPreview && !await runComparison("decision", false)) return;
    state.questionWizardMode = "full";
    state.questionWizardReturnPolicyId = "";
    state.questionWizardOrder = [...state.questionWizardAllOrder];
    if (returnPolicyId) {
      focusPolicy(returnPolicyId, false);
      await loadV4ApplicationPlan(returnPolicyId);
      showStep("preparation");
    } else {
      showStep("decision");
    }
    return;
  }
  renderPolicyDiscovery();
  byId("diagnosis-next").disabled = false;
  byId("policy-results").scrollIntoView({ behavior: "smooth", block: "start" });
}

function advanceQuestionWizard() {
  if (state.questionWizardIndex >= state.questionWizardOrder.length - 1) {
    finishQuestionWizard();
    return;
  }
  state.questionWizardIndex += 1;
  renderQuestionWizard();
}

function answerWizardQuestion(field, value) {
  state.eligibilityAnswers[field] = value || "unknown";
  if (!state.v3AskedFields.includes(field)) state.v3AskedFields.push(field);
  state.scenarioCacheKey = "";
  state.actionBrief = null;
  advanceQuestionWizard();
}

function previousWizardQuestion() {
  if (state.questionWizardIndex > 0) state.questionWizardIndex -= 1;
  state.questionWizardComplete = false;
  renderQuestionWizard();
}

function reviewWizardAnswers(fields = null, policyId = "") {
  const targetFields = fields ? [...new Set(fields)].filter((field) => state.questionCatalog[field]) : [];
  if (fields && !targetFields.length) {
    toast("이 항목은 화면 답변이 아니라 공식기관 확인이 필요합니다.");
    return;
  }
  state.questionWizardResultsVisible = false;
  state.questionWizardMode = targetFields.length ? "targeted" : "full";
  state.questionWizardReturnPolicyId = targetFields.length ? policyId : "";
  state.questionWizardOrder = targetFields.length ? targetFields : [...state.questionWizardAllOrder];
  state.questionWizardIndex = 0;
  state.questionWizardComplete = false;
  state.policyScenarioEditorPolicyId = "";
  state.costReductionEditorOpen = false;
  renderPolicyDiscovery();
}

function scenarioField(policyId, field, label, type = "text", suffix = "") {
  const value = state.policyScenarioValues[policyId]?.[field] ?? "";
  const attrs = type === "number" ? 'min="0" step="1" inputmode="numeric"' : "";
  return `<label>${escapeHtml(label)}<span class="${suffix ? "money-input" : ""}"><input type="${type}" ${attrs} value="${escapeHtml(value)}" data-policy-scenario="${escapeHtml(policyId)}" data-scenario-field="${escapeHtml(field)}">${suffix ? `<b>${escapeHtml(suffix)}</b>` : ""}</span></label>`;
}

function renderPolicyScenarios() {
  const cards = [];
  const policyId = state.policyScenarioEditorPolicyId;
  if (policyId === "POL_SEOUL_CRISIS_TRACK2_2026H2") cards.push(`<article class="policy-scenario-card"><strong>위기 소상공인 지원 상세 계산</strong><div class="form-grid">${scenarioField(policyId, "amount", "계획 중인 지원 신청액", "number", "만원")}${scenarioField(policyId, "expenseAmount", "계획 중인 선지출액", "number", "만원")}${scenarioField(policyId, "expenseDate", "계획 중인 선지출일", "date")}${scenarioField(policyId, "paymentDate", "확인한 지급 예정일", "date")}</div><p class="field-help">공고상 최대 300만원 범위입니다. 값이 모두 있어야 조건부 현금 대안을 만들며 승인 가능성을 뜻하지 않습니다.</p></article>`);
  if (policyId === "POL_SEMAS_EMPLOYMENT_INSURANCE_2026") cards.push(`<article class="policy-scenario-card"><strong>자영업자 고용보험료 지원 상세 계산</strong><div class="form-grid"><label>확인한 기준보수 등급<select data-policy-scenario="${policyId}" data-scenario-field="grade"><option value="">선택</option>${Array.from({length:7},(_,index)=>`<option value="${index + 1}" ${String(state.policyScenarioValues[policyId]?.grade) === String(index + 1) ? "selected" : ""}>${index + 1}등급</option>`).join("")}</select></label><label>보험료가 현재 월 지출에 포함됐나요?<select data-policy-scenario="${policyId}" data-scenario-field="inBaseline"><option value="">선택</option><option value="true" ${state.policyScenarioValues[policyId]?.inBaseline === "true" ? "selected" : ""}>예</option><option value="false" ${state.policyScenarioValues[policyId]?.inBaseline === "false" ? "selected" : ""}>아니오</option></select></label></div></article>`);
  if (policyId === "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026") cards.push(`<article class="policy-scenario-card"><strong>가족친화 기업지원금 상세 계산</strong><div class="form-grid">${scenarioField(policyId, "amount", "확인한 신청 예정액", "number", "만원")}${scenarioField(policyId, "paymentDate", "확인한 지급 예정일", "date")}</div><p class="field-help">공고상 최대 비교액은 450만원입니다. 실제 사업주 부담액과 지급 차수를 확인한 경우에만 사용하세요.</p></article>`);
  byId("policy-scenario-form").innerHTML = cards.join("") || '<p class="field-help">이 정책은 현재 상세 현금 계산용 금액·날짜 구조가 없습니다. 공식 공고와 상담기관에서 다음 행동을 확인해 주세요.</p>';
}

function baselineCashNeed() {
  const baseline = state.data?.intervention_results?.find((item) => item.alternative_id === "no_action" && item.metrics);
  const safeCash = Number(state.data?.safe_cash?.suggested_amount || 0);
  return Math.max(0, safeCash - Number(baseline?.metrics?.week13_minimum_cash || 0));
}

function renderPolicyCashNeed() {
  const amount = baselineCashNeed();
  byId("policy-cash-need-value").textContent = compactMoney(amount);
  byId("policy-cash-need-explanation").textContent = amount > 0
    ? "현금이 가장 낮은 주에도 앞으로 28일 필요현금을 유지하기 위한 차액입니다. 대출 권장액이나 승인금액이 아닙니다."
    : "현재 선택한 상권 범위에서는 13주 동안 앞으로 28일 필요현금 기준을 유지합니다.";
}

function policyFundingText(policyId) {
  const guidance = policyFundingGuidance[policyId];
  if (!guidance) return "공식 지원 범위와 금융조건을 공고에서 확인해야 합니다.";
  const cashNeed = baselineCashNeed();
  if (!guidance.maximumAmount || cashNeed <= 0) return guidance.terms;
  return `${guidance.terms} 현재 계산된 추가 필요 현금은 ${compactMoney(cashNeed)}이며, 실제 인정액과 지급일이 확인되기 전에는 현금 유입으로 계산하지 않습니다.`;
}

function openPolicyScenarioEditor(policyId) {
  if (!policyScenarioSupported.has(policyId)) return;
  if (!state.selectedPolicyIds.has(policyId)) {
    if (state.selectedPolicyIds.size >= 3) return toast("상세 계산할 정책을 선택하려면 기존 선택을 하나 해제해 주세요.");
    state.selectedPolicyIds.add(policyId);
  }
  state.policyScenarioEditorPolicyId = policyId;
  state.scenarioCacheKey = "";
  state.actionBrief = null;
  renderPolicyDiscovery();
  byId("policy-scenario-inputs").scrollIntoView({ behavior: "smooth", block: "start" });
}

function closePolicyScenarioEditor() {
  state.policyScenarioEditorPolicyId = "";
  renderPolicyDiscovery();
}

function setCostReductionEditor(open) {
  state.costReductionEditorOpen = open;
  renderPolicyDiscovery();
  if (open) byId("cost-reduction-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderPolicyDiscovery() {
  const discovery = state.data?.policy_discovery;
  if (!discovery) return;
  if (state.questionWizardResultsVisible) {
    renderPolicyResults(discovery);
    return;
  }
  byId("policy-questionnaire").hidden = false;
  byId("policy-results").hidden = true;
  byId("policy-cash-need").hidden = true;
  byId("optional-comparison-tools").hidden = true;
  byId("policy-scenario-inputs").hidden = true;
  byId("cost-reduction-panel").hidden = true;
  byId("policy-refresh-actions").hidden = true;
  byId("diagnosis-next").disabled = true;
  initializeQuestionWizard(discovery.staged_questions || []);
  if (!state.questionWizardOrder.length) {
    state.questionWizardComplete = true;
    state.questionWizardResultsVisible = true;
    renderPolicyResults(discovery);
    return;
  }
  renderQuestionWizard();
}

function renderPolicyResults(discovery) {
  byId("policy-questionnaire").hidden = true;
  byId("policy-results").hidden = false;
  byId("policy-cash-need").hidden = false;
  byId("optional-comparison-tools").hidden = false;
  byId("policy-scenario-inputs").hidden = !state.policyScenarioEditorPolicyId;
  byId("cost-reduction-panel").hidden = !state.costReductionEditorOpen;
  byId("policy-refresh-actions").hidden = !state.policyScenarioEditorPolicyId && !state.costReductionEditorOpen;
  byId("open-cost-reduction").setAttribute("aria-expanded", String(state.costReductionEditorOpen));
  renderPolicyCashNeed();
  byId("situation-labels").innerHTML = (discovery.situation_labels || []).map((label) => `<span>${escapeHtml(humanizeText(label))}</span>`).join("");
  (discovery.staged_questions || []).forEach((item) => { state.questionCatalog[item.field] = item; });
  const allCandidates = (discovery.candidates || []).filter((item) => Object.hasOwn(financialPolicyNeeds, item.policy_id));
  if (!state.policySelectionInitialized) {
    state.policySelectionInitialized = true;
  }
  const selectedCandidates = allCandidates.filter((item) => state.selectedPolicyIds.has(item.policy_id));
  const candidates = [...allCandidates.slice(0, 3), ...selectedCandidates].filter((item, index, items) => items.findIndex((other) => other.policy_id === item.policy_id) === index).slice(0, 3);
  byId("policy-discovery-status").textContent = `${allCandidates.length}개 후보 중 우선순위 ${candidates.length}개를 보여줍니다. 현재 ${state.selectedPolicyIds.size}개 선택.`;
  const card = (item) => {
    const readiness = item.application_readiness || {};
    const readinessItems = readiness.next_actions || [];
    const isConditional = state.conditionalPolicyIds.has(item.policy_id);
    const simulationButton = policyScenarioSupported.has(item.policy_id) ? `<button type="button" class="secondary" data-open-policy-scenario="${escapeHtml(item.policy_id)}">상세 현금 영향 계산</button>` : "";
    return `<article class="policy-discovery-card ${state.selectedPolicyIds.has(item.policy_id) ? "is-selected" : ""}"><div><label class="policy-select"><input type="checkbox" data-policy-select="${escapeHtml(item.policy_id)}" ${state.selectedPolicyIds.has(item.policy_id) ? "checked" : ""}> 확인할 정책으로 선택</label><span class="policy-readiness">${escapeHtml(readiness.status || item.eligibility_readiness)}</span><h4>${escapeHtml(item.policy_name)}</h4><p>${escapeHtml(policyCardSummaries[item.policy_id] || "정책의 지원 내용을 공식 공고에서 확인해 주세요.")}</p><p class="policy-funding"><strong>공식 지원 범위</strong> ${escapeHtml(policyFundingText(item.policy_id))}</p><p class="policy-why"><strong>내 상황과 연결된 이유</strong> ${escapeHtml(humanizeText(item.match_reason || "현재 점포 조건과 정책 목적이 연결되었습니다. 지원 대상 확정은 아닙니다."))}</p><div class="application-readiness"><strong>${escapeHtml(readiness.status || "공식 확인 필요")}</strong>${readinessItems.length ? `<ol>${readinessItems.map((action) => `<li>${escapeHtml(humanizeText(action))}</li>`).join("")}</ol>` : ""}</div><p class="policy-impact-note"><strong>${isConditional ? "조건부 현금 그래프 사용 중" : "확정 현금 영향 미산정"}</strong> ${isConditional ? "표시된 가정으로만 계산한 점선이며 추천 순위에는 넣지 않습니다." : "실제 금액과 지급일이 정해지기 전에는 확정 숫자 순위에 넣지 않습니다."}</p></div><div class="policy-card-actions"><a href="${safeUrl(item.official_url)}" target="_blank" rel="noreferrer">공고 보기</a>${simulationButton}</div></article>`;
  };
  byId("policy-discovery-cards").innerHTML = candidates.length ? candidates.map(card).join("") : '<p class="field-help">현재 답변에서 바로 확인할 금융 정책을 찾지 못했습니다.</p>';
  renderPolicyScenarios();
  byId("diagnosis-next").disabled = false;
}

function humanizeText(value) {
  let text = String(value ?? "");
  Object.entries(policyNames).forEach(([id, label]) => { text = text.replaceAll(id, label); });
  return text.replaceAll("동시수혜 공식 근거 확인 필요", "두 지원을 함께 받을 수 있는지 공식기관에 확인해 주세요").replaceAll("공식 근거 확인 필요", "최신 지원 조건을 공식기관에 확인해 주세요").replaceAll("Track2", "위기 소상공인 지원").replaceAll("안전현금", "28일 필요현금");
}
function enableSelectedPolicyPreviews() {
  const candidates = state.data?.policy_discovery?.candidates || [];
  candidates.forEach((item) => {
    if (state.selectedPolicyIds.has(item.policy_id) && item.application_readiness?.conditional_graph_supported) {
      state.conditionalPolicyIds.add(item.policy_id);
    } else {
      state.conditionalPolicyIds.delete(item.policy_id);
    }
  });
  state.scenarioCacheKey = "";
}

function policyFocusCandidates() {
  return (state.data?.policy_discovery?.candidates || []).filter((item) => state.selectedPolicyIds.has(item.policy_id));
}

function policyAlternative(candidate) {
  const alternativeId = conditionalAlternativeByPolicy[candidate?.policy_id];
  return state.data?.intervention_results?.find((item) => item.alternative_id === alternativeId && item.metrics) || null;
}

function signedMoney(value) {
  if (value == null) return "효과 미산정";
  return `${value > 0 ? "+" : ""}${compactMoney(value)}`;
}

function focusPolicy(policyId, updateChart = true) {
  const candidates = policyFocusCandidates();
  if (!candidates.some((item) => item.policy_id === policyId)) return;
  state.focusedPolicyId = policyId;
  const alternative = policyAlternative(candidates.find((item) => item.policy_id === policyId));
  state.selectedAlternative = alternative?.alternative_id || "no_action";
  syncPolicySearchToAlternative(state.selectedAlternative);
  renderPolicyFocus();
  if (updateChart) renderCharts();
}

function renderPolicyFocus() {
  const section = byId("v4-policy-focus");
  const candidates = policyFocusCandidates();
  section.hidden = false;
  if (!candidates.length) {
    state.focusedPolicyId = "";
    byId("v4-policy-focus-title").textContent = "비교할 정책을 먼저 선택해 주세요";
    byId("v4-policy-position").textContent = "3단계에서 최대 3개 정책을 고를 수 있습니다.";
    byId("v4-policy-tabs").innerHTML = "";
    byId("v4-policy-focus-content").innerHTML = '<div class="empty-state"><p>정책을 선택하면 무대응 대비 효과와 신청 준비 경로가 여기에 표시됩니다.</p><button type="button" class="primary" data-step="diagnosis">정책 선택으로 돌아가기</button></div>';
    byId("v4-policy-deltas").innerHTML = '<p>선택한 정책이 없어 무대응 기준선만 표시합니다.</p>';
    byId("v4-policy-prev").disabled = true;
    byId("v4-policy-next").disabled = true;
    return;
  }
  if (!candidates.some((item) => item.policy_id === state.focusedPolicyId)) state.focusedPolicyId = candidates[0].policy_id;
  const candidate = candidates.find((item) => item.policy_id === state.focusedPolicyId);
  const index = candidates.indexOf(candidate);
  const readiness = candidate.application_readiness || {};
  const baseline = state.data.intervention_results.find((item) => item.alternative_id === "no_action" && item.metrics);
  const alternative = policyAlternative(candidate);
  const visibleAlternativeIds = new Set(["no_action", ...candidates.map((item) => conditionalAlternativeByPolicy[item.policy_id]).filter(Boolean)]);
  if (!visibleAlternativeIds.has(state.selectedAlternative)) state.selectedAlternative = alternative?.alternative_id || "no_action";
  const week13Delta = alternative && baseline ? alternative.metrics.week13_ending_cash - baseline.metrics.week13_ending_cash : null;
  const debtDelta = alternative && baseline ? alternative.metrics.net_new_borrowing - baseline.metrics.net_new_borrowing : null;
  const paymentDelta = alternative && baseline ? alternative.metrics.maximum_monthly_debt_service - baseline.metrics.maximum_monthly_debt_service : null;
  const structural = readiness.conditional_graph_status === "structural_block";
  const calculationUnavailable = readiness.conditional_graph_status === "calculation_unavailable" || !alternative;
  const status = structural ? "현재 입력 기준 지원 어려움" : calculationUnavailable ? "효과 계산 조건 확인 필요" : "조건부 효과 비교 가능";
  const explanation = structural
    ? readiness.conditional_graph_reason || "앞에서 입력한 조건에 지원 제외 사유가 있습니다. 잘못 입력했다면 5단계에서 답변을 수정할 수 있습니다."
    : calculationUnavailable
    ? readiness.conditional_graph_reason || "공식 금액이나 현재 재무조건이 부족해 임의의 효과를 만들지 않았습니다. 신청 가능 여부와는 별개입니다."
    : "현재 입력과 검수된 정책 가정으로 계산한 효과입니다. 실제 지원 여부와 금액은 공식 심사에서 정해집니다.";
  byId("v4-policy-focus-title").textContent = candidate.policy_name;
  byId("v4-policy-position").textContent = `${index + 1} / ${candidates.length} 정책`;
  byId("v4-policy-prev").disabled = candidates.length < 2;
  byId("v4-policy-next").disabled = candidates.length < 2;
  byId("v4-policy-tabs").innerHTML = candidates.map((item, itemIndex) => `<button type="button" role="tab" data-focus-policy="${escapeHtml(item.policy_id)}" aria-selected="${item.policy_id === candidate.policy_id}" class="${item.policy_id === candidate.policy_id ? "is-selected" : ""}">${itemIndex + 1}. ${escapeHtml(item.policy_name)}</button>`).join("");
  byId("v4-policy-focus-content").innerHTML = `<div class="v4-policy-summary"><span class="v4-policy-status ${structural ? "is-blocked" : calculationUnavailable ? "is-check" : "is-ready"}">${escapeHtml(status)}</span><p>${escapeHtml(policyCardSummaries[candidate.policy_id] || policyFundingText(candidate.policy_id))}</p><p class="v4-policy-explanation">${escapeHtml(explanation)}</p></div><div class="v4-policy-metrics"><div><span>13주 뒤 현금 차이</span><strong>${signedMoney(week13Delta)}</strong></div><div><span>새로 생기는 빚 차이</span><strong>${signedMoney(debtDelta)}</strong></div><div><span>월 최대상환 변화</span><strong>${signedMoney(paymentDelta)}</strong></div></div><button type="button" class="primary v4-policy-cta" data-v4-start-application="${escapeHtml(candidate.policy_id)}">${structural ? "지원이 어려운 이유와 입력 확인" : "이 정책 신청 준비로 이동"}</button>`;
  byId("v4-policy-deltas").innerHTML = candidates.map((item) => {
    const itemAlternative = policyAlternative(item);
    const delta = itemAlternative && baseline ? itemAlternative.metrics.week13_ending_cash - baseline.metrics.week13_ending_cash : null;
    return `<button type="button" data-focus-policy="${escapeHtml(item.policy_id)}" class="${item.policy_id === candidate.policy_id ? "is-selected" : ""}"><span>${escapeHtml(item.policy_name)}</span><strong>${signedMoney(delta)}</strong><small>13주 뒤 현금 차이</small></button>`;
  }).join("");
}

function alternativeReadiness(item) {
  const plan = state.data?.execution_plan?.find((entry) => entry.alternative_id === item.alternative_id);
  const checks = [...(item.items_to_confirm || []), ...(plan?.conditions_to_check_now || [])].filter(Boolean);
  if (!item.ranking_eligible || checks.length || Number(item.metrics?.confirmation_item_count || 0) > 0) {
    return { className: "is-check", label: "자격·접수 추가 확인" };
  }
  return { className: "is-ready", label: "바로 비교 가능" };
}

function canvasSetup(canvas) {
  const ratio = window.devicePixelRatio || 1, width = Math.max(320, canvas.getBoundingClientRect().width || 900), height = Math.max(280, Math.min(480, width * .45));
  canvas.width = width * ratio; canvas.height = height * ratio;
  const context = canvas.getContext("2d"); context.scale(ratio, ratio); return { context, width, height };
}
function drawChart(canvas, series, safeCash = null, interactive = false) {
  if (!canvas || !series.length || !series[0].values.length || canvas.offsetParent === null) return;
  const { context: ctx, width, height } = canvasSetup(canvas), css = getComputedStyle(document.documentElement);
  const colors = { text: css.getPropertyValue("--muted").trim(), line: css.getPropertyValue("--line").trim(), warning: css.getPropertyValue("--warning").trim(), danger: css.getPropertyValue("--danger").trim() };
  const pad = { left: 82, right: 20, top: 30, bottom: 50 }, all = series.flatMap((item) => item.values).concat(safeCash == null ? [] : [safeCash]);
  let min = Math.min(0, ...all), max = Math.max(0, ...all); if (min === max) max += 1;
  const x = (i) => pad.left + i * (width - pad.left - pad.right) / Math.max(1, series[0].values.length - 1);
  const y = (v) => pad.top + (max - v) * (height - pad.top - pad.bottom) / (max - min);
  ctx.clearRect(0, 0, width, height); ctx.font = "12px system-ui"; ctx.fillStyle = colors.text; ctx.strokeStyle = colors.line; ctx.lineWidth = 1;
  let shortfallLabel = null;
  if (safeCash != null && safeCash > 0) {
    const safeTop = y(safeCash), zeroLine = y(0), bandTop = Math.min(safeTop, zeroLine), bandHeight = Math.abs(zeroLine - safeTop);
    ctx.fillStyle = "rgba(180,140,35,.10)";
    ctx.fillRect(pad.left, bandTop, width - pad.left - pad.right, bandHeight);
    if (bandHeight >= 24) shortfallLabel = { x: pad.left + 10, y: bandTop + 18 };
  }
  const zeroTolerance = Math.max(1, (max - min) * .12);
  const gridValues = [];
  for (let i = 0; i <= 4; i += 1) { const value = min + (max - min) * i / 4; if (value > zeroTolerance) gridValues.push(value); }
  if (min < 0) {
    gridValues.push(min);
    const negativeSpan = Math.abs(y(min) - y(0));
    const negativeGuideCount = negativeSpan >= 150 ? 2 : 1;
    for (let i = 1; i <= negativeGuideCount; i += 1) gridValues.push(min * i / (negativeGuideCount + 1));
  }
  [...new Set(gridValues.map((value) => Math.round(value)))].sort((a, b) => b - a).forEach((value) => { const py = y(value); ctx.strokeStyle = colors.line; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad.left, py); ctx.lineTo(width - pad.right, py); ctx.stroke(); ctx.fillStyle = colors.text; ctx.textAlign = "left"; ctx.fillText(`${Math.round(value / 10000).toLocaleString("ko-KR")}만`, 25, py + 4); });
  const zeroY = y(0); ctx.strokeStyle = colors.text; ctx.globalAlpha = .8; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(pad.left, zeroY); ctx.lineTo(width - pad.right, zeroY); ctx.stroke(); ctx.globalAlpha = 1; ctx.fillStyle = colors.text; ctx.textAlign = "left"; ctx.font = "700 12px system-ui"; ctx.fillText("0만원", 25, zeroY + (zeroY < pad.top + 14 ? 14 : -7)); ctx.font = "12px system-ui";
  ctx.save(); ctx.translate(14, height / 2); ctx.rotate(-Math.PI / 2); ctx.fillStyle = colors.text; ctx.textAlign = "center"; ctx.fillText("현금 잔액(만원)", 0, 0); ctx.restore();
  canvas._seriesHit = [];
  series.forEach((item) => { const points = item.values.map((value, index) => ({ x: x(index), y: y(value) })); ctx.strokeStyle = item.color; ctx.globalAlpha = item.opacity ?? 1; ctx.lineWidth = item.width || 3; ctx.lineCap = "round"; ctx.setLineDash(item.dash || []); ctx.beginPath(); points.forEach((point, index) => index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y)); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1; if (interactive && item.id) canvas._seriesHit.push({ id: item.id, points }); });
  if (shortfallLabel) { ctx.fillStyle = colors.warning; ctx.textAlign = "left"; ctx.font = "700 12px system-ui"; ctx.fillText("28일 필요현금 미달 구간", shortfallLabel.x, shortfallLabel.y); }
  if (min < 0 && zeroY < height - pad.bottom - 18) { ctx.fillStyle = colors.danger; ctx.textAlign = "left"; ctx.font = "700 12px system-ui"; ctx.fillText("현금 적자 구간", pad.left + 10, zeroY + 18); }
  ctx.font = "12px system-ui";
  ctx.fillStyle = colors.text; ctx.textAlign = "center"; series[0].values.forEach((_, index) => { if (index === 0 || index === series[0].values.length - 1 || index % 2 === 0) ctx.fillText(`${index + 1}주`, x(index), height - 22); });
}
function renderCharts() {
  if (!state.data) return;
  const styles = getComputedStyle(document.documentElement), accent = styles.getPropertyValue("--accent").trim(), hoverColor = styles.getPropertyValue("--map-accent").trim();
  const allAlternatives = state.data.intervention_results.filter((item) => item.metrics);
  const baseline = allAlternatives.find((item) => item.alternative_id === "no_action");
  const selectedAlternativeIds = new Set(policyFocusCandidates().map((item) => conditionalAlternativeByPolicy[item.policy_id]).filter(Boolean));
  const alternatives = allAlternatives.filter((item) => item.alternative_id === "no_action" || selectedAlternativeIds.has(item.alternative_id));
  const comparisons = scenarioComparison();
  const scenarioSeries = comparisons.length ? comparisons.map((item) => {
    const isSelected = item.scenario === state.scenario, isHovered = item.scenario === state.hoveredScenario;
    return { id: item.scenario, label: scenarioLabels[item.scenario], color: isHovered ? hoverColor : isSelected ? accent : "#7f8984", opacity: isHovered ? 1 : isSelected ? .85 : .38, width: isHovered ? 5 : isSelected ? 4 : 2, dash: item.scenario === "downside" ? [8, 5] : item.scenario === "recovery" ? [2, 5] : [], values: item.weekly_13.map((week) => week.closing_cash) };
  }).sort((left, right) => Number(left.id === state.scenario) + Number(left.id === state.hoveredScenario) - Number(right.id === state.scenario) - Number(right.id === state.hoveredScenario)) : [{ label: scenarioLabels[state.scenario], color: accent, values: (baseline?.weekly_13 || state.data.baseline_cashflow.weekly_13).map((item) => item.closing_cash) }];
  byId("scenario-chart-legend").innerHTML = (comparisons.length ? comparisons : [{ scenario: state.scenario }]).map((item) => `<button type="button" data-select-scenario="${escapeHtml(item.scenario)}" class="${item.scenario === state.scenario ? "is-selected" : ""} ${item.scenario === state.hoveredScenario ? "is-hovered" : ""}"><i class="scenario-line scenario-line--${escapeHtml(item.scenario)}"></i>${escapeHtml(scenarioLabels[item.scenario])}${item.thirteen_week_percent == null ? "" : ` · 13주 ${escapeHtml(formatPercent(item.thirteen_week_percent))}`}</button>`).join("");
  drawChart(byId("baseline-chart"), scenarioSeries, state.data.safe_cash.suggested_amount, true);
  const ordered = [...alternatives].sort((a, b) => Number(a.alternative_id === state.selectedAlternative || a.alternative_id === state.hoveredAlternative) - Number(b.alternative_id === state.selectedAlternative || b.alternative_id === state.hoveredAlternative));
  const series = ordered.map((item) => {
    const isSelected = item.alternative_id === state.selectedAlternative, isHovered = item.alternative_id === state.hoveredAlternative;
    return { id: item.alternative_id, label: humanizeText(item.label), color: isHovered ? hoverColor : isSelected ? accent : "#7f8984", opacity: isHovered ? 1 : isSelected ? .85 : .35, width: isHovered ? 5 : isSelected ? 4 : 1.7, dash: item.ranking_eligible ? [] : [8, 5], values: item.weekly_13.map((week) => week.closing_cash) };
  });
  byId("comparison-legend").innerHTML = alternatives.map((item) => { const readiness = alternativeReadiness(item); return `<button type="button" data-select-alternative="${escapeHtml(item.alternative_id)}" class="${item.alternative_id === state.selectedAlternative ? "is-selected" : ""} ${item.alternative_id === state.hoveredAlternative ? "is-hovered" : ""}" aria-label="${escapeHtml(humanizeText(item.label))}, ${escapeHtml(readiness.label)}"><i class="comparison-status ${readiness.className}" aria-hidden="true"></i><span class="comparison-line"></span>${escapeHtml(humanizeText(item.label))}</button>`; }).join("");
  drawChart(byId("comparison-chart"), series, state.data.safe_cash.suggested_amount, true);
}

function chooseSituationExample(button) {
  byId("v3-situation-text").value = button.dataset.situationExample || "";
  document.querySelectorAll("[data-situation-example]").forEach((node) => node.classList.toggle("is-selected", node === button));
  state.situationInterpretation = null;
  byId("v3-situation-review").hidden = true;
  byId("v3-situation-status").textContent = "예시 문장을 불러왔습니다. 내용을 수정한 뒤 입력에 반영할 내용을 확인해 주세요.";
  byId("v3-situation-text").focus();
}

function renderSituationReview(result) {
  state.situationInterpretation = result;
  const items = result.understood || [];
  const container = byId("v3-situation-review-items");
  container.innerHTML = items.map((item) => {
    const canApply = item.key !== "area" || Boolean(result.suggested_area_code);
    const detail = item.key === "area" && !canApply
      ? "상권명이 정확하지 않아 지도에서 직접 선택해야 합니다."
      : item.key === "area" || item.key === "industry"
        ? "확인하면 위 사업장 입력에 반영됩니다."
        : item.key === "goal"
          ? "확인하면 4단계 비교 기준의 초기 선택에 반영됩니다."
          : "확인하면 후속 질문과 행동계획의 우선순위에 반영됩니다.";
    return `<label><input type="checkbox" data-situation-item="${escapeHtml(item.key)}" ${canApply ? "checked" : "disabled"}><span><strong>${escapeHtml(item.label)}: ${escapeHtml(item.value)}</strong><small>${escapeHtml(detail)}</small></span></label>`;
  }).join("") || '<p class="field-help">반영할 후보를 찾지 못했습니다. 사업장·업종과 재무값을 직접 입력해 주세요.</p>';
  byId("v3-situation-review").hidden = false;
}

function invalidateSituationDependentResults() {
  state.data = null;
  state.marketScenarios = null;
  state.scenarioResults = {};
  state.scenarioCacheKey = "";
  state.selectedAlternative = null;
  state.selectedPolicyIds = new Set();
  state.conditionalPolicyIds = new Set();
  state.policySelectionInitialized = false;
  state.questionCatalog = {};
  state.eligibilityAnswers = {};
  state.questionWizardOrder = [];
  state.questionWizardAllOrder = [];
  state.questionWizardIndex = 0;
  state.questionBatchRound = 0;
  state.questionWizardComplete = false;
  state.questionWizardResultsVisible = false;
  state.v3AskedFields = [];
  state.actionBrief = null;
  state.pendingWhatIf = null;
  state.whatIfUndo = null;
  state.whatIfOriginalPrompt = "";
  state.whatIfClarificationAttempts = 0;
  byId("v3-undo-what-if").hidden = true;
  byId("diagnosis-empty").hidden = false;
  byId("diagnosis-result").hidden = true;
  byId("decision-empty").hidden = false;
  byId("decision-result").hidden = true;
  byId("diagnosis-next").disabled = true;
}

function renderSituationFinanceContext() {
  const panel = byId("v3-finance-context");
  const context = state.situationContext;
  if (!context?.signals?.length) {
    panel.hidden = true;
    return;
  }
  byId("v3-finance-context-items").innerHTML = context.signals
    .map((signal) => situationSignalGuidance[signal])
    .filter(Boolean)
    .map((message) => `<li>${escapeHtml(message)}</li>`)
    .join("");
  panel.hidden = false;
}

function applyConfirmedSituation() {
  const result = state.situationInterpretation;
  if (!result) return toast("먼저 문장에서 반영할 내용을 확인해 주세요.");
  const checked = new Set(
    [...document.querySelectorAll("[data-situation-item]:checked")].map((node) => node.dataset.situationItem)
  );
  const knownSignals = new Set(Object.keys(situationSignalGuidance));
  const signals = (result.understood || [])
    .map((item) => item.key)
    .filter((key) => checked.has(key) && knownSignals.has(key));
  const areaCode = checked.has("area") ? result.suggested_area_code : null;
  const industryCode = checked.has("industry") ? result.suggested_industry_code : null;
  const confirmedGoal = checked.has("goal") ? result.suggested_goal : null;

  if (areaCode) selectArea(areaCode, false, false, true, false);
  if (industryCode) {
    const major = industryMajor(industryCode);
    byId("industry-major-select").value = major;
    populateIndustries(major, industryCode);
  }
  if (confirmedGoal && goalPresentations[confirmedGoal]) {
    state.goal = confirmedGoal;
    const goalInput = document.querySelector(`input[name="goal"][value="${CSS.escape(confirmedGoal)}"]`);
    if (goalInput) goalInput.checked = true;
  }

  state.situationContext = {
    original_text: result.original_text,
    confirmed_area_code: areaCode,
    confirmed_industry_code: industryCode,
    signals,
    confirmed_goal: confirmedGoal,
  };
  invalidateSituationDependentResults();
  renderSituationFinanceContext();
  updateSummary();
  const applied = [];
  if (areaCode) applied.push("사업장");
  if (industryCode) applied.push("업종");
  if (signals.length) applied.push("후속 확인 우선순위");
  if (confirmedGoal) applied.push("비교 기준 후보");
  byId("v3-situation-status").textContent = applied.length
    ? `${applied.join(" · ")}에 확인한 내용을 반영했습니다. 금액은 2단계에서 직접 입력해 주세요.`
    : "반영한 후보가 없습니다. 사업장·업종과 재무값을 직접 입력해 주세요.";
  toast("확인한 상황을 다음 입력과 질문 흐름에 반영했습니다.");
}

async function interpretV3Situation() {
  const text = byId("v3-situation-text").value.trim();
  if (text.length < 2) return toast("현재 상황을 두 글자 이상 적어 주세요.");
  const button = byId("v3-interpret-situation");
  button.disabled = true;
  byId("v3-situation-status").textContent = "문장에서 확인할 사업장·업종·걱정거리·비교 기준을 정리하고 있습니다.";
  try {
    const result = await api("/api/v4/situation/interpret", { method: "POST", body: JSON.stringify({ text }) });
    renderSituationReview(result);
    byId("v3-situation-status").textContent = (result.understood || []).length
      ? "찾은 내용을 확인했습니다. 체크한 항목만 다음 입력과 질문 흐름에 반영됩니다."
      : "확인 가능한 내용을 찾지 못했습니다. 사업장·업종과 재무값을 직접 입력해 주세요.";
  } catch (error) {
    byId("v3-situation-status").textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function applyV3WhatIfInputs(comparison) {
  const quick = comparison?.quick_input;
  if (quick?.recent_monthly_revenues?.length) {
    state.revenueMonths = quick.recent_monthly_revenues.length;
    renderRevenueMonths(quick.recent_monthly_revenues.map((value) => value / 10000));
  }
  const reductions = comparison?.cost_reduction_plan || { rent: 0, labor: 0, purchase: 0, other_fixed: 0 };
  [["reduce-rent", "rent"], ["reduce-labor", "labor"], ["reduce-purchase", "purchase"], ["reduce-other", "other_fixed"]].forEach(([id, key]) => {
    byId(id).value = Number(reductions[key] || 0) / 10000;
  });
  if (comparison?.market_scenario && scenarioLabels[comparison.market_scenario]) {
    state.scenario = comparison.market_scenario;
    const radio = document.querySelector(`input[name="market-scenario"][value="${CSS.escape(state.scenario)}"]`);
    if (radio) radio.checked = true;
  }
  if (comparison?.goal) {
    state.goal = comparison.goal;
    const radio = document.querySelector(`input[name="goal"][value="${CSS.escape(state.goal)}"]`);
    if (radio) radio.checked = true;
  }
  updateConfirmedReduction();
}

function whatIfDisplayValue(detail, value) {
  return detail.display_type === "money" ? compactMoney(value) : String(value ?? "-");
}

function whatIfMoneyResultRow(label, before, after) {
  if (before == null || after == null) return "";
  const delta = Number(after) - Number(before);
  const deltaText = `${delta >= 0 ? "+" : ""}${compactMoney(delta)}`;
  return `<div class="v3-what-if-result-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(compactMoney(before))}</strong><span>→</span><strong>${escapeHtml(compactMoney(after))} <small class="v3-what-if-delta">(${escapeHtml(deltaText)})</small></strong></div>`;
}

function openWhatIfDialog() {
  const dialog = byId("v3-what-if-dialog");
  if (typeof dialog.showModal === "function") dialog.showModal();
}

function renderWhatIfClarification(payload, prompt) {
  state.pendingWhatIf = null;
  const source = payload.external_ai_used ? "Luna가 추가 확인이 필요하다고 판단했습니다" : "조건을 명확히 해주세요";
  byId("v3-what-if-dialog-content").innerHTML = `<span class="v3-what-if-source">${escapeHtml(source)}</span><h2 id="v3-what-if-dialog-title">한 가지 확인이 필요합니다</h2><p class="v3-what-if-prompt-review">입력한 가정: “${escapeHtml(prompt)}”</p><p>${escapeHtml(payload.message || "가정을 정확히 계산하려면 추가 정보가 필요합니다.")}</p>`;
  byId("v3-what-if-clarification-question").textContent = payload.clarification_question;
  byId("v3-what-if-clarification-answer").value = "";
  byId("v3-what-if-clarification").hidden = false;
  byId("v3-what-if-retry").hidden = false;
  byId("v3-what-if-apply").hidden = true;
  openWhatIfDialog();
  window.setTimeout(() => byId("v3-what-if-clarification-answer").focus(), 50);
}

function renderWhatIfUnsupported(payload, prompt) {
  state.pendingWhatIf = null;
  const examples = (payload.supported_examples || [
    "매출이 10% 더 떨어지면?",
    "매출이 10% 늘어나면?",
    "임대료를 월 100만원 줄이면?",
    "하방 시나리오로 바꾸면?",
  ]).map((example) => `<li>${escapeHtml(example)}</li>`).join("");
  byId("v3-what-if-dialog-content").innerHTML = `<span class="v3-what-if-source">현재 지원 범위 안내</span><h2 id="v3-what-if-dialog-title">현재 계산할 수 없는 조건입니다</h2><p class="v3-what-if-prompt-review">입력한 가정: “${escapeHtml(prompt)}”</p><p>${escapeHtml(payload.message || "같은 질문을 반복하지 않고 입력 가능한 조건을 안내합니다.")}</p><h3>입력 가능한 예시</h3><ul>${examples}</ul>`;
  byId("v3-what-if-clarification").hidden = true;
  byId("v3-what-if-retry").hidden = true;
  byId("v3-what-if-apply").hidden = true;
  openWhatIfDialog();
}

function renderWhatIfPreview(payload, prompt) {
  const preview = applyGoalRanking(payload.result, payload.comparison.goal);
  payload.previewData = preview;
  state.pendingWhatIf = payload;
  state.whatIfOriginalPrompt = "";
  state.whatIfClarificationAttempts = 0;
  const source = payload.external_ai_used ? "Luna 의도 해석 · 계산은 로컬 엔진" : "로컬 제한 규칙 해석 · 계산은 로컬 엔진";
  const changes = (payload.change_details || []).map((detail) => `<div class="v3-what-if-change-row"><span>${escapeHtml(detail.label)}</span><strong>${escapeHtml(whatIfDisplayValue(detail, detail.before))}</strong><span>→</span><strong>${escapeHtml(whatIfDisplayValue(detail, detail.after))}</strong></div>`).join("");
  const currentAlternatives = state.data?.intervention_results || [];
  const previewAlternatives = preview?.intervention_results || [];
  let comparedId = preview?.comparison_result?.top_alternative_id;
  if (!currentAlternatives.some((item) => item.alternative_id === comparedId && item.metrics) || !previewAlternatives.some((item) => item.alternative_id === comparedId && item.metrics)) comparedId = state.selectedAlternative;
  if (!currentAlternatives.some((item) => item.alternative_id === comparedId && item.metrics) || !previewAlternatives.some((item) => item.alternative_id === comparedId && item.metrics)) comparedId = "no_action";
  const beforeAlternative = currentAlternatives.find((item) => item.alternative_id === comparedId && item.metrics);
  const afterAlternative = previewAlternatives.find((item) => item.alternative_id === comparedId && item.metrics);
  const beforeTop = currentAlternatives.find((item) => item.alternative_id === state.data?.comparison_result?.top_alternative_id);
  const afterTop = previewAlternatives.find((item) => item.alternative_id === preview?.comparison_result?.top_alternative_id);
  const metricRows = beforeAlternative && afterAlternative ? [
    whatIfMoneyResultRow("13주 뒤 현금", beforeAlternative.metrics.week13_ending_cash, afterAlternative.metrics.week13_ending_cash),
    whatIfMoneyResultRow("6개월 뒤 현금", beforeAlternative.metrics.month6_ending_cash, afterAlternative.metrics.month6_ending_cash),
    whatIfMoneyResultRow("새로 생기는 빚", beforeAlternative.metrics.net_new_borrowing, afterAlternative.metrics.net_new_borrowing),
    whatIfMoneyResultRow("월 최대상환", beforeAlternative.metrics.maximum_monthly_debt_service, afterAlternative.metrics.maximum_monthly_debt_service),
  ].join("") : '<p class="field-help">같은 대안의 전·후 수치를 비교할 수 없습니다.</p>';
  const topRow = `<div class="v3-what-if-result-row"><span>현재 기준 1순위</span><strong>${escapeHtml(humanizeText(beforeTop?.label || "확인 필요"))}</strong><span>→</span><strong>${escapeHtml(humanizeText(afterTop?.label || "확인 필요"))}</strong></div>`;
  byId("v3-what-if-dialog-content").innerHTML = `<span class="v3-what-if-source">${escapeHtml(source)}</span><h2 id="v3-what-if-dialog-title">What-if 임시 계산 결과</h2><p class="v3-what-if-prompt-review">입력한 가정: “${escapeHtml(prompt)}”</p><h3>무엇을 바꿔 계산했나요?</h3><div class="v3-what-if-change-list">${changes}</div><h3>현재 입력과 가정 적용 후 결과</h3><p class="field-help">각 항목의 왼쪽은 현재 입력값으로 계산한 결과이고, 오른쪽은 이 가정을 적용한 임시 결과입니다.</p><div class="v3-what-if-result-grid">${metricRows}${topRow}</div><p class="notice">${escapeHtml(payload.notice)}</p>`;
  byId("v3-what-if-clarification").hidden = true;
  byId("v3-what-if-retry").hidden = true;
  byId("v3-what-if-apply").hidden = false;
  openWhatIfDialog();
}

async function runV3WhatIf(promptOverride = null, isRetry = false) {
  if (!state.data) return toast("먼저 현금 진단을 완료해 주세요.");
  const prompt = (promptOverride ?? byId("v3-what-if-prompt").value).trim();
  if (prompt.length < 2) return toast("바꿔 볼 조건을 적어 주세요.");
  if (!isRetry) {
    state.whatIfOriginalPrompt = prompt;
    state.whatIfClarificationAttempts = 0;
  }
  const button = byId("v3-run-what-if");
  button.disabled = true;
  showLoading("입력한 가정으로 현금흐름을 다시 계산하고 있습니다.");
  try {
    const payload = await api("/api/v4/what-if", { method: "POST", body: JSON.stringify({ comparison: comparisonRequest(), prompt, answered_fields: Object.keys(state.eligibilityAnswers), asked_fields: state.v3AskedFields, situation_context: situationContextPayload(), consent_to_external_ai: byId("v3-what-if-ai-consent").checked, question_round: state.questionBatchRound }) });
    if (!payload.applied) {
      if (payload.unsupported || (payload.clarification_question && state.whatIfClarificationAttempts >= 1)) {
        renderWhatIfUnsupported(payload, state.whatIfOriginalPrompt || prompt);
      } else if (payload.clarification_question) {
        state.whatIfClarificationAttempts = 1;
        renderWhatIfClarification(payload, state.whatIfOriginalPrompt || prompt);
      } else {
        renderWhatIfUnsupported(payload, state.whatIfOriginalPrompt || prompt);
      }
      byId("v3-what-if-status").textContent = payload.message;
      return;
    }
    renderWhatIfPreview(payload, prompt);
    byId("v3-what-if-status").textContent = "임시 계산을 완료했습니다. 팝업에서 변경 전·후 차이를 확인해 주세요.";
  } catch (error) {
    byId("v3-what-if-status").textContent = error.message;
  } finally {
    hideLoading();
    button.disabled = false;
  }
}

function applyPendingWhatIf() {
  const payload = state.pendingWhatIf;
  if (!payload) return;
  state.whatIfUndo = {
    comparison: cloneData(comparisonRequest()),
    data: cloneData(state.data),
    scenarioResults: cloneData(state.scenarioResults),
    scenarioCacheKey: state.scenarioCacheKey,
    selectedAlternative: state.selectedAlternative,
    scenario: state.scenario,
    goal: state.goal,
  };
  applyV3WhatIfInputs(payload.comparison);
  state.data = payload.previewData;
  state.scenarioResults = { [state.scenario]: state.data };
  state.scenarioCacheKey = comparisonCacheKey(comparisonRequest());
  const selectionStillAvailable = state.data.intervention_results.some((item) => item.alternative_id === state.selectedAlternative && item.metrics);
  state.selectedAlternative = selectionStillAvailable ? state.selectedAlternative : state.data.comparison_result.top_alternative_id;
  syncPolicySearchToAlternative(state.selectedAlternative);
  renderResults();
  updateSummary();
  byId("v3-what-if-dialog").close();
  byId("v3-undo-what-if").hidden = false;
  byId("v3-what-if-status").textContent = `${payload.changes.join(" · ")}을 현재 입력에 적용했습니다.`;
  state.pendingWhatIf = null;
  state.whatIfOriginalPrompt = "";
  state.whatIfClarificationAttempts = 0;
}

function undoAppliedWhatIf() {
  const snapshot = state.whatIfUndo;
  if (!snapshot) return;
  applyV3WhatIfInputs(snapshot.comparison);
  state.scenario = snapshot.scenario;
  state.goal = snapshot.goal;
  state.data = snapshot.data;
  state.scenarioResults = snapshot.scenarioResults;
  state.scenarioCacheKey = snapshot.scenarioCacheKey;
  state.selectedAlternative = snapshot.selectedAlternative;
  syncPolicySearchToAlternative(state.selectedAlternative);
  renderResults();
  updateSummary();
  state.whatIfUndo = null;
  byId("v3-undo-what-if").hidden = true;
  byId("v3-what-if-status").textContent = "What-if 적용 전 입력과 결과로 되돌렸습니다.";
  toast("What-if 적용 전 상태로 되돌렸습니다.");
}

function discardWhatIfDialog() {
  state.pendingWhatIf = null;
  state.whatIfOriginalPrompt = "";
  state.whatIfClarificationAttempts = 0;
  byId("v3-what-if-dialog").close();
}

function retryWhatIfClarification() {
  const answer = byId("v3-what-if-clarification-answer").value.trim();
  if (!answer) return toast("확인 질문에 답을 입력해 주세요.");
  if (state.whatIfClarificationAttempts !== 1 || !state.whatIfOriginalPrompt) return toast("확인 질문은 한 번만 답할 수 있습니다.");
  const combined = `${state.whatIfOriginalPrompt}\n확인 답변: ${answer}`;
  byId("v3-what-if-dialog").close();
  runV3WhatIf(combined, true);
}

function selectAlternative(id) {
  if (!state.data?.intervention_results.some((item) => item.alternative_id === id && item.metrics)) return;
  state.selectedAlternative = id; state.actionBrief = null;
  const policyId = policyByAlternative[id];
  if (policyId && state.selectedPolicyIds.has(policyId)) state.focusedPolicyId = policyId;
  syncPolicySearchToAlternative(id); renderPolicyFocus(); renderCharts();
}

function syncPolicySearchToAlternative(id) {
  const select = byId("qa-policy");
  if (!select) return;
  const policy = policyByAlternative[id] || "";
  select.value = [...select.options].some((option) => option.value === policy) ? policy : "";
  const scope = byId("qa-policy-scope");
  if (scope) scope.textContent = policy ? `현재 상담 정책: ${policyNames[policy] || select.selectedOptions[0]?.text || "선택 정책"}` : "현재 선택 정책만 상담합니다.";
}
function pointSegmentDistance(point, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y;
  if (!dx && !dy) return Math.hypot(point.x - a.x, point.y - a.y);
  const t = Math.max(0, Math.min(1, ((point.x - a.x) * dx + (point.y - a.y) * dy) / (dx * dx + dy * dy)));
  return Math.hypot(point.x - (a.x + t * dx), point.y - (a.y + t * dy));
}
function chartLineAt(event) {
  const canvas = event.currentTarget, rect = canvas.getBoundingClientRect(), point = { x: event.clientX - rect.left, y: event.clientY - rect.top };
  let best = { id: null, distance: 15 };
  (canvas._seriesHit || []).forEach((series) => { for (let index = 1; index < series.points.length; index += 1) { const distance = pointSegmentDistance(point, series.points[index - 1], series.points[index]); if (distance < best.distance) best = { id: series.id, distance }; } });
  return best.id;
}
function selectChartLine(event) {
  const id = chartLineAt(event);
  if (id) selectAlternative(id);
}
function hoverComparisonChartLine(event) {
  const id = chartLineAt(event);
  if (id === state.hoveredAlternative) return;
  state.hoveredAlternative = id;
  renderCharts();
}
function clearComparisonChartHover() {
  if (!state.hoveredAlternative) return;
  state.hoveredAlternative = null;
  renderCharts();
}
async function selectScenario(id, scrollAfter = true) {
  if (!Object.hasOwn(scenarioLabels, id)) return;
  state.scenario = id;
  const radio = document.querySelector(`input[name="market-scenario"][value="${id}"]`);
  if (radio) radio.checked = true;
  updateScenarioApplicationStatus();
  updateSummary();
  if (!state.data) return;
  let completed = false;
  if (state.scenarioResults[id]) {
    state.data = applyGoalRanking(state.scenarioResults[id]);
    state.selectedAlternative = state.data.comparison_result.top_alternative_id;
    syncPolicySearchToAlternative(state.selectedAlternative);
    renderResults();
    completed = true;
  } else {
    completed = await runComparison("diagnosis", false);
  }
  if (completed && scrollAfter) {
    const result = byId("diagnosis-result");
    result.scrollIntoView({ behavior: "smooth", block: "start" });
    result.focus({ preventScroll: true });
  }
}
function selectScenarioChartLine(event) {
  const id = chartLineAt(event);
  if (id && id !== state.scenario) selectScenario(id, false);
}
function hoverScenarioChartLine(event) {
  const id = chartLineAt(event);
  if (id === state.hoveredScenario) return;
  state.hoveredScenario = id;
  renderCharts();
}
function clearScenarioChartHover() {
  if (!state.hoveredScenario) return;
  state.hoveredScenario = null;
  renderCharts();
}

function officialSiteName(url) {
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    if (host.includes("seoulshinbo")) return "서울신용보증재단"; if (host.includes("seoul")) return "서울시";
    if (host.includes("semas")) return "소상공인시장진흥공단";
    if (host.includes("sbiz24")) return "소상공인24"; if (host.includes("bizinfo")) return "기업마당";
    if (host.includes("mss.go.kr")) return "중소벤처기업부"; return host;
  } catch { return "공식기관"; }
}
function evidenceLinks(items = []) {
  const grouped = new Map();
  items.forEach((item) => {
    const url = safeUrl(item.source_url);
    if (!grouped.has(url)) grouped.set(url, { url, pages: new Set() });
    const match = String(item.page_or_section || "").match(/PAGE\s+(\d+)/i);
    grouped.get(url).pages.add(match ? `${match[1]}쪽` : humanizeText(item.page_or_section || "근거 위치"));
  });
  return [...grouped.values()].map((item) => {
    const pages = [...item.pages].join(" · ");
    return `<a href="${item.url}" target="_blank" rel="noreferrer">${escapeHtml(officialSiteName(item.url))} 공고 원문${pages ? ` · 근거 ${escapeHtml(pages)}` : ""}</a>`;
  }).join("");
}
function appendChatMessage(role, content, extraHtml = "") {
  const thread = byId("chat-thread");
  const article = document.createElement("article");
  article.className = `chat-message chat-message--${role}`;
  const displayContent = role === "assistant" ? normalizeChatText(content) : String(content ?? "");
  article.innerHTML = `<div class="chat-avatar" aria-hidden="true">${role === "user" ? "나" : "AI"}</div><div class="chat-bubble"><p>${escapeHtml(displayContent)}</p>${extraHtml}</div>`;
  thread.appendChild(article);
  thread.scrollTop = thread.scrollHeight;
  return article;
}

function normalizeChatText(content) {
  return String(content ?? "")
    .replace(/\r\n?/g, "\n")
    .replace(/(^|\n)\s{0,3}#{1,6}\s*/g, "$1")
    .replace(/\s+#{1,6}\s+/g, "\n")
    .replace(/^\s*\|?\s*:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)+\s*\|?\s*$/gm, "")
    .replace(/^.*\|.*$/gm, (row) => row.split("|").map((cell) => cell.trim()).filter(Boolean).join(" · "))
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function discoveredPolicyLinks(items = []) {
  if (!items.length) return "";
  return `<div class="chat-policy-results"><strong>함께 확인할 정책</strong>${items.map((item) => `<a href="${safeUrl(item.official_url)}" target="_blank" rel="noreferrer"><span>${escapeHtml(item.policy_name)}</span><small>${escapeHtml(humanizeText(item.matched_section))}</small></a>`).join("")}</div>`;
}

function updateChatLimit() {
  const remaining = Math.max(0, 5 - state.chatTurns);
  byId("chat-count").textContent = `${state.chatTurns} / 5회`;
  byId("chat-send").disabled = remaining === 0;
  byId("chat-question").disabled = remaining === 0;
  byId("chat-question").placeholder = remaining === 0 ? "이번 상담의 5회 질문을 모두 사용했습니다." : "예: 대출 이자와 월 상환 부담을 줄일 정책이 있나요?";
}

async function askPolicy() {
  if (state.chatTurns >= 5) return toast("정책 상담은 현재 페이지에서 5회까지 가능합니다.");
  const input = byId("chat-question");
  const question = input.value.trim();
  if (question.length < 2) return toast("질문을 입력해 주세요.");
  const history = state.chatMessages.slice(-8);
  appendChatMessage("user", question);
  state.chatMessages.push({ role: "user", content: question });
  state.chatTurns += 1;
  input.value = "";
  updateChatLimit();
  const pending = appendChatMessage("assistant", "공식 공고에서 관련 근거를 찾고 있습니다.");
  pending.classList.add("is-loading");
  try {
    const selectedPolicy = byId("qa-policy").value;
    const payload = await api("/api/v1/ai/ask", { method: "POST", body: JSON.stringify({ policy_id: selectedPolicy || null, question, history }) });
    const links = evidenceLinks(payload.official_evidence);
    const extra = `${discoveredPolicyLinks(payload.discovered_policies)}${links ? `<div class="official-links evidence-links">${links}</div>` : ""}<p class="field-help">자격과 승인 여부는 공식기관에서 최종 확인하세요.</p>`;
    pending.remove();
    appendChatMessage("assistant", payload.answer, extra);
    state.chatMessages.push({ role: "assistant", content: payload.answer });
  } catch (error) {
    pending.remove();
    const message = `답변을 불러오지 못했습니다. ${error.message}`;
    appendChatMessage("assistant", message);
    state.chatMessages.push({ role: "assistant", content: message });
  }
}

document.addEventListener("click", async (event) => {
  const step = event.target.closest("[data-step]"); if (step) { event.preventDefault(); showStep(step.dataset.step); return; }
  const situationExample = event.target.closest("[data-situation-example]"); if (situationExample) { chooseSituationExample(situationExample); return; }
  const preset = event.target.closest("[data-preset]"); if (preset) { applyPreset(preset.dataset.preset); return; }
  const scenario = event.target.closest("[data-select-scenario]"); if (scenario) { selectScenario(scenario.dataset.selectScenario, false); return; }
  const questionExample = event.target.closest("[data-question-example]");
  if (questionExample) {
    byId("chat-question").value = questionExample.dataset.questionExample;
    byId("chat-question").focus();
    return;
  }
  const focusedPolicy = event.target.closest("[data-focus-policy]");
  if (focusedPolicy) { focusPolicy(focusedPolicy.dataset.focusPolicy); return; }
  const alternative = event.target.closest("[data-select-alternative]"); if (alternative) selectAlternative(alternative.dataset.selectAlternative);
  const policyScenario = event.target.closest("[data-open-policy-scenario]");
  if (policyScenario) { openPolicyScenarioEditor(policyScenario.dataset.openPolicyScenario); return; }
  const editPolicyAnswer = event.target.closest("[data-edit-policy-answer]");
  if (editPolicyAnswer) {
    reviewWizardAnswers([editPolicyAnswer.dataset.editPolicyAnswer], editPolicyAnswer.dataset.policyId);
    showStep("diagnosis");
    window.setTimeout(() => byId("policy-questionnaire").scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    return;
  }
  const questionChoice = event.target.closest("[data-question-choice]");
  if (questionChoice) { answerWizardQuestion(questionChoice.dataset.questionChoice, questionChoice.dataset.questionValue); return; }
  const questionUnknown = event.target.closest("[data-question-unknown]");
  if (questionUnknown) { answerWizardQuestion(questionUnknown.dataset.questionUnknown, "unknown"); return; }
  const questionNext = event.target.closest("[data-question-next]");
  if (questionNext) {
    const question = currentWizardQuestion();
    const input = question ? document.querySelector(`[data-question-entry="${question.field}"]`) : null;
    if (!input?.value) { toast("값을 입력하거나 모름을 선택해 주세요."); return; }
    answerWizardQuestion(question.field, input.value);
    return;
  }
  const level = event.target.closest("[data-map-level]");
  if (level?.dataset.mapLevel === "district") resetMapToSeoul();
  if (level?.dataset.mapLevel === "dong" && byId("district-select").value) { byId("dong-select").value = ""; state.selectedDong = ""; clearSelectedArea(); refreshAreaList(); renderDongCircles(true); }
  if (level?.dataset.mapLevel === "area" && byId("dong-select").value) renderAreaCircles(filteredAreas(), true);
});
document.addEventListener("change", (event) => {
  const policy = event.target.closest("[data-policy-select]");
  if (policy) {
    const id = policy.dataset.policySelect;
    if (policy.checked && state.selectedPolicyIds.size >= 3 && !state.selectedPolicyIds.has(id)) {
      policy.checked = false;
      toast("비교할 정책은 최대 3개까지 선택할 수 있습니다.");
      return;
    }
    if (policy.checked) state.selectedPolicyIds.add(id); else {
      state.selectedPolicyIds.delete(id);
      state.conditionalPolicyIds.delete(id);
      if (state.policyScenarioEditorPolicyId === id) state.policyScenarioEditorPolicyId = "";
    }
    state.scenarioCacheKey = ""; state.actionBrief = null;
    renderPolicyDiscovery();
    return;
  }
  const answer = event.target.closest("[data-eligibility-field]");
  if (answer) {
    state.eligibilityAnswers[answer.dataset.eligibilityField] = answer.value || "unknown";
    state.scenarioCacheKey = ""; state.actionBrief = null;
    return;
  }
  const scenarioField = event.target.closest("[data-policy-scenario]");
  if (scenarioField) {
    const id = scenarioField.dataset.policyScenario;
    state.policyScenarioValues[id] ||= {};
    state.policyScenarioValues[id][scenarioField.dataset.scenarioField] = scenarioField.value;
    state.scenarioCacheKey = ""; state.actionBrief = null;
  }
});
byId("district-select").addEventListener("change", (event) => event.target.value ? chooseDistrict(event.target.value, true) : resetMapToSeoul());
byId("dong-select").addEventListener("change", (event) => event.target.value ? chooseDong(byId("district-select").value, event.target.value, true) : renderDongCircles(true));
byId("area-search").addEventListener("input", () => { refreshAreaList(); const query = byId("area-search").value.trim(); if (query) renderAreaCircles(filteredAreas(), true); else if (byId("dong-select").value) renderAreaCircles(filteredAreas(), true); else if (byId("district-select").value) renderDongCircles(true); else renderDistrictCircles(true); });
byId("area-select").addEventListener("change", (event) => selectArea(event.target.value));
byId("industry-major-select").addEventListener("change", (event) => { populateIndustries(event.target.value); updateSummary(); });
byId("industry-select").addEventListener("change", () => { updateSummary(); refreshComparisonForMarketChange(); });
byId("business-next").addEventListener("click", () => { try { validateBusiness(); showStep("finance"); } catch (error) { toast(error.message); } });
byId("add-revenue-month").addEventListener("click", () => { if (state.revenueMonths < 12) { state.revenueMonths += 1; renderRevenueMonths(); } });
["opening-cash", "monthly-rent", "monthly-labor", "monthly-purchase", "monthly-other-fixed", "loan-balance"].forEach((id) => byId(id).addEventListener("input", updateSummary));
["reduce-rent", "reduce-labor", "reduce-purchase", "reduce-other"].forEach((id) => byId(id).addEventListener("input", () => { updateConfirmedReduction(); state.scenarioCacheKey = ""; state.actionBrief = null; }));
byId("run-diagnosis").addEventListener("click", () => openV4InputLedger());
byId("diagnosis-next").addEventListener("click", () => { enableSelectedPolicyPreviews(); runComparison("decision"); });
byId("refresh-policy-comparison").addEventListener("click", async () => { if (await runComparison("diagnosis", false)) toast("선택한 정책 조건과 금액을 다시 계산했습니다."); });
byId("policy-question-back").addEventListener("click", previousWizardQuestion);
byId("policy-question-review").addEventListener("click", reviewWizardAnswers);
byId("open-cost-reduction").addEventListener("click", () => setCostReductionEditor(true));
byId("close-cost-reduction").addEventListener("click", () => setCostReductionEditor(false));
byId("close-policy-scenario").addEventListener("click", closePolicyScenarioEditor);
byId("v3-interpret-situation").addEventListener("click", interpretV3Situation);
byId("v3-apply-situation").addEventListener("click", applyConfirmedSituation);
byId("v3-situation-text").addEventListener("input", () => {
  if (!state.situationInterpretation) return;
  state.situationInterpretation = null;
  byId("v3-situation-review").hidden = true;
  byId("v3-situation-status").textContent = "문장을 수정했습니다. 입력에 반영할 내용을 다시 확인해 주세요.";
});
byId("v3-run-what-if").addEventListener("click", () => runV3WhatIf());
byId("v3-what-if-prompt").addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); runV3WhatIf(); } });
document.querySelectorAll("[data-what-if-example]").forEach((button) => button.addEventListener("click", () => {
  byId("v3-what-if-prompt").value = button.dataset.whatIfExample;
  byId("v3-what-if-prompt").focus();
}));
byId("v3-undo-what-if").addEventListener("click", undoAppliedWhatIf);
byId("v3-what-if-close").addEventListener("click", discardWhatIfDialog);
byId("v3-what-if-discard").addEventListener("click", discardWhatIfDialog);
byId("v3-what-if-apply").addEventListener("click", applyPendingWhatIf);
byId("v3-what-if-retry").addEventListener("click", retryWhatIfClarification);
byId("v3-what-if-clarification-answer").addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); retryWhatIfClarification(); } });
byId("v3-what-if-dialog").addEventListener("click", (event) => {
  const dialog = event.currentTarget;
  const rect = dialog.getBoundingClientRect();
  const inside = event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
  if (!inside) discardWhatIfDialog();
});
byId("run-csv").addEventListener("click", runCsvBaseline);
byId("baseline-chart").addEventListener("click", selectScenarioChartLine);
byId("baseline-chart").addEventListener("pointermove", hoverScenarioChartLine);
byId("baseline-chart").addEventListener("pointerleave", clearScenarioChartHover);
byId("comparison-chart").addEventListener("click", selectChartLine);
byId("comparison-chart").addEventListener("pointermove", hoverComparisonChartLine);
byId("comparison-chart").addEventListener("pointerleave", clearComparisonChartHover);
document.querySelectorAll("input[name=market-scenario]").forEach((node) => node.addEventListener("change", () => selectScenario(node.value)));
document.querySelectorAll("input[name=goal]").forEach((node) => node.addEventListener("change", () => {
  const selectedBeforeGoalChange = state.selectedAlternative;
  state.goal = node.value;
  Object.values(state.scenarioResults).forEach((result) => applyGoalRanking(result));
  if (!state.data) return;
  state.data = applyGoalRanking(state.scenarioResults[state.scenario] || state.data);
  const selectionStillAvailable = state.data.intervention_results.some((item) => item.alternative_id === selectedBeforeGoalChange && item.metrics);
  state.selectedAlternative = selectionStillAvailable ? selectedBeforeGoalChange : state.data.comparison_result.top_alternative_id;
  syncPolicySearchToAlternative(state.selectedAlternative);
  renderResults(); updateSummary();
}));
byId("active-scenario-link").addEventListener("click", () => {
  showStep("diagnosis");
  window.setTimeout(() => byId("scenario-panel").scrollIntoView({ behavior: "smooth", block: "start" }), 80);
});
byId("chat-send").addEventListener("click", askPolicy);
byId("chat-question").addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); askPolicy(); } });
byId("v4-policy-prev").addEventListener("click", () => {
  const candidates = policyFocusCandidates();
  if (candidates.length < 2) return;
  const index = Math.max(0, candidates.findIndex((item) => item.policy_id === state.focusedPolicyId));
  focusPolicy(candidates[(index - 1 + candidates.length) % candidates.length].policy_id);
});
byId("v4-policy-next").addEventListener("click", () => {
  const candidates = policyFocusCandidates();
  if (candidates.length < 2) return;
  const index = Math.max(0, candidates.findIndex((item) => item.policy_id === state.focusedPolicyId));
  focusPolicy(candidates[(index + 1) % candidates.length].policy_id);
});
byId("safe-cash-help").addEventListener("click", () => {
  const dialog = byId("safe-cash-dialog");
  if (typeof dialog.showModal === "function") dialog.showModal();
});
byId("safe-cash-close").addEventListener("click", () => byId("safe-cash-dialog").close());
byId("safe-cash-confirm").addEventListener("click", () => byId("safe-cash-dialog").close());
byId("safe-cash-dialog").addEventListener("click", (event) => {
  const dialog = event.currentTarget;
  const rect = dialog.getBoundingClientRect();
  const inside = event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
  if (!inside) dialog.close();
});
window.addEventListener("resize", () => state.data && renderCharts(), { passive: true });

const today = new Date();
byId("csv-reference").value = today.toISOString().slice(0, 10);
renderRevenueMonths();
updateConfirmedReduction();
updateChatLimit();
updateScenarioApplicationStatus();
loadCatalogs().catch(() => toast("상권과 업종 목록을 불러오지 못했습니다."));
