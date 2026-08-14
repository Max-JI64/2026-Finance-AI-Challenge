https://daker.ai/public/hackathons/2026-finance-ai-challenge



# 서울 소상공인 AI 금융 생존 내비게이터

서울시 상권·업종의 **다음 분기 매출환경 악화 위험**을 예측하고, 사용자가 입력한 사업체 금융부담을 별도로 진단한 뒤 공식 정책자료에 근거한 지원정책 추천과 설명을 제공하는 MVP입니다.

현재 상태는 **Stage 0 개발 기반 구축**입니다. 실제 데이터, 학습 모델, 정책 추천 및 RAG 기능은 아직 구현되지 않았으며 고정된 예시 결과를 반환하지 않습니다.

## 예측 범위

- 예측함: 서울시 `상권 × 업종`의 다음 분기 매출환경 악화 위험
- 별도 계산함: 사용자 입력 기반 사업체 금융부담
- 구현함: 규칙 기반 정책 후보 필터·순위와 공식자료 기반 RAG 설명
- 예측·판단하지 않음: 개별 점포 폐업확률, 개인 신용평가, 부도확률, 대출 승인 가능성, 실제 대출심사

자세한 포함·제외 범위는 [reports/stage0/mvp_scope.md](reports/stage0/mvp_scope.md)를 확인하세요.

## 실행 환경

- Windows 기준 Python 3.13.1
- 패키지는 `requirements.txt`에 검증된 버전을 고정
- API 키는 `.env.example`을 복사한 `.env` 또는 배포 환경변수로만 제공
- 난수 시드와 주요 경로·임계값·가중치는 `config/settings.yaml`에서 관리

## 처음 실행하기

PowerShell에서 프로젝트 루트로 이동한 뒤 실행합니다.

```powershell
& 'C:\Program Files\Python313\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

테스트:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Stage 0 전체 확인:

```powershell
.\scripts\verify_stage0.ps1 -PythonPath '.\.venv\Scripts\python.exe'
```

개발 서버:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

서버 실행 후 아래 주소를 확인합니다.

- 상태 확인: `http://127.0.0.1:8000/health`
- 서비스 범위: `http://127.0.0.1:8000/scope`
- API 문서: `http://127.0.0.1:8000/docs`

## 폴더 구조

```text
data/raw/            내려받은 원본(수정 금지)
data/interim/        정제·결합 중간 산출물
data/processed/      학습·서비스용 최종 데이터
models/              모델과 전처리 객체
rag/documents/       정책 원문 또는 정제 문서
rag/metadata/        구조화한 정책 조건
rag/index/           검색 인덱스
src/data/            수집·검증·전처리
src/features/        Feature 생성
src/modeling/        학습·평가·예측
src/finance/         금융부담 진단
src/recommendation/  정책 필터와 Ranking
src/rag/             검색과 근거 기반 답변
app/                 웹 API와 향후 화면
tests/               핵심 로직 테스트
reports/             QA·성능·데모 증거
config/              경로·임계값·가중치·시드
```

## 데이터 원칙

1. 원본 파일은 `data/raw/`에 저장한 뒤 수정하지 않습니다.
2. 출처, 다운로드일, 대상 기간, 파일 크기, 행·열 수를 데이터 목록에 남깁니다.
3. Panel Dataset은 `연도 + 분기 + 상권코드 + 서비스업종코드`를 기본 키로 사용합니다.
4. 모델 검증은 시간순 분할을 사용하고 미래정보 누수를 허용하지 않습니다.
5. 데이터나 공식 근거가 없으면 임의의 점수·자격·정책 내용을 생성하지 않습니다.

## 현재 확인 명령

시스템 Python에 의존성이 이미 설치된 개발 환경에서는 다음 명령으로 바로 확인할 수 있습니다.

```powershell
& 'C:\Program Files\Python313\python.exe' -m pytest
```

현재 개발 환경의 검증 결과와 아직 사람이 확인해야 할 항목은 `reports/stage0/verification.md`에 기록합니다.

