const state = {
  data: null, areaPoints: [], industries: [], selectedArea: null, selectedDong: "",
  marketScenarios: null, scenario: "central", goal: "최소부채", selectedAlternative: null,
  revenueMonths: 6, mapLevel: "district", map: null, circleLayer: null, circles: new Map(),
  visibleDongDistrict: "", visibleAreaScope: "", policies: [], chatMessages: [], chatTurns: 0,
  eligibilityAnswers: {}, policyScenarioValues: {},
};

const byId = (id) => document.getElementById(id);
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
const industryMajorLabels = { CS1: "외식업", CS2: "서비스업", CS3: "소매업" };
const policyNames = {
  POL_SEOUL_CRISIS_TRACK2_2026H2: "위기 소상공인 지원",
  POL_SEMAS_REFINANCE_2026: "소상공인 대환대출",
  POL_SEOUL_FUND_2026: "서울시 중소기업육성자금",
};
const policyByAlternative = {
  track2_reimbursement: "POL_SEOUL_CRISIS_TRACK2_2026H2", refinance: "POL_SEMAS_REFINANCE_2026",
  emergency_loan: "POL_SEOUL_FUND_2026", combined_safe_cash: "POL_SEOUL_CRISIS_TRACK2_2026H2",
};
const alternativeDescriptions = {
  no_action: "지금의 매출·지출·대출 조건을 그대로 유지했을 때의 결과입니다.",
  cost_reduction_5: "월 지출을 5% 줄였을 때 현금 잔액이 얼마나 달라지는지 보여줍니다.",
  track2_reimbursement: "지원비가 지급된다는 조건으로 지급 전후 현금 변화를 계산합니다.",
  refinance: "현재 대출을 더 낮은 금리와 긴 상환기간으로 바꾼 경우를 계산합니다.",
  emergency_loan: "서울시 정책자금을 추가로 빌렸을 때 현금과 상환 부담을 함께 계산합니다.",
  combined_safe_cash: "비용 절감과 가능한 정책수단을 함께 적용해 안전현금을 확보하는 경우입니다.",
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
  "cash-rich": { revenues: [1800, 1780, 1760, 1740, 1710, 1680], cash: 3000, rent: 200, labor: 450, purchase: 400, loan: 1000, rate: 4, term: 48 },
  stable: { revenues: [1200, 1190, 1210, 1180, 1200, 1190], cash: 1200, rent: 180, labor: 350, purchase: 300, loan: 1500, rate: 5, term: 36 },
  "sales-down": { revenues: [700, 760, 820, 880, 940, 1000], cash: 500, rent: 180, labor: 350, purchase: 280, loan: 2000, rate: 6.5, term: 36 },
  "high-fixed": { revenues: [1000, 1020, 1040, 1060, 1080, 1100], cash: 400, rent: 300, labor: 500, purchase: 250, loan: 1500, rate: 6, term: 30 },
  "debt-heavy": { revenues: [1100, 1120, 1140, 1160, 1180, 1200], cash: 300, rent: 180, labor: 300, purchase: 250, loan: 5000, rate: 9, term: 24 },
};

function toast(message) {
  const node = byId("toast"); node.textContent = message; node.classList.add("is-visible");
  window.setTimeout(() => node.classList.remove("is-visible"), 3000);
}

async function api(path, options = {}) {
  const headers = options.body ? { "Content-Type": "application/json", ...(options.headers || {}) } : options.headers;
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || "요청을 처리하지 못했습니다.");
  return payload;
}

function showStep(id) {
  const order = ["business", "finance", "diagnosis", "decision"];
  document.querySelectorAll(".screen").forEach((node) => node.classList.toggle("is-active", node.id === id));
  document.querySelectorAll(".step-button").forEach((node) => node.classList.toggle("is-active", node.dataset.step === id));
  byId("summary-progress").textContent = `${order.indexOf(id) + 1} / 4`;
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

function selectArea(code, fromMap = false, refreshResults = true, focusMap = true) {
  const item = state.areaPoints.find((area) => area.code === String(code));
  if (!item) return;
  state.selectedArea = item; byId("district-select").value = item.district; populateDongs(item.district, item.administrative_dong); byId("area-search").value = "";
  refreshAreaList(); byId("area-select").value = item.code;
  byId("selected-location").innerHTML = `<strong>${escapeHtml(item.name)}</strong><br>${escapeHtml(item.district)} ${escapeHtml(item.administrative_dong)} · ${escapeHtml(item.category)} · ${Math.round(item.area_m2).toLocaleString("ko-KR")}㎡`;
  renderAreaCircles(filteredAreas(), false);
  const circle = state.circles.get(item.code);
  if (focusMap && state.map && circle) { state.map.flyTo([item.latitude, item.longitude], 17, { duration: fromMap ? .35 : .6 }); if (fromMap) circle.openPopup(); }
  updateSummary();
  if (refreshResults) refreshComparisonForMarketChange(); else loadMarketScenarios();
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
  state.areaPoints = areas.items; state.industries = industries.items; state.policies = policies.items;
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
  ["opening-cash", "monthly-rent", "monthly-labor", "monthly-purchase", "loan-balance"].forEach((id) => { if (byId(id).value === "" || Number(byId(id).value) < 0) throw new Error("현재 현금과 월 지출을 빠짐없이 입력해 주세요."); });
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
  if (employment.grade && ["true", "false"].includes(employment.inBaseline)) scenarios.push({
    policy_id: "POL_SEMAS_EMPLOYMENT_INSURANCE_2026",
    employment_insurance_grade: Number(employment.grade),
    expense_already_in_baseline: employment.inBaseline === "true",
  });
  const family = state.policyScenarioValues.POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026 || {};
  if (family.amount && family.paymentDate) scenarios.push({
    policy_id: "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026",
    approved_support_amount: Math.round(Number(family.amount) * 10000),
    payment_date: family.paymentDate,
  });
  return scenarios;
}

async function loadMarketScenarios() {
  if (!state.selectedArea || !byId("industry-select").value) return;
  byId("model-period").textContent = "기준자료 확인 중";
  byId("model-period-help").textContent = "선택한 상권·업종의 마지막 집계시점을 확인하고 있습니다.";
  try {
    const payload = await api(`/api/v1/market-scenarios/${encodeURIComponent(state.selectedArea.code)}/${encodeURIComponent(byId("industry-select").value)}`);
    state.marketScenarios = payload.market_scenario;
    const nodes = document.querySelectorAll("#scenario-options label");
    if (state.marketScenarios.available) {
      ["downside", "central", "recovery"].forEach((name, index) => { const item = state.marketScenarios.scenarios[name]; nodes[index].querySelector("b").textContent = `13주 ${formatPercent(item.thirteen_week_percent)} · 6개월 ${formatPercent(item.six_month_percent)}`; });
      const period = String(state.marketScenarios.reference_period);
      const periodLabel = period.length === 5 ? `${period.slice(0, 4)}년 ${period.slice(4)}분기` : period;
      byId("model-period").textContent = `모델 입력 기준 · ${periodLabel}`;
      byId("model-period-help").textContent = `${periodLabel}까지 집계된 상권·업종 자료를 모델 입력으로 사용해 이후 13주와 6개월의 변화 범위를 계산합니다. 현재 실시간 자료나 내 점포 실적을 뜻하지 않습니다.`;
    } else { nodes.forEach((node) => node.querySelector("b").textContent = "집계자료 없음"); byId("model-period").textContent = "모델 자료 없음"; byId("model-period-help").textContent = "선택한 조합의 모델 입력자료가 없어 상권 변화율 0%로 계산합니다."; }
  } catch { state.marketScenarios = null; byId("model-period").textContent = "기준자료 불러오기 실패"; byId("model-period-help").textContent = "상권 변화율을 불러오지 못해 입력한 재무정보만으로 계산합니다."; }
}
function formatPercent(value) { return `${Number(value) > 0 ? "+" : ""}${Number(value).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}%`; }

async function refreshComparisonForMarketChange() {
  await loadMarketScenarios();
  if (state.data) await runComparison("diagnosis", false);
}

async function runComparison(next = "diagnosis", navigate = true) {
  try { validateBusiness(); validateFinance(); } catch (error) { toast(error.message); return false; }
  const loanBalance = moneyInputValue("loan-balance");
  const body = {
    area_code: state.selectedArea.code, industry_code: byId("industry-select").value, market_scenario: state.scenario,
    direct_shock_13_week_percent: 0, direct_shock_6_month_percent: 0, safe_cash_override: null,
    goal: state.goal, assume_conditional: byId("conditional-assumption").checked,
    quick_input: {
      reference_date: referenceDate(), opening_cash: moneyInputValue("opening-cash"), safe_cash_threshold: 0,
      recent_monthly_revenues: revenueValues(true), revenue_timing: byId("revenue-timing").value,
      monthly_rent: moneyInputValue("monthly-rent"), monthly_labor_cost: moneyInputValue("monthly-labor"),
      monthly_variable_cost: moneyInputValue("monthly-purchase"), expense_timing: byId("expense-timing").value,
      total_loan_balance: loanBalance, annual_interest_rate_percent: loanBalance ? numericValue("loan-rate") : 0,
      remaining_term_months: loanBalance ? numericValue("loan-term") : 1, debt_timing: byId("debt-timing").value,
    },
    existing_loan_rate_percent: loanBalance ? numericValue("loan-rate") : 0,
    existing_loan_term_months: loanBalance ? numericValue("loan-term") : 1,
    eligibility_profile: eligibilityProfilePayload(),
    policy_scenarios: policyScenarioPayload(),
  };
  const button = next === "diagnosis" ? byId("run-diagnosis") : byId("diagnosis-next");
  const original = button.textContent; button.disabled = true; button.textContent = "계산 중";
  try {
    state.data = await api("/api/v1/alternatives/compare", { method: "POST", body: JSON.stringify(body) });
    state.selectedAlternative = state.data.comparison_result.top_alternative_id;
    renderResults(); updateSummary(); if (navigate) showStep(next); return true;
  } catch (error) { toast(error.message); return false; }
  finally { button.disabled = false; button.textContent = original; }
}

async function applyPreset(id) {
  const preset = presentationPresets[id];
  const area = state.areaPoints.find((item) => item.code === "3001491") || state.areaPoints[0];
  const industry = state.industries.find((item) => item.code === "CS100001") || state.industries[0];
  if (!preset || !area || !industry) return toast("준비된 가게 상황을 불러오지 못했습니다.");
  selectArea(area.code, false, false);
  const major = industryMajor(industry.code); byId("industry-major-select").value = major; populateIndustries(major, industry.code);
  state.revenueMonths = preset.revenues.length; renderRevenueMonths(preset.revenues);
  [["opening-cash", preset.cash], ["monthly-rent", preset.rent], ["monthly-labor", preset.labor], ["monthly-purchase", preset.purchase], ["loan-balance", preset.loan], ["loan-rate", preset.rate], ["loan-term", preset.term]].forEach(([field, value]) => { byId(field).value = value; });
  byId("revenue-timing").value = "daily"; byId("expense-timing").value = "early"; byId("debt-timing").value = "late";
  state.scenario = "central"; document.querySelector('input[name="market-scenario"][value="central"]').checked = true;
  document.querySelectorAll("[data-preset]").forEach((node) => node.classList.toggle("is-selected", node.dataset.preset === id));
  byId("preset-status").textContent = "6개월 재무정보를 채웠습니다. 아래 사업장을 확인한 뒤 재무 입력과 현금 진단을 순서대로 볼 수 있습니다.";
  updateSummary(); await loadMarketScenarios(); await runComparison("diagnosis", false);
  toast("6개월 입력을 채웠습니다. 현재 화면에서 다음 단계로 진행하세요.");
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

function firstBelowSafe(weekly, safeCash) { const found = weekly.find((item) => item.closing_cash < safeCash); return found ? `${found.period}주차 (${found.end_date})` : "13주 내 없음"; }
function scenarioComparison() { return state.data?.market_scenario_comparison || []; }
function scenarioValuesDiffer(selector) { const values = scenarioComparison().map(selector); return new Set(values.map((value) => String(value))).size > 1; }
function renderResults() {
  byId("diagnosis-empty").hidden = true; byId("diagnosis-result").hidden = false; byId("decision-empty").hidden = true; byId("decision-result").hidden = false; byId("diagnosis-next").disabled = false;
  const inputBaseline = state.data.baseline_cashflow;
  const baselineAlternative = state.data.intervention_results.find((item) => item.alternative_id === "no_action" && item.metrics);
  const weekly = baselineAlternative?.weekly_13 || inputBaseline.weekly_13;
  const week13EndingCash = baselineAlternative?.metrics?.week13_ending_cash ?? inputBaseline.weekly_summary.ending_cash;
  const month6EndingCash = baselineAlternative?.metrics?.month6_ending_cash ?? inputBaseline.monthly_summary.ending_cash;
  const safeCash = state.data.safe_cash.suggested_amount;
  const safeDateChanges = scenarioValuesDiffer((item) => firstBelowSafe(item.weekly_13, safeCash));
  const week13Changes = scenarioValuesDiffer((item) => item.week13_ending_cash);
  const month6Changes = scenarioValuesDiffer((item) => item.month6_ending_cash);
  const metrics = [
    ["현재 보유 현금", compactMoney(inputBaseline.weekly_13[0]?.opening_cash ?? state.data.baseline_input.opening_cash), "상권 범위와 무관한 입력값", false],
    ["필요한 안전현금", compactMoney(safeCash), "향후 28일 필수 지출이라 범위 선택과 무관", false],
    ["안전현금 아래", firstBelowSafe(weekly, safeCash), "선택한 상권 범위에 따라 달라짐", safeDateChanges],
    ["13주 뒤 현금", compactMoney(week13EndingCash), week13EndingCash < 0 ? "선택 범위에서 현금 부족 예상" : "선택 범위에서 0원 이상 유지", week13Changes],
  ];
  byId("diagnosis-metrics").innerHTML = metrics.map(([label, value, note, changes]) => `<div class="metric ${changes ? "is-scenario-sensitive" : "is-fixed"}"><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div>`).join("");
  byId("six-month-summary").innerHTML = `<dt class="${month6Changes ? "is-scenario-sensitive" : ""}">현금 잔액</dt><dd class="${month6Changes ? "is-scenario-sensitive" : ""}">${compactMoney(month6EndingCash)}</dd><dt>남은 대출</dt><dd>${compactMoney(inputBaseline.debt_summary.remaining_principal_at_6_months)}</dd><dt>만기까지 총이자</dt><dd>${compactMoney(baselineAlternative?.metrics?.total_interest_through_maturity ?? inputBaseline.debt_summary.total_interest_through_maturity)}</dd>`;
  renderAlternatives(); renderPolicyDiscovery(); renderCharts();
}

function renderPolicyDiscovery() {
  const discovery = state.data?.policy_discovery;
  if (!discovery) return;
  byId("situation-labels").innerHTML = (discovery.situation_labels || []).map((label) => `<span>${escapeHtml(label)}</span>`).join("");
  const mode = discovery.retrieval_mode === "hybrid" ? `Hybrid AI 검색 · ${discovery.embedding_model}` : discovery.retrieval_mode === "bm25_fallback" ? "Embedding 2회 실패 · 정확어 검색으로 계속" : "정확어 검색";
  byId("policy-discovery-status").textContent = `${mode}. ${discovery.privacy || ""}`;
  const hasScenarioInputs = (discovery.candidates || []).some((item) => item.candidate_state !== "제외" && ["reviewed_event_requires_grade", "reviewed_event_requires_amount_date"].includes(item.event_status));
  renderStagedQuestions(discovery.staged_questions || [], hasScenarioInputs);
  byId("policy-discovery-cards").innerHTML = (discovery.candidates || []).map((item) => `<article class="policy-discovery-card"><div><span class="policy-readiness">${escapeHtml(item.eligibility_readiness)}</span><h3>${escapeHtml(item.policy_name)}</h3><p class="matched-section">찾은 근거: ${escapeHtml(item.matched_section)}</p><p>${escapeHtml(String(item.match_explanation || "").replace(/[#|>*_]/g, " ").replace(/\s+/g, " "))}</p><small>${escapeHtml(item.simulation_readiness)}</small>${renderPolicyScenarioInputs(item)}</div><div class="policy-card-actions"><a href="${safeUrl(item.official_url)}" target="_blank" rel="noreferrer">공고 보기</a><button type="button" class="primary" data-ask-policy="${escapeHtml(item.policy_id)}">이 정책 질문하기</button></div></article>`).join("") || '<p class="field-help">현재 입력에서 추가 정책 후보를 찾지 못했습니다.</p>';
  bindPolicyScenarioInputs();
}

function renderStagedQuestions(questions, hasScenarioInputs = false) {
  const panel = byId("staged-question-panel");
  panel.hidden = !questions.length && !hasScenarioInputs;
  byId("staged-questions").innerHTML = questions.map((item) => {
    const value = state.eligibilityAnswers[item.field] ?? "";
    const control = item.input_type === "date" ? `<input type="date" data-eligibility-field="${escapeHtml(item.field)}" value="${escapeHtml(value)}">` : item.input_type === "number" ? `<input type="number" min="0" max="10000" step="1" data-eligibility-field="${escapeHtml(item.field)}" value="${escapeHtml(value)}" placeholder="모르면 비워두기">` : `<select data-eligibility-field="${escapeHtml(item.field)}"><option value="">모름</option>${(item.options || []).filter((option) => option.value !== "unknown").map((option) => `<option value="${escapeHtml(option.value)}" ${value === option.value ? "selected" : ""}>${escapeHtml(option.label)}</option>`).join("")}</select>`;
    return `<div class="staged-question"><label>${escapeHtml(item.label)}</label>${control}<small>${escapeHtml(item.reason)} ${escapeHtml(item.impact)}</small></div>`;
  }).join("");
  document.querySelectorAll("[data-eligibility-field]").forEach((node) => node.addEventListener("change", () => { state.eligibilityAnswers[node.dataset.eligibilityField] = node.value; }));
}

function renderPolicyScenarioInputs(item) {
  if (item.candidate_state === "제외") return "";
  const saved = state.policyScenarioValues[item.policy_id] || {};
  if (item.event_status === "reviewed_event_requires_grade") return `<div class="policy-scenario-inputs" data-policy-scenario="${escapeHtml(item.policy_id)}"><label>고용보험 가입등급<select data-scenario-key="grade"><option value="">선택</option>${[1,2,3,4,5,6,7].map((grade) => `<option value="${grade}" ${String(saved.grade) === String(grade) ? "selected" : ""}>${grade}등급</option>`).join("")}</select></label><label>보험료가 현재 월지출에 포함됐나요?<select data-scenario-key="inBaseline"><option value="">모름</option><option value="true" ${saved.inBaseline === "true" ? "selected" : ""}>예</option><option value="false" ${saved.inBaseline === "false" ? "selected" : ""}>아니오</option></select></label></div>`;
  if (item.event_status === "reviewed_event_requires_amount_date") return `<div class="policy-scenario-inputs" data-policy-scenario="${escapeHtml(item.policy_id)}"><label>실제 신청금액<input type="number" min="1" max="450" step="1" data-scenario-key="amount" value="${escapeHtml(saved.amount || "")}" placeholder="만원"></label><label>공고 차수 지급예정일<input type="date" data-scenario-key="paymentDate" value="${escapeHtml(saved.paymentDate || "")}"></label></div>`;
  return "";
}

function bindPolicyScenarioInputs() {
  document.querySelectorAll("[data-policy-scenario]").forEach((group) => {
    const policyId = group.dataset.policyScenario;
    state.policyScenarioValues[policyId] ||= {};
    group.querySelectorAll("[data-scenario-key]").forEach((node) => node.addEventListener("change", () => { state.policyScenarioValues[policyId][node.dataset.scenarioKey] = node.value; }));
  });
}

function humanizeText(value) {
  let text = String(value ?? "");
  Object.entries(policyNames).forEach(([id, label]) => { text = text.replaceAll(id, label); });
  return text.replaceAll("동시수혜 공식 근거 확인 필요", "두 지원을 함께 받을 수 있는지 공식기관에 확인해 주세요").replaceAll("공식 근거 확인 필요", "최신 지원 조건을 공식기관에 확인해 주세요").replaceAll("Track2", "위기 소상공인 지원");
}
function alternativeNote(item, baseline) {
  if (item.alternative_id === "no_action") return "다른 대안의 효과를 비교하는 기준선입니다.";
  const delta = item.metrics.week13_ending_cash - baseline.metrics.week13_ending_cash;
  return `아무 조치도 하지 않을 때보다 13주 뒤 현금이 ${compactMoney(Math.abs(delta))} ${delta >= 0 ? "많습니다" : "적습니다"}.`;
}
function goalMetric(item) {
  const metrics = item.metrics;
  if (state.goal === "최장생존") return `${metrics.survival_days_6_month}일`;
  if (state.goal === "최소상환") return compactMoney(metrics.maximum_monthly_debt_service);
  if (state.goal === "빠른실행") return metrics.days_to_first_effect === 0 ? "즉시 반영" : `${metrics.days_to_first_effect}일 후`;
  return compactMoney(metrics.net_new_borrowing);
}
function orderAlternatives(alternatives) {
  const orderedIds = state.data.comparison_result.ordered_alternative_ids || [];
  const order = new Map(orderedIds.map((id, index) => [id, index]));
  return [...alternatives].sort((left, right) => {
    const leftRank = order.has(left.alternative_id) ? order.get(left.alternative_id) : Number.MAX_SAFE_INTEGER;
    const rightRank = order.has(right.alternative_id) ? order.get(right.alternative_id) : Number.MAX_SAFE_INTEGER;
    return leftRank - rightRank;
  });
}
function renderRankingNotice(alternatives, top) {
  const notice = byId("ranking-notice");
  const selected = alternatives.find((item) => item.alternative_id === state.selectedAlternative) || alternatives.find((item) => item.alternative_id === top);
  if (!selected) { notice.hidden = true; return; }
  const goal = goalPresentations[state.goal] || { label: state.goal, metric: "판단값" };
  const topItem = alternatives.find((item) => item.alternative_id === top);
  const eligibleCount = alternatives.filter((item) => item.ranking_eligible).length;
  const plan = state.data.execution_plan?.find((item) => item.alternative_id === selected.alternative_id);
  const checks = [...new Set([...(selected.items_to_confirm || []), ...(plan?.conditions_to_check_now || [])].map(humanizeText).filter(Boolean))];
  const messages = [];
  if (!selected.ranking_eligible) {
    messages.push("자격·접수 조건이 아직 확인되지 않아 추천 순위에서는 제외된 가정 결과입니다.");
  } else if (selected.alternative_id === top) {
    messages.push(`현재 자격이 확인된 ${eligibleCount}개 대안 중 1순위입니다.`);
  } else if (topItem) {
    messages.push(`현재 목표의 1순위는 ${topItem.label}입니다.`);
  }
  if (selected.metrics.week13_minimum_cash < 0) {
    messages.push(`13주 중 현금이 최저 ${compactMoney(selected.metrics.week13_minimum_cash)}까지 내려가므로 이 대안만으로는 현금 부족을 막지 못합니다.`);
  } else {
    messages.push("13주 동안 계산상 현금 잔액이 0원 아래로 내려가지 않습니다.");
  }
  const tone = selected.metrics.week13_minimum_cash < 0 ? "is-danger" : (!selected.ranking_eligible || checks.length ? "is-caution" : "is-safe");
  notice.className = `ranking-notice ${tone}`;
  notice.innerHTML = `<div class="ranking-notice-heading"><span>현재 선택한 대안</span><strong>${escapeHtml(selected.label)}</strong></div><div class="ranking-goal"><span>${escapeHtml(goal.label)} 판단값</span><strong>${escapeHtml(goal.metric)} ${escapeHtml(goalMetric(selected))}</strong></div><p>${messages.map(escapeHtml).join(" ")}</p>${checks.length ? `<div class="ranking-checks"><strong>이 대안에서 확인할 사항</strong><ul>${checks.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>` : ""}`;
  notice.hidden = false;
}
function renderAlternatives() {
  const alternatives = orderAlternatives(state.data.intervention_results.filter((item) => item.metrics));
  const baseline = alternatives.find((item) => item.alternative_id === "no_action") || alternatives[0];
  const top = state.data.comparison_result.top_alternative_id;
  if (!alternatives.length) { byId("alternative-cards").innerHTML = '<div class="empty-state"><h2>현재 비교 가능한 대안이 없습니다</h2><p>공식 상담기관에서 조건을 확인해 주세요.</p></div>'; return; }
  const rankById = new Map((state.data.comparison_result.ordered_alternative_ids || []).map((id, index) => [id, index + 1]));
  const goal = goalPresentations[state.goal] || { label: state.goal, metric: "판단값" };
  renderRankingNotice(alternatives, top);
  byId("alternative-cards").innerHTML = alternatives.map((item) => `<article class="alternative-card ${item.alternative_id === top ? "is-top" : ""} ${!item.ranking_eligible ? "is-unranked" : ""} ${item.alternative_id === state.selectedAlternative ? "is-selected" : ""}" data-select-alternative="${escapeHtml(item.alternative_id)}" tabindex="0" aria-label="${escapeHtml(item.label)} 선택">${!item.ranking_eligible ? '<span class="ranking-status">자격 확인 전 · 추천 순위 제외</span>' : ""}<h2>${escapeHtml(item.label)}</h2><p>${escapeHtml(alternativeDescriptions[item.alternative_id] || humanizeText(item.reason_summary) || "현금과 부채 영향을 비교합니다.")}</p><div class="goal-score"><span>${escapeHtml(goal.label)} 판단값</span><strong>${escapeHtml(goal.metric)} ${escapeHtml(goalMetric(item))}</strong></div><div class="card-metrics"><div><span>13주 뒤 현금</span><strong>${compactMoney(item.metrics.week13_ending_cash)}</strong></div><div><span>6개월 뒤 현금</span><strong>${compactMoney(item.metrics.month6_ending_cash)}</strong></div><div><span>새로 생기는 빚</span><strong>${compactMoney(item.metrics.net_new_borrowing)}</strong></div><div><span>월 최대상환</span><strong>${compactMoney(item.metrics.maximum_monthly_debt_service)}</strong></div></div><p class="card-delta">${escapeHtml(alternativeNote(item, baseline))}</p><button type="button" class="primary detail-button" data-open-alternative="${escapeHtml(item.alternative_id)}">자세히 보기</button></article>`).join("");
  byId("comparison-body").innerHTML = alternatives.map((item) => `<tr class="${item.alternative_id === top ? "is-top" : ""}"><td>${rankById.has(item.alternative_id) ? `${rankById.get(item.alternative_id)}위` : "순위 제외"}</td><td>${escapeHtml(item.label)}</td><td>${compactMoney(item.metrics.week13_ending_cash)}</td><td>${compactMoney(item.metrics.month6_ending_cash)}</td><td>${compactMoney(item.metrics.net_new_borrowing)}</td><td>${compactMoney(item.metrics.maximum_monthly_debt_service)}</td><td>${compactMoney(item.metrics.total_interest_through_maturity)}</td><td>${item.metrics.confirmation_item_count}</td></tr>`).join("");
}

function canvasSetup(canvas) {
  const ratio = window.devicePixelRatio || 1, width = Math.max(320, canvas.getBoundingClientRect().width || 900), height = Math.max(280, Math.min(480, width * .45));
  canvas.width = width * ratio; canvas.height = height * ratio;
  const context = canvas.getContext("2d"); context.scale(ratio, ratio); return { context, width, height };
}
function drawChart(canvas, series, safeCash = null, interactive = false) {
  if (!canvas || !series.length || !series[0].values.length || canvas.offsetParent === null) return;
  const { context: ctx, width, height } = canvasSetup(canvas), css = getComputedStyle(document.documentElement);
  const colors = { text: css.getPropertyValue("--muted").trim(), line: css.getPropertyValue("--line").trim(), warning: css.getPropertyValue("--warning").trim() };
  const pad = { left: 82, right: 20, top: 30, bottom: 50 }, all = series.flatMap((item) => item.values).concat(safeCash == null ? [] : [safeCash]);
  let min = Math.min(0, ...all), max = Math.max(0, ...all); if (min === max) max += 1;
  const x = (i) => pad.left + i * (width - pad.left - pad.right) / Math.max(1, series[0].values.length - 1);
  const y = (v) => pad.top + (max - v) * (height - pad.top - pad.bottom) / (max - min);
  ctx.clearRect(0, 0, width, height); ctx.font = "12px system-ui"; ctx.fillStyle = colors.text; ctx.strokeStyle = colors.line; ctx.lineWidth = 1;
  if (safeCash != null && safeCash > 0) { ctx.fillStyle = "rgba(180,140,35,.10)"; ctx.fillRect(pad.left, y(safeCash), width - pad.left - pad.right, Math.max(0, y(0) - y(safeCash))); ctx.strokeStyle = colors.warning; ctx.setLineDash([6, 4]); ctx.beginPath(); ctx.moveTo(pad.left, y(safeCash)); ctx.lineTo(width - pad.right, y(safeCash)); ctx.stroke(); ctx.setLineDash([]); }
  for (let i = 0; i <= 4; i += 1) { const value = min + (max - min) * i / 4, py = y(value); ctx.strokeStyle = colors.line; ctx.beginPath(); ctx.moveTo(pad.left, py); ctx.lineTo(width - pad.right, py); ctx.stroke(); ctx.fillStyle = colors.text; ctx.fillText(`${Math.round(value / 10000).toLocaleString("ko-KR")}만`, 25, py + 4); }
  ctx.save(); ctx.translate(14, height / 2); ctx.rotate(-Math.PI / 2); ctx.fillStyle = colors.text; ctx.textAlign = "center"; ctx.fillText("현금 잔액(만원)", 0, 0); ctx.restore();
  canvas._seriesHit = [];
  series.forEach((item) => { const points = item.values.map((value, index) => ({ x: x(index), y: y(value) })); ctx.strokeStyle = item.color; ctx.globalAlpha = item.opacity ?? 1; ctx.lineWidth = item.width || 3; ctx.lineCap = "round"; ctx.setLineDash(item.dash || []); ctx.beginPath(); points.forEach((point, index) => index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y)); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1; if (interactive && item.id) canvas._seriesHit.push({ id: item.id, points }); });
  ctx.fillStyle = colors.text; ctx.textAlign = "center"; series[0].values.forEach((_, index) => { if (index === 0 || index === series[0].values.length - 1 || index % 2 === 0) ctx.fillText(`${index + 1}주`, x(index), height - 22); });
}
function renderCharts() {
  if (!state.data) return;
  const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();
  const alternatives = state.data.intervention_results.filter((item) => item.metrics), baseline = alternatives.find((item) => item.alternative_id === "no_action");
  const comparisons = scenarioComparison();
  const scenarioSeries = comparisons.length ? comparisons.map((item) => ({ id: item.scenario, label: scenarioLabels[item.scenario], color: item.scenario === state.scenario ? accent : "#7f8984", opacity: item.scenario === state.scenario ? 1 : .5, width: item.scenario === state.scenario ? 4 : 2, dash: item.scenario === "downside" ? [8, 5] : item.scenario === "recovery" ? [2, 5] : [], values: item.weekly_13.map((week) => week.closing_cash) })).sort((left, right) => Number(left.id === state.scenario) - Number(right.id === state.scenario)) : [{ label: scenarioLabels[state.scenario], color: accent, values: (baseline?.weekly_13 || state.data.baseline_cashflow.weekly_13).map((item) => item.closing_cash) }];
  byId("scenario-chart-legend").innerHTML = (comparisons.length ? comparisons : [{ scenario: state.scenario }]).map((item) => `<span class="${item.scenario === state.scenario ? "is-selected" : ""}"><i class="scenario-line scenario-line--${escapeHtml(item.scenario)}"></i>${escapeHtml(scenarioLabels[item.scenario])}${item.thirteen_week_percent == null ? "" : ` · 13주 ${escapeHtml(formatPercent(item.thirteen_week_percent))}`}</span>`).join("");
  drawChart(byId("baseline-chart"), scenarioSeries, state.data.safe_cash.suggested_amount);
  const ordered = [...alternatives].sort((a, b) => Number(a.alternative_id === state.selectedAlternative) - Number(b.alternative_id === state.selectedAlternative));
  const series = ordered.map((item) => ({ id: item.alternative_id, label: item.label, color: item.alternative_id === state.selectedAlternative ? accent : "#7f8984", opacity: item.alternative_id === state.selectedAlternative ? 1 : .48, width: item.alternative_id === state.selectedAlternative ? 4 : 1.7, values: item.weekly_13.map((week) => week.closing_cash) }));
  byId("comparison-legend").innerHTML = alternatives.map((item) => `<button type="button" data-select-alternative="${escapeHtml(item.alternative_id)}" class="${item.alternative_id === state.selectedAlternative ? "is-selected" : ""}"><span></span>${escapeHtml(item.label)}</button>`).join("");
  drawChart(byId("comparison-chart"), series, state.data.safe_cash.suggested_amount, true);
}
function selectAlternative(id) {
  if (!state.data?.intervention_results.some((item) => item.alternative_id === id && item.metrics)) return;
  state.selectedAlternative = id; renderAlternatives(); renderCharts();
}
function pointSegmentDistance(point, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y;
  if (!dx && !dy) return Math.hypot(point.x - a.x, point.y - a.y);
  const t = Math.max(0, Math.min(1, ((point.x - a.x) * dx + (point.y - a.y) * dy) / (dx * dx + dy * dy)));
  return Math.hypot(point.x - (a.x + t * dx), point.y - (a.y + t * dy));
}
function selectChartLine(event) {
  const canvas = event.currentTarget, rect = canvas.getBoundingClientRect(), point = { x: event.clientX - rect.left, y: event.clientY - rect.top };
  let best = { id: null, distance: 15 };
  (canvas._seriesHit || []).forEach((series) => { for (let index = 1; index < series.points.length; index += 1) { const distance = pointSegmentDistance(point, series.points[index - 1], series.points[index]); if (distance < best.distance) best = { id: series.id, distance }; } });
  if (best.id) selectAlternative(best.id);
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
function officialLinks(urls = []) {
  const counts = {};
  return urls.map((url) => { const site = officialSiteName(url); counts[site] = (counts[site] || 0) + 1; return `<a href="${safeUrl(url)}" target="_blank" rel="noreferrer">${escapeHtml(site)} 공고 ${counts[site]}</a>`; }).join(" ") || "공식기관에서 확인";
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
function openAlternative(id) {
  const item = state.data?.intervention_results.find((alt) => alt.alternative_id === id);
  if (!item?.metrics) return;
  selectAlternative(id);
  const policy = policyByAlternative[id], plan = state.data.execution_plan?.find((entry) => entry.alternative_id === id);
  const conditions = [...(item.items_to_confirm || []), ...(plan?.conditions_to_check_now || [])].map(humanizeText).filter(Boolean);
  const planHtml = plan ? `<section class="dialog-plan"><h3>실행 전에 확인할 내용</h3><dl><dt>먼저 확인</dt><dd>${escapeHtml([...new Set(conditions)].join(", ") || "추가 확인 없음")}</dd><dt>신청기한</dt><dd>${escapeHtml(humanizeText(plan.application_deadline || "공식 공고에서 확인"))}</dd><dt>준비서류</dt><dd>${escapeHtml((plan.required_documents || []).map(humanizeText).join(", ") || "공식 공고에서 확인")}</dd><dt>지급 전 필요현금</dt><dd>${compactMoney(plan.cash_needed_before_payment)}</dd><dt>최소 신청금액</dt><dd>${compactMoney(plan.minimum_loan_amount)}</dd><dt>문의</dt><dd>${escapeHtml(humanizeText(plan.inquiry || "공식기관에서 확인"))}</dd><dt>공식 링크</dt><dd class="official-links">${officialLinks(plan.official_urls)}</dd></dl></section>` : `<section class="dialog-plan"><h3>실행 방법</h3><p>${id === "no_action" ? "별도 신청 없이 현재 조건을 유지합니다." : "별도 정책 신청 없이 월 지출 항목을 확인하고 줄일 금액을 정합니다."}</p></section>`;
  byId("dialog-content").innerHTML = `<p class="eyebrow">대안 상세</p><h2>${escapeHtml(item.label)}</h2><p>${escapeHtml(alternativeDescriptions[id] || humanizeText(item.reason_summary))}</p><div class="dialog-metrics"><div><span>13주 뒤 현금</span><strong>${compactMoney(item.metrics.week13_ending_cash)}</strong></div><div><span>6개월 뒤 현금</span><strong>${compactMoney(item.metrics.month6_ending_cash)}</strong></div><div><span>새로 생기는 빚</span><strong>${compactMoney(item.metrics.net_new_borrowing)}</strong></div><div><span>월 최대상환</span><strong>${compactMoney(item.metrics.maximum_monthly_debt_service)}</strong></div><div><span>만기까지 총이자</span><strong>${compactMoney(item.metrics.total_interest_through_maturity)}</strong></div><div><span>확인할 조건</span><strong>${item.metrics.confirmation_item_count}개</strong></div></div>${planHtml}<p class="notice">계산 결과는 승인 가능성을 뜻하지 않습니다. 지원 금액과 지급일, 접수 가능 여부는 신청 전에 공식기관에서 확인해 주세요.</p>`;
  byId("dialog-ai").hidden = !policy; if (policy) byId("qa-policy").value = policy;
  const dialog = byId("alternative-dialog"); if (typeof dialog.showModal === "function") dialog.showModal();
}

function appendChatMessage(role, content, extraHtml = "") {
  const thread = byId("chat-thread");
  const article = document.createElement("article");
  article.className = `chat-message chat-message--${role}`;
  article.innerHTML = `<div class="chat-avatar" aria-hidden="true">${role === "user" ? "나" : "AI"}</div><div class="chat-bubble"><p>${escapeHtml(content)}</p>${extraHtml}</div>`;
  thread.appendChild(article);
  thread.scrollTop = thread.scrollHeight;
  return article;
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
  byId("chat-question").placeholder = remaining === 0 ? "이번 상담의 5회 질문을 모두 사용했습니다." : "예: 제가 아파서 가게를 쉬면 받을 수 있는 지원이 있나요?";
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

document.addEventListener("click", (event) => {
  const step = event.target.closest("[data-step]"); if (step) { event.preventDefault(); showStep(step.dataset.step); return; }
  const preset = event.target.closest("[data-preset]"); if (preset) { applyPreset(preset.dataset.preset); return; }
  const questionExample = event.target.closest("[data-question-example]");
  if (questionExample) {
    byId("chat-question").value = questionExample.dataset.questionExample;
    byId("chat-question").focus();
    return;
  }
  const detail = event.target.closest("[data-open-alternative]"); if (detail) { event.stopPropagation(); openAlternative(detail.dataset.openAlternative); return; }
  const alternative = event.target.closest("[data-select-alternative]"); if (alternative) selectAlternative(alternative.dataset.selectAlternative);
  const askCandidate = event.target.closest("[data-ask-policy]"); if (askCandidate) { byId("qa-policy").value = askCandidate.dataset.askPolicy; byId("qa-section").scrollIntoView({ behavior: "smooth" }); byId("chat-question").focus(); return; }
  const level = event.target.closest("[data-map-level]");
  if (level?.dataset.mapLevel === "district") resetMapToSeoul();
  if (level?.dataset.mapLevel === "dong" && byId("district-select").value) { byId("dong-select").value = ""; state.selectedDong = ""; clearSelectedArea(); refreshAreaList(); renderDongCircles(true); }
  if (level?.dataset.mapLevel === "area" && byId("dong-select").value) renderAreaCircles(filteredAreas(), true);
});
document.addEventListener("keydown", (event) => {
  const card = event.target.closest(".alternative-card[data-select-alternative]");
  if (card && !event.target.closest("button") && ["Enter", " "].includes(event.key)) { event.preventDefault(); selectAlternative(card.dataset.selectAlternative); }
});

byId("district-select").addEventListener("change", (event) => event.target.value ? chooseDistrict(event.target.value, true) : resetMapToSeoul());
byId("dong-select").addEventListener("change", (event) => event.target.value ? chooseDong(byId("district-select").value, event.target.value, true) : renderDongCircles(true));
byId("area-search").addEventListener("input", () => { refreshAreaList(); const query = byId("area-search").value.trim(); if (query) renderAreaCircles(filteredAreas(), true); else if (byId("dong-select").value) renderAreaCircles(filteredAreas(), true); else if (byId("district-select").value) renderDongCircles(true); else renderDistrictCircles(true); });
byId("area-select").addEventListener("change", (event) => selectArea(event.target.value));
byId("industry-major-select").addEventListener("change", (event) => { populateIndustries(event.target.value); updateSummary(); });
byId("industry-select").addEventListener("change", () => { updateSummary(); refreshComparisonForMarketChange(); });
byId("business-next").addEventListener("click", () => { try { validateBusiness(); showStep("finance"); } catch (error) { toast(error.message); } });
byId("add-revenue-month").addEventListener("click", () => { if (state.revenueMonths < 12) { state.revenueMonths += 1; renderRevenueMonths(); } });
["opening-cash", "monthly-rent", "monthly-labor", "monthly-purchase", "loan-balance"].forEach((id) => byId(id).addEventListener("input", updateSummary));
byId("run-diagnosis").addEventListener("click", () => runComparison("diagnosis"));
byId("apply-staged-answers").addEventListener("click", () => runComparison("decision", false));
byId("diagnosis-next").addEventListener("click", () => showStep("decision"));
byId("run-csv").addEventListener("click", runCsvBaseline);
byId("comparison-chart").addEventListener("click", selectChartLine);
document.querySelectorAll("input[name=market-scenario]").forEach((node) => node.addEventListener("change", async () => {
  state.scenario = node.value;
  updateSummary();
  if (!state.data) return;
  const completed = await runComparison("diagnosis", false);
  if (completed) {
    const result = byId("diagnosis-result");
    result.scrollIntoView({ behavior: "smooth", block: "start" });
    result.focus({ preventScroll: true });
  }
}));
document.querySelectorAll("input[name=goal]").forEach((node) => node.addEventListener("change", () => { state.goal = node.value; if (state.data) runComparison("decision"); }));
byId("conditional-assumption").addEventListener("change", () => { if (state.data) runComparison("diagnosis"); });
byId("chat-send").addEventListener("click", askPolicy);
byId("chat-question").addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); askPolicy(); } });
byId("dialog-close").addEventListener("click", () => byId("alternative-dialog").close());
byId("dialog-ai").addEventListener("click", () => { byId("alternative-dialog").close(); byId("qa-section").scrollIntoView({ behavior: "smooth" }); byId("chat-question").focus(); });
byId("alternative-dialog").addEventListener("click", (event) => {
  const dialog = event.currentTarget;
  const rect = dialog.getBoundingClientRect();
  const inside = event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
  if (!inside) dialog.close();
});
window.addEventListener("resize", () => state.data && renderCharts(), { passive: true });

const today = new Date();
byId("csv-reference").value = today.toISOString().slice(0, 10);
renderRevenueMonths();
updateChatLimit();
loadCatalogs().catch(() => toast("상권과 업종 목록을 불러오지 못했습니다."));
