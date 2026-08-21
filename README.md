https://daker.ai/public/hackathons/2026-finance-ai-challenge



# 정책금융 영향 시뮬레이터

서울 소상공인이 **정책 지원 전후의 13주 현금과 6개월 부채**를 같은 일정에서 비교하는 MVP입니다. 무대응, 비용절감, 비차입 지원, 대환, 신규 정책자금, 복합안을 함께 계산하고 공식 근거와 실행계획을 제공합니다.

현재 **Stage 0~6과 RE Stage 1~8.2**를 완료했고, **RE Stage 8.3 사용자 직접 서비스 검토·수정**을 진행합니다. FastAPI 4단계 화면, 서울 상권 지도, 최근 3~12개월 재무 입력, 17개 정책 Hybrid 후보발굴, 단계형 자격질문, 검수 Event 동적 대안, 결정론 순위와 GPT-5.6 Luna 설명 Fallback을 포함합니다. 기존 RE9 기준선에서 가상 페르소나 8/8과 대표 10개 정책 검색 20/20을 재현했지만, 사용자 수정이 끝나면 다시 검증합니다. 외부 배포는 중단했으며 향후 별도 승인 후 지속 무료 요금제만 사용합니다. 개인 매출·폐업·승인확률은 예측하지 않습니다.

## 예측 범위

- 계산함: 13주·6개월 현금흐름, 고갈시점, 신규부채, 월상환, 총이자
- 구분함: 상권환경 스트레스, 사업체 현금흐름, 정책 자격, 정책 접수상태
- 구현함: 규칙 기반 자격·후보 라우팅, 목표별 결정론적 비교, SQLite 공식자료 RAG, 선택적 Luna 설명
- 예측·판단하지 않음: 개별 점포 미래매출·폐업확률, 개인 신용평가, 부도확률, 대출 승인 가능성, 정책 인과효과

자세한 포함·제외 범위는 [reports/stage0/mvp_scope.md](reports/stage0/mvp_scope.md)를 확인하세요.

## 실행 환경

- Windows 기준 Python 3.13.1
- 패키지는 `requirements.txt`에 검증된 버전을 고정
- API 키는 환경변수로만 제공하며 저장소·로그·로컬 DB에 기록하지 않음
- 난수 시드와 주요 경로·임계값·가중치는 `config/settings.yaml`에서 관리

## 처음 실행하기

PowerShell에서 프로젝트 루트로 이동한 뒤 실행합니다.

```powershell
& 'C:\Program Files\Python313\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

테스트:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

RE8 로컬 정책근거 DB 재생성:

```powershell
& 'C:\Program Files\Python313\python.exe' .\scripts\build_re_stage8_local_db.py
```

RE8.1 상권 지도와 최신 모델 입력자료 재생성은 사용자가 원본 상권 Shapefile을 내려받아 지정 폴더에 둔 뒤 실행합니다.

```powershell
& 'C:\Program Files\Python313\python.exe' .\scripts\build_re_stage8_service_data.py
```

OpenAI 설명을 사용할 때 현재 PowerShell 프로세스에 새 키를 설정합니다. 채팅이나 파일에 키를 붙여 넣지 마세요.

```powershell
$env:OPENAI_API_KEY='새로 발급한 키'
$env:OPENAI_MODEL='gpt-5.6-luna'
```

개발 서버:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

서버 실행 후 아래 주소를 확인합니다.

- 상태 확인: `http://127.0.0.1:8000/health`
- 웹 화면: `http://127.0.0.1:8000/`
- 현재 서비스 계약: `http://127.0.0.1:8000/api/v1/service-contract`
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
app/                 FastAPI 통합 API와 정적 웹 화면
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

RE8 API·기능 검증은 `reports/re_stage8/`, RE8.2 Hybrid 계약은 `reports/re_stage8_2/`, RE9 로컬 QA·기능명세·Runbook은 `reports/re_stage9/`에 기록합니다.
