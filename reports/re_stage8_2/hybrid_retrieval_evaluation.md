# RE8.2 BM25·Vector·Hybrid 검색 평가

- 고정 한국어 정답계약: 40건(검색 32건 + 안전성 8건)
- 동일 질문을 BM25 단독, Vector 단독, Hybrid에 적용
- 사용자 승인 선택: text-embedding-3-large 3072차원 + Hybrid

| 방식 | Candidate Recall@5 | Hit@5 | MRR | 총 지연(ms) |
| --- | ---: | ---: | ---: | ---: |
| bm25 | 0.953 | 0.969 | 0.823 | 1722.5 |
| vector-small | 0.922 | 0.969 | 0.712 | 15612.7 |
| hybrid-small | 0.984 | 1.000 | 0.889 | 4573.5 |
| vector-large | 0.984 | 1.000 | 0.799 | 22926.6 |
| hybrid-large | 1.000 | 1.000 | 0.872 | 7273.4 |

신규 4개 정책 Hit@5: 1.000
안전성: 8/8 통과
최종 품질 Gate: 통과
