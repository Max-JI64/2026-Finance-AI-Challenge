# 버팀AI V5

V5는 V4를 독립 복사한 뒤, 사용자가 고른 해결 목적을 정책 검토 순서, 지표 강조, 공고 확인 순서까지 연결한 정책금융 코파일럿이다. V4와 공용 금융 엔진은 수정하지 않는다.

## 사용자 흐름

화면에는 `진단 → 비교 → 준비` 세 단계만 보인다.

1. 상권과 업종, 최근 매출, 현금, 비용, 대출을 입력한다.
2. 현금 생존, 부채 부담, 비용 절감, 정책 유형 비교 중 주된 해결 목적 하나를 고른다.
3. 13주 현금과 6개월 부채 진단 뒤 AI 검토 계획을 확인한다.
4. 질문을 거치지 않고 정책 후보를 확인해 최대 3개를 고른다.
5. 선택한 정책은 기존 순위와 별개인 `검토 순서`로 살펴본다.
6. 준비 화면에서 해당 정책에 필요한 조건을 `예`, `아니오`, `모름` 또는 값으로 직접 선택한다. 선택할 때마다 자격 상태와 계산 가능한 정책 효과를 다시 확인한다.
7. 저장 공고에서는 지금 확인할 신청정보 한 항목을 먼저 본다.

`무엇부터 확인할지 모르겠음`을 고르면 재무 신호에 맞는 검토 기준을 제안하지만 자동으로 확정하지 않는다.

## 금융 권한 경계

공식 Rule, 정책 Event, 현금흐름 엔진이 자격, 금액, 효과, 기존 순위를 결정한다. V5 검토 렌즈는 다음 값의 표시 순서만 바꾼다.

- 선택 정책의 검토 순서와 기본 초점
- 비교 지표 순서
- 공고 필드 확인 순서
- 검증된 사실의 설명 순서

조건부 정책은 기존 계약대로 순위에서 제외한다. V5는 승인 가능성, 개인 매출, 정책 선정 또는 실제 수급을 예측하지 않는다.

## 공고 분석과 저장

- 원본은 공용 공개 공고 인덱스 `rag/index/policy_re8.sqlite3`를 읽는다.
- V5 캐시는 `v5/runtime/notice_extraction_cache.sqlite`로 분리한다.
- Luna는 저장 공고의 신청 기간, 신청 경로, 금융 조건, 필요 서류, 문의처, 게시일을 구조화한다.
- 서버가 Chunk ID, 인용문, 숫자 근거를 확인한 필드만 표시한다.
- 검증 실패나 누락 필드는 값을 채우지 않고 공식 공고 직접 확인으로 남긴다.
- 사용자 재무 입력과 정책별 조건 선택값은 `sessionStorage`에만 두며 공고 캐시에 저장하지 않는다.

임의 신청서류 업로드와 OCR, 사용자 데이터 장기 저장, 계좌 연동, 외부 알림, 기관 전송, 자동 신청은 포함하지 않는다. 외부 AI가 없어도 재무 진단과 정책 비교는 완료할 수 있다.

## 실행

Windows Codex에서는 프로젝트 규칙에 따라 일반 CPython 3.13을 승인된 `Start-Process` 경로로 실행한다.

```powershell
$p = Start-Process -FilePath 'C:\Program Files\Python313\python.exe' -ArgumentList @('-m','uvicorn','v5.main:app','--host','127.0.0.1','--port','8003') -WorkingDirectory 'D:\대회\2026 금융 AI Challenge' -WindowStyle Hidden -PassThru
```

브라우저 주소는 `http://127.0.0.1:8003/`이다. 발표 프리셋은 `http://127.0.0.1:8003/?demo=1`에서만 보이며 입력값만 채운다.

## 검증

```powershell
$p = Start-Process -FilePath 'C:\Program Files\Python313\python.exe' -ArgumentList @('-m','pytest','v5\tests\test_v5.py','-q') -WorkingDirectory 'D:\대회\2026 금융 AI Challenge' -Wait -PassThru -NoNewWindow
exit $p.ExitCode
```

평가 Oracle은 `reports/v5/evaluation/`에 있다.

- 검토 렌즈 25개
- 정책별 준비 조건 계약
- 사용자 흐름 페르소나 8개

기존 `question_planner_cases.json`은 앞단 질문 게이트를 사용하던 설계의 이력 파일이며 현재 실행 경로와 회귀 기준에는 사용하지 않는다.

V4 복사 직후 증거는 `V4_COPY_BASELINE_SHA256.md`, 현재 검증 결과와 미검증 범위는 `VERIFICATION.md`에 기록한다.
