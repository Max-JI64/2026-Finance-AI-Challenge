# RE Stage 4 오류 코드

| 코드 | 의미 |
| --- | --- |
| `POLICY_TERMS_UNCONFIRMED` | 핵심 공식 조건이 미확인이라 계산 차단 |
| `POLICY_SUBPRODUCT_REQUIRED` | 세부사업 선택 전 대표 계산 금지 |
| `WRONG_CONVERTER` | 지원유형과 다른 변환기 사용 |
| `POLICY_AMOUNT_EXCEEDS_OFFICIAL_CAP` | 조건부 금액이 공식 한도 초과 |
| `POLICY_EVENT_OUTSIDE_EFFECTIVE_PERIOD` | 사업 수행·대출 실행일이 정책 적용기간 밖 |
| `REIMBURSEMENT_INPUT_REQUIRED` | 사후정산 총사업비·적격비용·선지출일 누락 |
| `INVALID_ELIGIBLE_EXPENSE` | 적격비용이 총사업비 초과 |
| `INVALID_VAT_AND_ELIGIBLE_EXPENSE` | 적격비용과 부가세가 총사업비 초과 |
| `SUPPORT_EXCEEDS_ELIGIBLE_EXPENSE` | 지원액이 적격비용 초과 |
| `INVALID_VOUCHER_PERIOD` | 바우처 활성일·소진기한 역전 |
| `VOUCHER_EXPIRY_EXCEEDS_OFFICIAL_DATE` | 공식 소진기한 초과 |
| `BANK_RATE_REQUIRED` | 은행 심사금리 입력 필요 |
| `REFERENCE_RATE_REQUIRED` | 정책자금 기준금리 입력 필요 |
| `POLICY_INTEREST_RATE_UNCONFIRMED` | 계산 가능한 공식 금리 규칙 없음 |
| `LOAN_TERMS_NOT_IN_OFFICIAL_OPTIONS` | 기간·거치·상환방식이 공식 옵션과 불일치 |
| `POLICY_OPTION_CONFIRMATION_REQUIRED` | 세부 상환옵션의 공식 확인 필요 |
| `REFINANCE_RATE_MISMATCH` | 대환 후 금리가 공식 고정금리와 불일치 |
| `DUPLICATE_LINKED_POLICY_EVENT` | 같은 연결 금융효과를 중복 적용 |
| `DUPLICATE_POLICY_EVENT` | 동일 이벤트 중복 |
| `INVALID_LINKED_POLICY_EVENT` | 공식 연결관계가 아닌 대출 결합 |
| `GUARANTEE_FEE_SUPPORT_EXCEEDS_CAP` | 보증료 지원액이 공식 한도 초과 |
| `GUARANTEE_FEE_SUPPORT_EXCEEDS_FEE` | 보증료 지원액이 실제 보증료 초과 |
| `REFINANCED_LOAN_NOT_IN_BASELINE` | 대환 대상 대출이 RE3 기준선에 없음 |
| `REFINANCE_BASELINE_ALIGNMENT_REQUIRED` | 실행일 기준 잔액과 RE3 기준선 불일치 가능성 |

오류에는 수정할 `field`를 함께 반환한다. 원금액과 개인 금융정보는 로그로 남기지 않는다.
