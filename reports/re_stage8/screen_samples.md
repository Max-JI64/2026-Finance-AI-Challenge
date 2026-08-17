# RE Stage 8 화면별 샘플

모든 이미지는 로컬 FastAPI 서버를 실제 Chromium 브라우저에서 열어 저장했다. 샘플 수치는 실제 사업장이 아닌 RE7 동결 가상 사업장과 RE8 간편입력 검증값이다.

| 화면 | 데스크톱 | 추가 검증 |
| --- | --- | --- |
| 서비스 안내 | `screens/01_intro_desktop.png` | `screens/01_intro_mobile.png` |
| 사업장 선택 | `screens/02_business_desktop.png` | 상권·업종 목록 로드 확인 |
| 재무 입력 | `screens/03_finance_desktop.png` | 검증 샘플·간편입력·CSV UI |
| 기준 현금흐름 | `screens/04_baseline_desktop.png` | 13주·6개월·부채 반환 계약 테스트 |
| 상권환경 | `screens/05_stress_desktop.png` | 직접 충격률 Fallback |
| 정책 자격 | `screens/06_eligibility_desktop.png` | 자격·접수상태·조건부 가정 분리 |
| 정책금융 영향 비교 | `screens/07_comparison_desktop.png` | `screens/07_comparison_mobile.png` |
| 실행계획·AI | `screens/08_plan_desktop.png` | 로컬 RAG Fallback 실제 화면 확인 |

브라우저 검증에서 간편입력 계산, 조건부 가정 해제, 로컬 RAG Fallback까지 클릭 흐름을 실행했다. 모바일은 390×844, 데스크톱은 기본 1440px급 뷰포트에서 확인했다.
