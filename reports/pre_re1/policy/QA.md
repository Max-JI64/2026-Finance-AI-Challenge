# P-01·P-03·P-04·P-05 사전 QA 보고서

## 판정

- 결과: **사전 QA 및 무손실 후보 통합 통과**
- RE Stage 1 상태: **미승인**
- 허용 범위: 원본 보존, 출처·형식·중복·건수 QA, 공통 스키마 변환, 정확 제목 그룹화
- 수행하지 않은 것: 퍼지매칭, 후보 제외, 대표 정책 순위화, 최종 8~12개 선정, 자격 Rule·금융 Event 확정

## 전수 확인 결과

| 항목 | 결과 |
| --- | ---: |
| 원본 인벤토리 파일 | 44개 |
| P-01 후보 CSV | 257건 |
| P-05 후보 CSV | 725건 |
| 기존 P-01↔P-05 정확 제목 교차행 | 197건 |
| 기존 P-01 정확제목 미매칭 후보 | 66건 |
| P-03 정책자금 공식 요약 Seed | 13건 |
| P-04 서울시 육성자금 Seed | 1건 |
| P-04 서울시 종합지원 Seed | 9건 |
| 통합 소스 레코드 | 1,005건 |
| 정확 제목 후보 그룹 | 827개 |
| 둘 이상 소스가 연결된 그룹 | 174개 |

## P-01·P-05

- 기존 Manifest와 후보 CSV 행 수가 일치한다.
- 기존 원본 응답, 파생 CSV·JSONL, QA와 정확 제목 Crosswalk를 재사용했다.
- P-05 날짜 필터는 등록일이 아니라 수정일 기준이라는 기존 제한을 유지했다.
- 정확 제목 일치는 공식 자격 검증이 아니다.

## P-03 소진공

- `정책자금 한눈에 보기.md`에서 직접대출·대리대출 13종을 파싱했다.
- 기준금리와 가산금리·고정금리 표현이 구분되어 있다.
- 제외업종과 재해자금 허용 예외가 함께 보존되어 있다.
- 정책별 세부 공지와 첨부파일은 아직 없으므로 자격 Rule·상환 Event를 확정할 수 없다.
- 원본 Markdown을 수정하지 않고 `data/raw_re/policy/semas/manifest.json`에 URL·파일시각·SHA-256을 추가했다.

## P-04 서울시

- 최초 안내 첨부 3개, 변경공고와 별표 3개, 소상공인 종합지원 안내 1개를 확인했다.
- 변경공고 본문에 서울특별시공고 제2026-1433호와 2026-05-04가 기록되어 있다.
- 별표 1은 최초본과 변경공고본이 SHA-256까지 동일하다.
- 별표 2와 별표 3은 차이가 있어 자동으로 어느 값을 채택하지 않았다.
- 전체 줄 차이는 `reports/pre_re1/policy/seoul_version_diff.md`에 보존했다.
- 원본 Markdown을 수정하지 않고 `data/raw_re/policy/seoul_fund/2026/manifest.json`에 URL·파일시각·SHA-256을 추가했다.

## 알려진 품질 제한

- 수동 저장 Markdown에는 출처 URL과 확인일이 본문에 없는 파일이 있어 별도 Manifest로 보완했다.
- 파일 수정시각은 로컬 저장시각 근거이며, 웹페이지 게시·적용일과 같은 의미가 아니다.
- P-03은 요약 페이지이고 P-04 종합지원 페이지도 개별 사업 공고가 아니므로 최종 원문 묶음이 아니다.
- 퍼지매칭과 의미기반 통합은 사용자 승인 전 수행하지 않았다.
- 다운로드 완료는 RE Stage 1 승인이나 최종 정책 채택을 의미하지 않는다.

## 산출물

- `reports/pre_re1/policy/source_inventory.csv`
- `reports/pre_re1/policy/qa_summary.json`
- `reports/pre_re1/policy/seoul_version_diff.md`
- `reports/pre_re1/policy/selection_decision_needed.md`
- `data/processed_re/policy/pre_re1/source_records.csv`
- `data/processed_re/policy/pre_re1/candidate_groups.csv`
- `data/raw_re/policy/semas/manifest.json`
- `data/raw_re/policy/seoul_fund/2026/manifest.json`
