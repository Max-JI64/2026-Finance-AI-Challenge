# RE8.2 구현 검증

- 상태: 구현·승인·확대평가 완료, Gate 통과
- 정책: 17개
- 사용자 검토 Markdown Chunk: 817개
- 저장 HTML 본문 검색·Embedding: 0개
- Embedding: small 1536차원 817행, large 3072차원 817행
- 사용자 질의·범주형 상황요약 영구저장: 없음
- OpenAI 장애 Fallback: BM25 자동 테스트 통과
- Embedding 요청: 5초 Timeout, 최초 1회 + 오류 재시도 1회, 이후 BM25
- 자격·접수·버전·Fallback 안전성: 8/8 통과

## 검색 평가

| 방식 | Recall@5 | Hit@5 | MRR |
| --- | ---: | ---: | ---: |
| bm25 | 0.953 | 0.969 | 0.823 |
| vector-small | 0.922 | 0.969 | 0.712 |
| hybrid-small | 0.984 | 1.000 | 0.889 |
| vector-large | 0.984 | 1.000 | 0.799 |
| hybrid-large | 1.000 | 1.000 | 0.872 |


사용자 승인 모델은 `text-embedding-3-large` 3,072차원 Hybrid이며, 확대 평가 Gate를 통과했다.
