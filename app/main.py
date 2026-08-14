"""Stage 0 FastAPI entry point.

This module deliberately exposes only project metadata. Real risk scores and
recommendations must not be returned until data/model/policy evidence exists.
"""

from fastapi import FastAPI

from src.settings import load_settings


SETTINGS = load_settings()

app = FastAPI(
    title="서울 소상공인 AI 금융 생존 내비게이터",
    version=str(SETTINGS["project"]["version"]),
    description="상권환경 위험과 사업체 금융부담을 분리해 진단하는 MVP",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a dependency-free liveness response."""

    return {"status": "ok", "version": str(SETTINGS["project"]["version"])}


@app.get("/scope")
def scope() -> dict[str, object]:
    """Return the frozen prediction boundary used throughout the MVP."""

    prediction = SETTINGS["prediction"]
    return {
        "geography": prediction["geography"],
        "predicts": "다음 분기 상권·업종 매출환경 악화 위험",
        "separates": ["상권환경 위험", "사업체 금융부담"],
        "does_not_predict": [
            "개별 점포 폐업확률",
            "개인 신용평가",
            "부도확률",
            "대출 승인 가능성",
        ],
        "implementation_status": "stage_0_foundation",
    }

