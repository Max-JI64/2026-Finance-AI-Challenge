# RE Stage 3 입력 오류·경고 코드

| 코드 | 구분 | 의미 | 수정 위치 |
| --- | --- | --- | --- |
| `INVALID_INPUT` | 오류 | 스키마, 날짜, 허용값 또는 교차필드 조건 위반 | 반환된 `field` |
| `MISSING_REQUIRED_VALUE` | 오류 | CSV 필수 값 누락 | 반환된 CSV 행·열 |
| `INVALID_WON_AMOUNT` | 오류 | 원 단위 정수가 아닌 CSV 금액 | 반환된 CSV 행·열 |
| `INVALID_PERCENTAGE` | 오류 | 숫자가 아닌 연이율 백분율 | 반환된 CSV 행·열 |
| `CSV_HEADER_MISMATCH` | 오류 | 상세 CSV 헤더 또는 순서 불일치 | 해당 파일 |
| `CSV_ENCODING_ERROR` | 오류 | UTF-8/UTF-8-SIG가 아닌 CSV | 해당 파일 |
| `INVALID_MATURITY_DATE` | 오류 | 대출 만기가 기준일보다 앞섬 | `loans.<id>.maturity_date` |
| `INVALID_GRACE_PERIOD` | 오류 | 거치개월이 남은 납부회수 이상 | `loans.<id>.grace_months` |
| `POSSIBLE_TEN_THOUSAND_WON_UNIT` | 경고 | 0원보다 크고 1만원보다 작은 금액 발견 | 반환된 `field` |
| `UNUSUALLY_HIGH_VARIABLE_COST_RATE` | 경고 | 변동비율 80% 초과 | `variable_cost_rate_percent` |
| `UNUSUALLY_HIGH_INTEREST_RATE` | 경고 | 연이율 50% 초과 | 해당 대출 연이율 |

Pydantic 스키마 오류는 계산 전에 발생한다. API 통합 시 이 오류의 첫 `loc`을 `field`로 변환하고 원금액 자체는 오류 로그에 기록하지 않는다.
