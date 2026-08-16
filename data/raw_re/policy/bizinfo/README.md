# 기업마당 중소기업 지원사업 공고 API 데이터

## 1. 데이터 개요

이 폴더에는 중소벤처기업부의 **중소기업 지원사업 공고 조회 서비스**에서 수집한 공고 원본과 분석 편의용 파생파일이 있다.

- 공식 명칭: 중소벤처기업부_중소기업 지원사업 공고 조회 서비스
- 공식 안내: [공공데이터포털 API 페이지](https://www.data.go.kr/data/15157820/openapi.do)
- API Endpoint: `https://apis.data.go.kr/1421000/bizinfo/pblancBsnsService`
- 제공 대상: 중앙부처·지방자치단체·유관기관의 중소기업 지원사업 공고
- 프로젝트 역할: 소상공인이 이용할 가능성이 있는 정책의 **광역 후보 탐색**
- 단독 사용 제한: 이 데이터만으로 소상공인 자격, 금리, 한도, 접수상태 또는 최종 정책조건을 확정하지 않는다.
- 최초 수집일: 2026-08-15

기업마당은 소상공인 전용 서비스가 아니다. 후보 정책은 소상공인24, 소상공인시장진흥공단, 서울시, 수행기관의 공식 상세 페이지와 공고문·첨부파일에서 다시 검증해야 한다.

## 2. 현재 수집 결과

| 항목 | 결과 |
| --- | ---: |
| API가 보고한 전체 건수 | 1,545건 |
| 저장한 원본 페이지 | 2개 |
| 고유 공고ID | 1,545건 |
| 공고ID 중복 | 0건 |
| 등록연도 2026 | 1,521건 |
| 등록연도 2025 | 23건 |
| 등록연도 2023 | 1건 |
| 2026년 소상공인 검토 후보 | 257건 |
| 핵심 필드 명시 후보 | 249건 |
| 공고명·사업개요 탐색 후보 | 8건 |

API의 공식 설명은 당해 연도 공고를 제공한다고 되어 있으나 실제 응답에는 2025년 23건과 2023년 1건이 포함됐다. 전체 응답은 원본 증거로 보존하고, 프로젝트에서 사용하는 당해 연도 범위는 `current_year_2026_items.*`로 분리했다.

## 3. 폴더 구조와 파일 용도

```text
bizinfo/
├─ README.md
└─ 2026-08-15/
   ├─ pages/
   │  ├─ page_0001.json
   │  └─ page_0002.json
   ├─ all_items.jsonl
   ├─ all_items.csv
   ├─ current_year_2026_items.jsonl
   ├─ current_year_2026_items.csv
   ├─ small_business_candidates.jsonl
   ├─ small_business_candidates.csv
   ├─ manifest.json
   └─ QA.md
```

| 파일 | 행·건수 | 설명 | 권장 용도 |
| --- | ---: | --- | --- |
| `pages/page_*.json` | 2개 페이지·1,545건 | API 응답을 그대로 저장한 원본 | 원본 재현·감사 |
| `all_items.jsonl` | 1,545행 | 전체 응답을 한 공고 한 줄로 정리 | 전체 응답 처리 |
| `all_items.csv` | 1,545행 | 전체 응답의 Excel·분석용 CSV | 범위 밖 연도 확인 포함 |
| `current_year_2026_items.jsonl` | 1,521행 | `creatPnttm` 등록연도가 2026인 공고 | 2026년 전체 공고 분석 |
| `current_year_2026_items.csv` | 1,521행 | 위 자료의 UTF-8 BOM CSV | 일반 분석의 기본 입력 |
| `small_business_candidates.jsonl` | 257행 | 2026년 자료에서 소상공인 관련 조건으로 찾은 검토 후보 | 후보 정책 검토 |
| `small_business_candidates.csv` | 257행 | 후보 분류 근거를 추가한 CSV | 수동 검토·정책 선별 |
| `manifest.json` | 1개 | 수집범위, 건수, 연도, 필드 채움 수, SHA-256 | 기계 판독 QA |
| `QA.md` | 1개 | 핵심 수집·검증 결과 | 빠른 품질 확인 |

CSV는 Excel에서 한글이 깨지지 않도록 UTF-8 BOM으로 저장했다. JSONL은 한 줄이 공고 1건이며 UTF-8이다.

## 4. 권장 사용 순서

1. 2026년 전체 공고가 필요하면 `current_year_2026_items.csv`를 사용한다.
2. 소상공인 관련 공고를 검토하려면 `small_business_candidates.csv`를 사용한다.
3. `candidate_reason`으로 후보가 선택된 필드와 이유를 확인한다.
4. 후보를 정책으로 채택하기 전에 `pblancUrl`, 신청 URL, 첨부파일과 해당 기관의 공식 원문을 확인한다.
5. 최종 자격·금융조건은 별도의 정책 Metadata·Rule·Event 구조에 공식 근거와 함께 기록한다.

`small_business_candidates.csv`는 정책 목록의 최종본이 아니다. 키워드가 일치해도 실제 지원대상에 소상공인이 없을 수 있으며, 반대로 표현 차이 때문에 후보에서 빠진 공고도 있을 수 있다.

## 5. 소상공인 후보 분류 기준

| 후보 등급 | 이번 건수 | 판정 기준 | 의미 |
| --- | ---: | --- | --- |
| `explicit_core` | 249건 | 지원대상·해시태그·지원분야·소관기관·수행기관에 `소상공인` 또는 소진공 기관명이 명시됨 | 우선 검토 후보 |
| `explicit_discovery` | 8건 | 공고명·사업개요·신청방법 등 탐색본문에 `소상공인`이 있음 | 본문 기준 추가 검토 후보 |
| `adjacent_review` | 0건 | 자영업·전통시장·상점가·골목상권 등 인접어만 일치 | 현재 수집에서는 없음 |

모든 후보의 `eligibility_status`는 `미확정_공식원문재검증필요`이다.

## 6. 원본 변수표

`비어 있지 않은 건수`는 원본 전체 1,545건을 기준으로 계산했다. API 명세상 모든 필드는 문자열이며, CSV에서도 문자열로 저장된다.

| 변수명 | 한글 의미 | 비어 있지 않은 건수 | 사용 시 주의 |
| --- | --- | ---: | --- |
| `pblancNm` | 공고명 | 1,545 | 정책명 후보와 교차확인의 기본값 |
| `pblancUrl` | 기업마당 상세 URL | 1,545 | 기업마당 상세 페이지이며 최종 원문 URL과 다를 수 있음 |
| `pblancId` | 공고 고유 ID | 1,545 | 기업마당 내부 기본키, 이번 수집 중복 0건 |
| `jrsdInsttNm` | 소관기관명 | 1,545 | 실제 수행기관과 구분 |
| `excInsttNm` | 수행기관명 | 1,545 | 지원 접수·집행기관 후보 |
| `bsnsSumryCn` | 사업개요 내용 | 1,545 | 자격과 금융조건의 최종 근거로 사용하지 않음 |
| `pldirSportRealmLclasCodeNm` | 정책지원 분야 대분류명 | 1,545 | 분야 분류와 후보 필터에 사용 가능 |
| `creatPnttm` | 등록일시 | 1,545 | 2026년 파생본의 연도 판정 기준 |
| `reqstBeginEndDe` | 신청기간 | 1,545 | 자유 텍스트이므로 날짜 구조화 후 원문 대조 필요 |
| `updtPnttm` | 수정일시 | 1,545 | 공고 변경 여부 추적에 사용 |
| `trgetNm` | 지원대상 | 1,545 | 소상공인 후보 필터의 핵심 필드지만 최종 자격근거는 아님 |
| `inqireCo` | 조회수 | 1,545 | 인기도 참고값이며 정책 적합도나 효과를 뜻하지 않음 |
| `flpthNm` | 첨부파일 경로명 | 1,111 | `fileNm`과 함께 사용하며 빈값 가능 |
| `fileNm` | 첨부파일명 | 1,111 | 복수·실제 다운로드 가능 여부 확인 필요 |
| `printFlpthNm` | 본문 출력파일 경로명 | 1,545 | 기업마당 내부 출력용 경로 |
| `printFileNm` | 본문 출력파일명 | 1,545 | 일반 첨부파일과 구분 |
| `hashtags` | 해시태그 | 1,545 | 후보 탐색용이며 자격조건으로 사용 금지 |
| `reqstMthPapersCn` | 신청방법·제출서류 내용 | 1,544 | 최신 접수방식은 공식 신청페이지에서 재확인 |
| `refrncNm` | 문의처 | 1,544 | 기관·부서·전화번호가 혼합될 수 있음 |
| `rceptEngnHmpgUrl` | 사업 신청 URL | 823 | 빈값이 많으며 링크 유효성과 공식성 확인 필요 |

## 7. 후보 파생변수표

다음 변수는 API 원본 필드가 아니라 `small_business_candidates.*` 생성 과정에서 추가됐다.

| 변수명 | 설명 | 값·예시 |
| --- | --- | --- |
| `candidate_tier` | 후보 탐색 강도 | `explicit_core`, `explicit_discovery`, `adjacent_review` |
| `candidate_match_fields` | 후보 조건이 일치한 원본 필드명 | `trgetNm|hashtags` 등 |
| `candidate_reason` | 일치한 필드와 키워드를 읽기 쉬운 문장으로 기록 | `소상공인 명시:trgetNm` 등 |
| `eligibility_status` | 자격 확정 여부 | 항상 `미확정_공식원문재검증필요` |

## 8. 품질과 해석 제한

- 원본 전체 1,545건, 페이지별 합계 1,545건, CSV·JSONL 행 수가 일치한다.
- `pblancId`는 모두 존재하며 중복이 없다.
- API 응답코드는 두 페이지 모두 `00`이다.
- 원본 페이지와 파생파일의 SHA-256은 `manifest.json`에 기록돼 있다.
- 인증키는 이 데이터 폴더의 산출물에 저장하지 않았다.
- API 정보에 일일 호출 한도가 없어 현재 `미확인`으로 기록했다.
- 기업마당 후보는 정책 자격·금리·지원한도·접수상태의 공식 증거가 아니다.
- 동일 공고명, 비슷한 내용, 동일 정책은 서로 다른 주장이다. ID나 공식 공고번호와 원문을 함께 확인해야 한다.

## 9. 재수집

재수집 코드는 [`scripts/collect_bizinfo.py`](../../../../scripts/collect_bizinfo.py)이다.

```powershell
& 'C:\Program Files\Python313\python.exe' 'scripts\collect_bizinfo.py' `
  --api-info 'data\raw_re\policy\bizinfo\API정보.md' `
  --expected-year 2026 `
  --collection-date YYYY-MM-DD
```

수집기는 인증키를 [`API정보.md`](API정보.md)에서 실행 시점에만 읽는다. 기존 날짜 폴더가 비어 있지 않으면 덮어쓰지 않는다.
