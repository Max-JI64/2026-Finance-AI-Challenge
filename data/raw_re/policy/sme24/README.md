# 중소벤처24 공고 API 데이터

## 1. 데이터 개요

이 폴더에는 중소기업기술정보진흥원의 **중소벤처24 공고정보 API**에서 수집한 원본, 소상공인 검토 후보, 기업마당 공고와의 교차확인 결과가 있다.

- 공식 명칭: 중소기업기술정보진흥원_중소벤처24 공고정보
- 공식 안내: [공공데이터포털 API 페이지](https://www.data.go.kr/data/15113191/openapi.do)
- API Endpoint: `https://portal.smes.go.kr/ione-gw/api/pblanc/list`
- 프로젝트 역할: 기업마당 공고의 공고명·기간·기관·첨부파일을 확인하는 **P1 보조 교차확인 자료**
- 단독 사용 제한: 소상공인 전용 API가 아니며 자격·금리·한도·접수상태의 단독 근거로 사용하지 않는다.
- 최초 수집일: 2026-08-15
- 요청기간: 2026-01-01~2026-08-15

## 2. 날짜 범위의 실제 의미

API 명세는 `strDt`와 `endDt`를 검색 시작일·종료일로 설명하지만 어느 날짜 필드에 적용되는지는 명시하지 않는다. 실제 원본을 검증한 결과, 8개 요청 구간에서 **모든 응답의 `updDt`가 해당 요청 구간 안에 있었다.**

따라서 이 폴더의 범위는 다음과 같이 해석한다.

> 2026-01-01부터 2026-08-15까지 등록되었거나 갱신된 공고가 아니라, 정확히는 **해당 기간에 `updDt`가 기록된 공고**이다.

등록일 `creatDt` 기준 분포는 2026년 4,483건, 2025년 523건, 등록일 미제공 2,667건이다. 과거 등록 또는 등록일 미상 공고도 2026년에 수정됐다면 API 응답 범위에 포함되므로 삭제하지 않았다.

## 3. 현재 수집 결과

| 항목 | 결과 |
| --- | ---: |
| 성공한 월별 요청 구간 | 8개 |
| 원본 응답 항목 | 7,673건 |
| 고유 공고SEQ | 7,673건 |
| 공고SEQ 중복 | 0건 |
| `updDt`가 요청 구간에 포함 | 7,673건 |
| 소상공인 검토 후보 | 725건 |
| 코드 명시 후보 | 97건 |
| 텍스트 명시 후보 | 628건 |
| 기업마당 전체 정확 제목 교차일치 | 1,284행 |
| 교차일치한 고유 기업마당 ID | 1,244건 |
| 교차일치한 고유 중소벤처24 SEQ | 1,267건 |
| 기업마당 소상공인 후보 중 정확 일치 | 191건 |
| 기업마당 소상공인 후보 중 정확 일치 없음 | 66건 |

동일한 정규화 제목을 가진 공고가 한쪽에 여러 건 있을 수 있어 교차확인 행 수와 고유 ID·SEQ 수는 다르다.

## 4. 폴더 구조와 파일 용도

```text
sme24/
├─ README.md
└─ 2026-08-15/
   ├─ windows/
   │  ├─ window_20260101_20260131.json
   │  ├─ ...
   │  └─ window_20260801_20260815.json
   ├─ all_items.jsonl
   ├─ all_items.csv
   ├─ small_business_candidates.jsonl
   ├─ small_business_candidates.csv
   ├─ bizinfo_exact_title_crosswalk.csv
   ├─ bizinfo_candidate_exact_title_crosswalk.csv
   ├─ bizinfo_candidates_without_exact_sme24_match.csv
   ├─ sme24_small_business_candidates_without_exact_bizinfo_match.csv
   ├─ manifest.json
   └─ QA.md
```

| 파일 | 행·건수 | 설명 | 권장 용도 |
| --- | ---: | --- | --- |
| `windows/window_*.json` | 8개·7,673건 | 월별 API 응답 원본 | 원본 재현·감사 |
| `all_items.jsonl` | 7,673행 | 공고SEQ 기준 고유 공고 JSONL | 프로그램 처리 |
| `all_items.csv` | 7,673행 | 고유 공고의 UTF-8 BOM CSV | 전체 공고 분석 |
| `small_business_candidates.jsonl` | 725행 | 코드·텍스트 기반 소상공인 검토 후보 | 후보 처리 |
| `small_business_candidates.csv` | 725행 | 후보 근거와 서울 범위 검토값을 추가한 CSV | 수동 후보 검토 |
| `bizinfo_exact_title_crosswalk.csv` | 1,284행 | 중소벤처24와 기업마당 2026년 전체의 정확 제목 일치표 | 필드별 교차확인 |
| `bizinfo_candidate_exact_title_crosswalk.csv` | 197행 | 기업마당 소상공인 후보에 해당하는 정확 제목 일치행 | 우선 교차검토 |
| `bizinfo_candidates_without_exact_sme24_match.csv` | 66행 | 기업마당 후보 중 정확 제목 일치가 없는 공고 | 수동 확인 대상 |
| `sme24_small_business_candidates_without_exact_bizinfo_match.csv` | 544행 | 중소벤처24 후보 중 기업마당 정확 제목 일치가 없는 공고 | 기업마당 누락 후보 검토 |
| `manifest.json` | 1개 | 수집범위, 필드 채움 수, 교차확인 건수, SHA-256 | 기계 판독 QA |
| `QA.md` | 1개 | 핵심 수집·교차확인 결과 | 빠른 품질 확인 |

CSV는 Excel에서 한글이 깨지지 않도록 UTF-8 BOM으로 저장했다. JSONL은 한 줄이 공고 1건이며 UTF-8이다.

## 5. 권장 사용 순서

1. 전체 중소벤처24 공고를 확인할 때는 `all_items.csv`를 사용한다.
2. 소상공인 관련 공고를 검토할 때는 `small_business_candidates.csv`를 사용한다.
3. 기업마당 후보가 중소벤처24에 존재하는지 확인할 때는 `bizinfo_candidate_exact_title_crosswalk.csv`를 먼저 본다.
4. 정확 제목 일치가 없는 66건은 `bizinfo_candidates_without_exact_sme24_match.csv`에서 확인한다.
5. 일치하지 않는다고 정책이 없다고 결론 내리지 않는다. 제목 변경, 접두어, 차수 표기, 기관별 재공고 가능성을 공식 원문에서 확인한다.
6. 정확 제목이 일치해도 기관·기간·첨부파일 값이 다르면 행별 값을 비교하고 공식 공고문을 최종 근거로 사용한다.

## 6. 소상공인 후보 분류 기준

### 6.1 사용한 명시 코드

| 원본 변수 | 코드 | 명세상 의미 |
| --- | --- | --- |
| `cmpScaleCd` | `CC30` | 소상공인 |
| `needCrtfnCd` | `EC05` | 소상공인 확인·인증 |
| `bizTypeCd` | `PC80` | 소상공인 사업유형 |
| `sportTypeCd` | `RT06` | 소상공인 지원유형 |
| `sportInsttCd` | `SP05` | 소상공인시장진흥공단 |

이번 응답에서 `cmpScaleCd`와 `needCrtfnCd`는 전부 비어 있다. 따라서 실제 코드 후보 97건은 주로 `bizTypeCd`, `sportTypeCd`, `sportInsttCd`에서 확인됐다.

### 6.2 후보 등급

| 후보 등급 | 이번 건수 | 기준 |
| --- | ---: | --- |
| `explicit_code` | 97건 | 위 명시 코드 중 하나 이상 일치 |
| `explicit_text` | 628건 | 코드 일치는 없지만 공고명·지원대상·지원유형·기관·본문 등에 `소상공인` 명시 |

모든 후보의 `eligibility_status`는 `교차확인용_공식원문재검증필요`이다.

### 6.3 서울 적용범위 검토값

| 값 | 이번 건수 | 의미 |
| --- | ---: | --- |
| `seoul_explicit` | 36건 | `areaCd=1100`, 서울특별시 명시 |
| `area_unspecified_review` | 334건 | 지역코드가 없어 전국사업인지 별도 확인 필요 |
| `other_region_or_review` | 355건 | 서울 외 지역코드가 있거나 추가 해석 필요 |
| `nationwide_possible` | 0건 | `areaCd=1000` 명시 후보는 이번 수집에 없음 |

지역 미기재를 전국 적용으로 자동 간주하지 않는다.

## 7. 원본 변수표

`비어 있지 않은 건수`는 고유 공고 7,673건 기준이다. `명세 유형`은 공식 API 안내의 유형이며 CSV에서는 모든 값이 문자열로 저장된다.

### 7.1 공고 식별·본문

| 변수명 | 명세 유형 | 한글 의미 | 비어 있지 않은 건수 | 사용 시 주의 |
| --- | --- | --- | ---: | --- |
| `pblancSeq` | NUMBER | 공고SEQ | 7,673 | 중소벤처24 내부 기본키, 중복 0건 |
| `creatDt` | String | 공고등록일 | 5,006 | 2,667건 미제공, 조회기간 기준이 아님 |
| `pblancDtlUrl` | VARCHAR(1,000) | 상세정보 URL | 7,619 | 54건 빈값 |
| `pblancNm` | VARCHAR(500) | 공고명 | 7,673 | 기업마당 제목 교차확인의 기준값 |
| `detailBsnsNm` | VARCHAR(500) | 세부사업명 | 513 | 대부분 빈값 |
| `policyCnts` | CLOB | 사업개요 | 7,666 | HTML 포함 가능 |
| `sportMg` | CLOB | 지원규모 | 1,372 | 비정형 본문, 금액 구조화 전 원문 확인 필요 |
| `sportCnts` | CLOB | 지원내용 | 2,107 | HTML 포함 가능 |
| `sportTrget` | CLOB | 지원대상 | 7,666 | 후보 탐색값이며 최종 자격근거가 아님 |
| `reqstRcept` | CLOB | 신청방법 | 7,503 | 실제 접수경로와 마감상태 재확인 필요 |

### 7.2 기관·문의·날짜·첨부파일

| 변수명 | 명세 유형 | 한글 의미 | 비어 있지 않은 건수 | 사용 시 주의 |
| --- | --- | --- | ---: | --- |
| `sportInsttNm` | VARCHAR(100) | 지원기관명 | 7,671 | 기업마당 소관·수행기관과 역할이 다를 수 있음 |
| `sportInsttCd` | VARCHAR(4) | 지원기관코드 | 7,672 | `SP05`는 소상공인시장진흥공단 |
| `refrnc` | CLOB | 문의처 | 7,668 | 자유 텍스트 |
| `refrncUrl` | VARCHAR(1,000) | 문의처 홈페이지 | 4 | 거의 미제공 |
| `refrncDept` | VARCHAR(200) | 문의처 부서 | 1,557 | 선택 제공 |
| `refrncTel` | VARCHAR(100) | 문의처 전화번호 | 24 | 대부분 미제공 |
| `updDt` | String | 수정일시 | 7,673 | 이번 날짜 조회의 실제 기준 필드 |
| `pblancBgnDt` | String | 신청시작일 | 6,767 | `yyyy-MM-dd`, 미제공 가능 |
| `pblancEndDt` | String | 신청마감일 | 6,699 | 예산소진형·연장공고는 공식 원문 확인 필요 |
| `pblancAttach` | VARCHAR(4,000) | 첨부파일 URL | 6,209 | 복수 URL은 `\|` 구분 가능 |
| `pblancAttachNm` | VARCHAR(4,000) | 첨부파일명 | 1,498 | URL 필드와 채움 범위가 다름 |
| `reqstLinkInfo` | VARCHAR(1,000) | 온라인 신청 URL | 4,489 | 링크 안내용이며 실제 신청을 자동 수행하지 않음 |
| `pblancFileUrl` | VARCHAR(200) | 공고문 URL | 4,916 | 일반 첨부와 별도 제공 |
| `pblancFileNm` | VARCHAR(200) | 공고문 파일명 | 4,916 | 공고문 URL과 함께 사용 |

### 7.3 사업·지원·생애주기·지역 분류

| 변수명 | 명세 유형 | 한글 의미 | 비어 있지 않은 건수 | 사용 시 주의 |
| --- | --- | --- | ---: | --- |
| `bizType` | VARCHAR(100) | 사업유형 | 7,007 | 코드명 텍스트 |
| `bizTypeCd` | VARCHAR(4) | 사업유형코드 | 7,672 | `PC80`은 소상공인 |
| `sportType` | VARCHAR(100) | 지원유형 | 5,947 | 코드명 텍스트 |
| `sportTypeCd` | VARCHAR(4) | 지원유형코드 | 7,672 | `RT06`은 소상공인 |
| `lifeCyclDvsn` | VARCHAR(100) | 생애주기구분 | 0 | 이번 수집에서는 사용 불가 |
| `lifeCyclDvsnCd` | VARCHAR(4) | 생애주기구분코드 | 0 | 이번 수집에서는 사용 불가 |
| `areaNm` | VARCHAR(100) | 지역명 | 3,481 | 빈값을 전국으로 자동 간주하지 않음 |
| `areaCd` | VARCHAR(10) | 지역코드 | 3,481 | `1100`은 서울특별시, 복수는 구분자 확인 필요 |
| `cntcInsttNm` | VARCHAR(100) | 연계기관명 | 646 | 선택 제공 |
| `cntcInsttCd` | VARCHAR(4) | 연계기관코드 | 7,672 | 명칭은 비어 있어도 코드가 존재할 수 있음 |
| `induty` | VARCHAR(100) | 업종 | 0 | 이번 수집에서는 사용 불가 |

### 7.4 매출·업력·근로자·기업규모·인증조건

| 변수명 | 명세 유형 | 한글 의미 | 비어 있지 않은 건수 | 사용 시 주의 |
| --- | --- | --- | ---: | --- |
| `salsAmt` | VARCHAR(100) | 매출액 구간명 | 0 | 이번 수집에서는 사용 불가 |
| `salsAmtCd` | VARCHAR(4) | 매출액 구간코드 | 0 | 이번 수집에서는 사용 불가 |
| `minSalsAmt` | NUMBER | 최소 매출액 | 0 | 공식 공고문에서 별도 구조화 필요 |
| `maxSalsAmt` | NUMBER | 최대 매출액 | 0 | 공식 공고문에서 별도 구조화 필요 |
| `ablbiz` | VARCHAR(100) | 업력 구간명 | 0 | 이번 수집에서는 사용 불가 |
| `ablbizCd` | VARCHAR(4) | 업력 구간코드 | 0 | 이번 수집에서는 사용 불가 |
| `minAblbiz` | NUMBER | 최소 업력 | 0 | 공식 공고문에서 별도 구조화 필요 |
| `maxAblbiz` | NUMBER | 최대 업력 | 0 | 공식 공고문에서 별도 구조화 필요 |
| `emplyCnt` | VARCHAR(100) | 종업원수 구간명 | 0 | 이번 수집에서는 사용 불가 |
| `emplyCntCd` | VARCHAR(4) | 종업원수 구간코드 | 0 | 이번 수집에서는 사용 불가 |
| `minEmplyCnt` | NUMBER | 최소 종업원수 | 0 | 공식 공고문에서 별도 구조화 필요 |
| `mixEmplyCnt` | NUMBER | 최대 종업원수 | 0 | 공식 명세의 변수명이며 `max`가 아닌 `mix` 철자 유지 |
| `cmpScale` | VARCHAR(100) | 기업규모 | 0 | 이번 수집에서는 사용 불가 |
| `cmpScaleCd` | VARCHAR(4) | 기업규모코드 | 0 | `CC30` 명세가 있으나 실제 값 없음 |
| `needCrtfn` | VARCHAR(100) | 필요인증 | 0 | 이번 수집에서는 사용 불가 |
| `needCrtfnCd` | VARCHAR(4) | 필요인증코드 | 0 | `EC05` 명세가 있으나 실제 값 없음 |

### 7.5 대표자·금리·지원금액·창업 여부

| 변수명 | 명세 유형 | 한글 의미 | 비어 있지 않은 건수 | 사용 시 주의 |
| --- | --- | --- | ---: | --- |
| `rpsntAge` | NUMBER | 대표자 연령 | 0 | 이번 수집에서는 사용 불가 |
| `minRpsntAge` | NUMBER | 최소 대표자 연령 | 0 | 공식 공고문에서 별도 구조화 필요 |
| `maxRpsntAge` | NUMBER | 최대 대표자 연령 | 0 | 공식 공고문에서 별도 구조화 필요 |
| `minInrst` | NUMBER | 최소 금리 | 0 | API 값만으로 금융조건 산출 불가 |
| `maxInrst` | NUMBER | 최대 금리 | 0 | API 값만으로 금융조건 산출 불가 |
| `minSportAmt` | NUMBER | 최소 지원금액 | 0 | API 값만으로 금융조건 산출 불가 |
| `maxSportAmt` | NUMBER | 최대 지원금액 | 0 | API 값만으로 금융조건 산출 불가 |
| `refntnYn` | CHAR(1) | 재창업 여부 | 0 | 이번 수집에서는 사용 불가 |
| `fntnYn` | CHAR(1) | 예비·창업 여부 | 0 | 이번 수집에서는 사용 불가 |
| `fmleRpsntYn` | CHAR(1) | 여성대표 여부 | 0 | 이번 수집에서는 사용 불가 |

## 8. 후보 파생변수표

다음 변수는 API 원본이 아니라 `small_business_candidates.*` 생성 과정에서 추가됐다.

| 변수명 | 설명 | 값·예시 |
| --- | --- | --- |
| `candidate_tier` | 후보 선정 방식 | `explicit_code`, `explicit_text` |
| `candidate_code_matches` | 일치한 필드와 공식 코드 | `bizTypeCd:PC80;sportTypeCd:RT06` 등 |
| `candidate_text_fields` | `소상공인` 문구가 확인된 원본 필드 | `pblancNm`, `sportTrget` 등 |
| `seoul_scope` | 지역코드로 만든 보수적 서울 적용 검토값 | `seoul_explicit`, `area_unspecified_review` 등 |
| `eligibility_status` | 자격 확정 여부 | 항상 `교차확인용_공식원문재검증필요` |

## 9. 기업마당 교차확인 변수표

교차확인은 제목을 NFKC 정규화하고 영문 대소문자·공백·문장부호를 제거한 뒤 **완전히 같은 제목만** 연결한다. 유사도·부분문자열·임베딩 매칭은 사용하지 않았다.

| 변수명 | 설명 |
| --- | --- |
| `title_match_method` | 사용한 매칭 방식, `nfkc_casefold_alnum_exact` |
| `normalized_title` | 비교에 사용한 정규화 제목 |
| `sme24_pblancSeq` | 중소벤처24 공고SEQ |
| `sme24_pblancNm` | 중소벤처24 공고명 원문 |
| `bizinfo_pblancId` | 기업마당 공고ID |
| `bizinfo_pblancNm` | 기업마당 공고명 원문 |
| `is_bizinfo_small_business_candidate` | 기업마당 257건 후보 포함 여부, `yes` 또는 `no` |
| `sme24_creatDt` | 중소벤처24 등록일 |
| `bizinfo_creatPnttm` | 기업마당 등록일시 |
| `created_date_match` | 등록일 일치 여부, `yes` 또는 `no_or_unknown` |
| `sme24_sportInsttNm` | 중소벤처24 지원기관명 |
| `bizinfo_jrsdInsttNm` | 기업마당 소관기관명 |
| `bizinfo_excInsttNm` | 기업마당 수행기관명 |
| `agency_match` | 기관명 정규화 비교값, `yes`, `no`, `unknown` |
| `sme24_application_start` | 중소벤처24 신청시작일 |
| `bizinfo_application_start` | 기업마당 신청기간에서 추출한 시작일 |
| `application_start_match` | 시작일 일치 여부 |
| `sme24_application_end` | 중소벤처24 신청마감일 |
| `bizinfo_application_end` | 기업마당 신청기간에서 추출한 종료일 |
| `application_end_match` | 종료일 일치 여부 |
| `sme24_status_derived_from_dates` | 조회 종료일 기준 날짜 파생상태 |
| `sme24_attachment_present` | 중소벤처24 첨부 또는 공고문 URL 존재 여부 |
| `bizinfo_attachment_present` | 기업마당 첨부파일명 존재 여부 |
| `sme24_detail_url` | 중소벤처24 상세 URL |
| `bizinfo_detail_url` | 기업마당 상세 URL |
| `crosscheck_status` | `exact_title_candidate_not_official_validation` |

`sme24_status_derived_from_dates`는 명시적인 API 접수상태가 아니다. 신청 시작·종료일과 2026-08-15를 비교한 편의값이므로 예산소진, 조기마감, 연장 또는 변경공고를 반영하지 못할 수 있다.

## 10. 품질과 해석 제한

- 8개 월별 원본의 응답코드는 모두 `0`이다.
- 월별 원본 합계, JSONL·CSV 행 수, 고유 공고SEQ가 모두 7,673건으로 일치한다.
- 공고SEQ 중복은 0건이다.
- 모든 `updDt`가 해당 요청 구간 안에 있다.
- 원본과 모든 파생파일의 SHA-256은 `manifest.json`에 기록돼 있다.
- 인증키는 이 데이터 폴더의 산출물에 저장하지 않았다.
- API 정보에 일일 호출 한도가 없어 현재 `미확인`으로 기록했다.
- 명세에 존재해도 실제 채움 건수가 0인 변수는 현재 분석·자격판정·금융계산에 사용하면 안 된다.
- 정확 제목 일치는 동일 정책의 후보 증거일 뿐이다. 기관, 공고번호, 날짜, 첨부 원문이 모두 확인되기 전에는 동일 정책으로 확정하지 않는다.
- 정확 일치가 없다는 사실은 누락을 확정하지 않는다. 제목 변경·차수·지역 접두어·재공고를 수동 검토해야 한다.
- 중소벤처24와 기업마당 모두 최종 정책 자격과 금융조건의 공식 원문을 대체하지 않는다.

## 11. 재수집

재수집 코드는 [`scripts/collect_sme24.py`](../../../../scripts/collect_sme24.py)이다.

```powershell
& 'C:\Program Files\Python313\python.exe' 'scripts\collect_sme24.py' `
  --api-info 'data\raw_re\policy\sme24\API정보.md' `
  --start-date 2026-01-01 `
  --end-date 2026-08-15 `
  --collection-date YYYY-MM-DD
```

수집기는 인증키를 [`API정보.md`](API정보.md)에서 실행 시점에만 읽는다. 월별 원본을 저장하며 중단 시 `--resume`으로 기존 구간을 검증·재사용할 수 있다. `--rebuild-derived`는 API를 다시 호출하지 않고 기존 월별 원본에서 CSV·JSONL·교차확인·Manifest·QA를 재생성한다.
