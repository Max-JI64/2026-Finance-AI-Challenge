# RE Stage 3 상세 CSV 입력 템플릿

두 CSV는 UTF-8-SIG와 원 단위 정수를 사용한다. 기준일, 기초현금, 안전현금 기준은 CSV와 별도로 입력한다.

## `cashflow_events.csv`

- `event_type`: `historical_revenue`, `operating_inflow`, `accounts_receivable`, `fixed_cost`, `variable_cost`, `tax_utility`, `accounts_payable`, `one_time_expense`
- `historical_revenue`는 최근 6~12개월 맥락 보존용이며 미래 현금잔액에 더하지 않는다.
- 미래 현금흐름에 반영할 매출과 비용은 실제 예정일별로 한 행씩 입력한다. 엔진은 누락된 날짜나 반복일정을 만들지 않는다.
- 비용 행에는 `expense_type`이 필수다. 허용값은 `rent`, `labor`, `purchase`, `tax`, `utility`, `social_insurance`, `vehicle_fuel`, `equipment`, `repair`, `other`다.
- 동일 날짜·유형·금액·비용유형·설명의 비용 행이 반복되면 중복 가능성 오류로 처리한다.

## `loans.csv`

- `repayment_method`: `equal_principal`, `equal_payment`, `bullet`
- 금리는 연이율 백분율이다. 예를 들어 4.5%는 `4.5`로 입력한다.
- 이자는 일할계산하지 않고 매 납부일의 기초원금에 `연이율 / 12`를 적용한다.
- `grace_months`는 원금균등·원리금균등에서만 사용한다. 만기일시상환은 `0`을 입력한다.
- 납부일이 그 달의 마지막 날보다 크면 그 달 마지막 날을 사용한다. 만기일이 정규 납부일과 다르면 만기일을 마지막 이벤트로 사용한다.

주민등록번호, 계좌번호, 신용점수, 필수 사업자등록번호 필드는 없다.
