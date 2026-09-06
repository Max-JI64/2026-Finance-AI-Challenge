# 3페이지 공고 분석 fallback

대상은 사용자 화면의 세 공고로 한정한다.

- 소상공인 경영안정 바우처
- 새 길 여는 폐업지원
- 소상공인 재도전특별자금

`static/notice-fallback-results.json`에는 2026-09-06 실제 배포 서비스의 `/api/v5/application/notice-extract`를 `force_refresh: true`로 호출해 받은 `gpt-5.6-luna` 성공 응답을 보존했다. 공고 자체의 저장 기준일은 응답의 `retrieved_at`이며, 분석 요청 시각과 다르다. 분석문·근거·미확인 항목은 변경하지 않았다. 현재 접수 여부나 자격을 보장하는 데이터가 아니다.

일반 페이지에서도 API 오류, 20초 클라이언트 제한, unavailable 응답, 비어 있거나 불완전한 결과 발생 시 자동 복구한다. 재분석 실패 시 기존 결과를 유지하고, 없으면 저장 JSON(2차), 해당 요청도 실패하면 같은 실제 응답의 브라우저 내장본(3차)을 사용한다. 가상 공고 분석은 생성하지 않는다. 다른 정책·공고 버전 또는 서버가 알려준 원문 digest가 일치하지 않으면 저장본을 대신 표시하지 않는다.

## 테스트 주소

- `/?demo=1&notice_fallback=1`: 공고 AI 요청 오류 → 저장 JSON
- `/?demo=1&notice_fallback=2`: 공고 AI 요청 및 저장 JSON 오류 → 내장본
- `/?demo=1`: 강제 오류 없이 실제 공고 AI 오류 때 자동 복구

두 테스트 주소에서 기존 흐름대로 위 세 정책 중 원하는 정책을 선택해 3페이지로 이동한다. 공고 카드 위에 `실제 GPT 분석 저장본`, fallback 단계, 분석 저장 시각, `새 AI 응답 아님`이 표시된다. 그래프 전용 `fallback=1/2`와는 독립적이다.

## 배포 및 검증

서비스 반영에는 `static/index.html`, `static/v5-extension.js`, 새 `static/notice-fallback.js`, 새 `static/notice-fallback-results.json`이 모두 필요하다. 기존 Dockerfile의 `COPY v5 ./v5`에 포함되며 별도 서버 설정은 없다. 배포는 사용자 소유다.

`node v5/tests/test_notice_fallback.cjs`는 정확히 세 정책만 존재하는지, 저장 원문의 인용·digest, 13가지 성공/오류 경로, 기존 카드 및 확인 순서, 재분석 결과 유지와 정책·버전 격리를 검증한다. 실제 브라우저 시각 검사는 별도다. 캡처 스크립트는 명시적으로 실행할 때만 외부 GPT를 호출하며, 기본 대상도 위 세 정책으로 제한했다.
