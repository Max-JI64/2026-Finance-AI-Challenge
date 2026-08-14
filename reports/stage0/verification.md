# Stage 0 검증 기록

## 구현 범위

- Python 3.13.1 실행 환경과 고정 의존성
- 원본·중간·가공 데이터, 모델, RAG, 앱 코드의 폴더 분리
- YAML 중앙 설정과 난수 시드
- 환경변수 기반 비밀키 관리
- FastAPI 최소 애플리케이션의 `/health`, `/scope`
- MVP 포함·제외 범위 문서
- 자동화된 설정·구조·API 테스트

## 현재 환경 검증

| 항목 | 결과 | 증거 |
| --- | --- | --- |
| Python 버전 | 통과 | `C:\Program Files\Python313\python.exe --version` |
| 필수 패키지 Import | 통과 | `scripts/verify_stage0.ps1` |
| 자동 테스트 | 통과 — 8개 | `scripts/verify_stage0.ps1` → `8 passed` |
| 실제 HTTP 상태 응답 | 통과 | Uvicorn `GET /health` → HTTP 200 |
| 비밀값 미포함 예시 | 통과 | `tests/test_project_structure.py` |

## 완료 처리하지 않는 항목

- 팀 전체가 예측 대상과 제외 범위를 동일하게 설명하는지 확인
- 별도의 팀원 환경에서 README만 보고 설치·테스트·서버 실행 확인

위 두 항목은 담당 팀원의 실제 확인 결과가 있어야만 체크리스트에서 완료 처리합니다.
