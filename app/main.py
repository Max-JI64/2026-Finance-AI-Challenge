"""RE8 FastAPI application for the policy-finance impact simulator."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.cashflow import SimpleCashflowInput
from src.integration.re_stage8 import (
    API_VERSION,
    CsvCashflowRequest,
    EligibilityRequest,
    PolicyQuestionRequest,
    SampleCompareRequest,
    VERSIONS,
    area_catalog,
    area_map_catalog,
    ask_policy,
    calculate_csv_baseline,
    calculate_simple_baseline,
    compare_sample,
    eligibility_results,
    envelope,
    industry_catalog,
    market_scenario,
    policy_catalog,
    service_contract,
)
from src.settings import PROJECT_ROOT


STATIC_DIR = PROJECT_ROOT / "app/static"
MAX_REQUEST_BYTES = 2 * 1024 * 1024

app = FastAPI(
    title="정책금융 영향 시뮬레이터",
    version=API_VERSION,
    description=(
        "13주와 6개월 기준 현금흐름에서 무대응과 정책금융 개입의 현금 및 부채 영향을 비교합니다."
    ),
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def enforce_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(
            status_code=413,
            content={"error": "request_too_large", "message": "요청 크기는 2MB 이하여야 합니다."},
        )
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
        for item in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error": "invalid_input", "message": "입력값을 수정해 주세요.", "details": details},
    )


@app.exception_handler(ValueError)
async def value_error(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_request",
            "message": "요청 내용을 처리할 수 없습니다. 입력 형식과 범위를 확인해 주세요.",
        },
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "version": API_VERSION, "versions": VERSIONS}


@app.get("/scope")
def scope() -> dict[str, object]:
    return {
        "geography": "Seoul",
        "predicts": "다음 분기 상권·업종 매출환경 악화 위험",
        "separates": ["상권환경 위험", "사업체 금융부담"],
        "does_not_predict": [
            "개별 점포 폐업확률",
            "개인 신용평가",
            "부도확률",
            "대출 승인 가능성",
        ],
        "implementation_status": "re8_integrated_mvp",
    }


@app.get("/api/v1/service-contract")
def get_service_contract() -> dict[str, object]:
    return service_contract()


@app.get("/api/v1/catalog/areas")
def get_areas() -> dict[str, object]:
    return envelope(items=area_catalog())


@app.get("/api/v1/catalog/area-map")
def get_area_map() -> dict[str, object]:
    return envelope(items=area_map_catalog())


@app.get("/api/v1/catalog/industries")
def get_industries() -> dict[str, object]:
    return envelope(items=industry_catalog())


@app.get("/api/v1/catalog/policies")
def get_policies() -> dict[str, object]:
    return envelope(items=policy_catalog())


@app.get("/api/v1/market-scenarios/{area_code}/{industry_code}")
def get_market_scenarios(area_code: str, industry_code: str) -> dict[str, object]:
    return market_scenario(area_code, industry_code)


@app.post("/api/v1/cashflow/baseline")
def baseline(data: SimpleCashflowInput) -> dict[str, object]:
    return calculate_simple_baseline(data)


@app.post("/api/v1/cashflow/csv")
def csv_baseline(data: CsvCashflowRequest) -> dict[str, object]:
    return calculate_csv_baseline(data)


@app.post("/api/v1/policies/eligibility")
def eligibility(data: EligibilityRequest) -> dict[str, object]:
    return eligibility_results(data)


@app.post("/api/v1/simulations/policy-impact")
def policy_impact(data: SampleCompareRequest) -> dict[str, object]:
    return compare_sample(data)


@app.post("/api/v1/alternatives/compare")
def alternatives_compare(data: SampleCompareRequest) -> dict[str, object]:
    return compare_sample(data)


@app.post("/api/v1/ai/ask")
def ai_ask(data: PolicyQuestionRequest) -> dict[str, object]:
    return ask_policy(data)
