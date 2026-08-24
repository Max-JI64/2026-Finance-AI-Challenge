"""Independent FastAPI entry point for the V3 user experience."""

from __future__ import annotations

import warnings

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.main import app as v2_app
from src.cashflow.errors import CashflowInputError

from src.integration.re_stage8 import (
    ActionBriefRequest,
    PolicyQuestionRequest,
    action_brief,
    area_map_catalog,
    ask_policy,
    envelope,
    industry_catalog,
    market_scenario,
    policy_catalog,
)
from src.settings import PROJECT_ROOT
from v3.orchestrator import (
    OrchestrateRequest,
    SituationRequest,
    WhatIfRequest,
    apply_what_if,
    interpret_situation,
    orchestrate_state,
)


API_VERSION = "v3-api-v1.0"
STATIC_DIR = PROJECT_ROOT / "v3/static"
MAX_REQUEST_BYTES = 2 * 1024 * 1024

app = FastAPI(
    title="버팀AI V3 — 현금위기 대응 에이전트",
    version=API_VERSION,
    description="필요한 질문과 금융 도구를 선택해 검증된 현금위기 대응 행동계획을 제공합니다.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="v3-static")


@app.middleware("http")
async def enforce_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(status_code=413, content={"error": "request_too_large", "message": "요청 크기는 2MB 이하여야 합니다."})
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
        for item in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"error": "invalid_input", "message": "입력값을 수정해 주세요.", "details": details})


@app.exception_handler(ValueError)
async def value_error(_: Request, exc: ValueError) -> JSONResponse:
    message = exc.message if isinstance(exc, CashflowInputError) else "입력 형식과 범위를 확인해 주세요."
    return JSONResponse(status_code=400, content={"error": "invalid_request", "message": message})


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "version": API_VERSION,
        "v2_preserved": True,
        "external_ai_default": "off",
        "session_persistence": "none",
    }


@app.get("/scope")
def scope() -> dict[str, object]:
    return {
        "geography": "Seoul",
        "implementation_status": "v3_independent_bounded_agent",
        "predicts": "상권·업종 집계 하방·기준·회복 시나리오",
        "does_not_predict": ["개별 점포 폐업", "대출 승인", "정책 선정", "개인 신용"],
        "v4_features_not_enabled": ["장기 저장", "자동 알림", "계좌 연동", "자동 신청"],
    }


@app.get("/api/v3/catalog/areas")
def get_areas() -> dict[str, object]:
    return envelope(items=area_map_catalog())


@app.get("/api/v3/catalog/industries")
def get_industries() -> dict[str, object]:
    return envelope(items=industry_catalog())


@app.get("/api/v3/catalog/policies")
def get_policies() -> dict[str, object]:
    return envelope(items=policy_catalog())


@app.get("/api/v3/market-scenarios/{area_code}/{industry_code}")
def get_market_scenarios(area_code: str, industry_code: str) -> dict[str, object]:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
            category=UserWarning,
        )
        return market_scenario(area_code, industry_code)


@app.post("/api/v3/situation/interpret")
def situation_interpret(data: SituationRequest) -> dict[str, object]:
    return interpret_situation(data)


@app.post("/api/v3/orchestrate")
def orchestrate(data: OrchestrateRequest) -> dict[str, object]:
    return orchestrate_state(data)


@app.post("/api/v3/what-if")
def what_if(data: WhatIfRequest) -> dict[str, object]:
    return apply_what_if(data)


@app.post("/api/v3/ai/action-brief")
def ai_action_brief(data: ActionBriefRequest) -> dict[str, object]:
    return action_brief(data)


@app.post("/api/v3/ai/ask")
def ai_ask(data: PolicyQuestionRequest) -> dict[str, object]:
    return ask_policy(data)


# V3 keeps the reviewed V2 screen and all V2 utility routes available, while
# the routes declared above replace only the orchestration layer and static UI.
app.mount("/", v2_app, name="v2-compat")
