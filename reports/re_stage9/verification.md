# RE Stage 9 로컬 자동 QA

- 계약: `re9-v1` / 기준일: 2026-08-17
- 가상 페르소나: `8/8`
- 대표 10개 정책 공식근거 검색: `20/20` Hit@5
- 금지된 긍정 주장: `0건`
- 스크린샷 이미지 분석: 사용자 요청에 따라 미실시
- 외부 URL·운영계정·실제 Usage tier·운영 API 키: 사용자 배포 결정 전 미검증

## 페르소나 결과

| ID | 상황 | 목표 | 1순위 | 검색 | 통과 |
| --- | --- | --- | --- | --- | --- |
| P01 | 상권 하락·낮은 부채 | 최소부채 | cost_reduction_5 | bm25_fallback | 통과 |
| P02 | 안정 상권·높은 상환부담 | 최소상환 | cost_reduction_5 | bm25_fallback | 통과 |
| P03 | 상권 하락·현금 부족·기존 부채 | 최장생존 | cost_reduction_5 | bm25_fallback | 통과 |
| P04 | 사후환급 지급 지연 | 빠른실행 | cost_reduction_5 | bm25_fallback | 통과 |
| P05 | 단계형 확인 후 동적 기업지원 | 최소부채 | cost_reduction_5 | bm25_fallback | 통과 |
| P06 | 명확한 자격 부적격 | 최소부채 | cost_reduction_5 | bm25_fallback | 통과 |
| P07 | 자격 충족·접수 종료 | 최소부채 | cost_reduction_5 | bm25_fallback | 통과 |
| P08 | Embedding 2회 실패·BM25 전환·오류 입력 | 최소부채 | cost_reduction_5 | bm25_fallback | 통과 |

## 해석 경계

이 결과는 고정 가상 사업장의 기능·수치 일치 검증이다. 실제 사용성, 만족도, 정책 승인 가능성 또는 정책의 현실 효과를 입증하지 않는다.
