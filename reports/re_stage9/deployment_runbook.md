# RE Stage 9 배포 Runbook

## 현재 상태

- 로컬 배포 패키지: 준비 완료
- 외부 플랫폼·계정·공개 URL: 사용자 결정 대기
- RE9 전체 Gate: 미통과
- Health Check: `GET /health`
- 실행 명령: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`

## 배포 전 준비

1. 사용자가 배포 플랫폼과 계정을 선택하고 외부 배포를 명시적으로 승인한다.
2. 저장소 또는 빌드 컨텍스트에 `.env`가 포함되지 않았는지 확인한다.
3. 플랫폼 Secret에 `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-5.6-luna`, `OPENAI_EMBEDDING_MODEL=text-embedding-3-large`를 설정한다.
4. 배포계정의 실제 Usage tier와 Embeddings·Responses API 사용 가능 여부를 확인한다.
5. `requirements-runtime.txt` 또는 `Dockerfile`로 빌드한다. 개발·학습 전용 패키지는 운영 이미지에 포함하지 않는다.

## 배포 명령

Docker를 지원하는 플랫폼에서 다음 계약을 사용한다.

```text
Build: docker build -t policy-finance-simulator .
Run:   docker run --rm -p 8000:8000 --env-file <운영자 전용 환경파일> policy-finance-simulator
```

환경파일은 저장소 밖에 두며 채팅·문서·로그에 키를 복사하지 않는다. 플랫폼이 `PORT`를 주입하면 컨테이너 시작 명령이 해당 값을 사용한다.

## 필수 운영 확인

1. `/health`가 HTTP 200과 `status=ok`를 반환한다.
2. `/`에서 4단계 화면이 열리고 정책 수 17개가 조회된다.
3. P01과 P08을 실행해 정상 계산과 Embedding 장애 BM25 Fallback을 확인한다.
4. 재시작 후 P03 결과의 입력 Hash와 핵심 수치가 동결 Oracle과 일치하는지 확인한다.
5. 5초 Timeout, 사용자 동작당 최대 2회, 이후 BM25 전환을 운영 로그의 오류 종류와 호출 횟수만으로 확인한다.
6. 요청 본문, 원금액, 자격 응답 원문, 정책 질문, API 키가 로그에 남지 않는지 확인한다.

## 로그와 개인정보

- 허용: 시각, HTTP 상태, 경로 Template, 처리시간, Fallback 발생 여부, 예외 종류
- 금지: 요청 본문, CSV 본문, 원금액, 상호명, 상세주소, 식별번호, 자격 응답 원문, 정책 질문, API 응답 본문, API 키
- 외부 전송 고지: 승인된 범주형 상황과 로컬 비식별 처리된 정책 질문만 전송하며 OpenAI 기본 악용 모니터링 로그에는 최대 30일 포함될 수 있다.

## 재시작·Rollback

1. 마지막 통과 이미지 Tag와 Git Commit을 기록한다.
2. 재시작 후 `/health`와 P01을 재실행한다.
3. 핵심 수치, 공식 링크, 개인정보 경계 중 하나라도 불일치하면 신규 이미지 트래픽을 중단하고 마지막 통과 이미지로 되돌린다.
4. 오류 원인과 변경 파일을 `reports/re_stage9/`에 기록한 뒤 다시 전체 Gate를 수행한다.

## 미완료 운영 항목

- 플랫폼·계정 선택
- 공개 URL 발급 및 제출기간 접근 보장
- 운영 API 키·Usage tier 확인
- 공개 URL 재시작 검증
- 공개 URL 데스크톱·모바일 DOM QA
- 데모 직전 정책 접수상태·변경공고 최종 확인
