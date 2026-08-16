API안내

인증키 : B4ZR8wJKiUNdQorhO/GlwaoUyE3c2oHe2GjGuf8yQ8VV76czOZW/Mdvj+2NEvxiGyajUbk/5hfD7dRoE2umF/w==


공고정보
공고정보 API
요청 URL
https://portal.smes.go.kr/ione-gw/api/pblanc/list
설명
중소벤처24 홈페이지에 공개된 사업공고 정보를 연계하기 위한 API
메서드
GET
응답형식
JSON
요청 파라미터
※ token(인증키)은 기정원에 요청하여 발급 받아야 합니다.
※ GET 방식으로 호출 시 token 값은 URL encoding하여 전달해야 합니다.

요청 파라미터. 파라미터명, 타입, 한글명, 필수여부, 설명 정보가 제공됨.
파라미터명	타입	한글명	필수여부	설명
token	String	인증키	필수	GET 방식으로 호출시 url encoding 필요
strDt	String	검색시작일	선택	yyyyMMdd 형식의 날짜 문자열
endDt	String	검색종료일	선택	yyyyMMdd 형식의 날짜 문자열
html	String	html 여부	선택	yes : 컨텐츠 항목에 html 태그 포함(기본값) / no : html 태그 제외한 Text 출력
호출 URL 예시
https://portal.smes.go.kr/ione-gw/api/pblanc/list?token={인증키}&strDt=20260101&endDt=20260110
결과상태 코드
결과상태 코드. 코드, 메시지, 비고 정보가 제공됨.
코드	메시지	비고
0	정상적으로 조회 되었습니다.	정상
9	인증키 오류. 허용되지 않은 인증키입니다.	오류
10	인증키 오류. 해당 API의 인증키가 아닙니다.	오류
11	시작일자 길이 오류	오류
12	종료일자 길이 오류	오류
13	검색 기간 오류	오류
14	허용되지 않은 IP 접근입니다.	오류
99	기타 오류 발생	오류
응답메시지
응답메시지. 필드명, 타입, 한글명, 필수여부, 설명 정보가 제공됨.
필드명	타입	한글명	필수	설명
resultCd	String	결과상태코드	Y	결과상태 코드 참조
data	Array	공고 데이터	Y	-
pblancSeq	NUMBER	공고SEQ	-	숫자
creatDt	String	공고등록일	-	yyyy-MM-dd HH:mm:ss 형식의 문자열
pblancDtlUrl	VARCHAR(1,000)	상세정보경로	-	URL 텍스트
pblancNm	VARCHAR(500)	공고명	-	텍스트
detailBsnsNm	VARCHAR(500)	세부사업명	-	텍스트
policyCnts	CLOB	사업개요	-	텍스트(HTML태그포함)
sportMg	CLOB	지원규모	-	텍스트(HTML태그포함)
sportCnts	CLOB	지원내용	-	텍스트(HTML태그포함)
sportTrget	CLOB	지원대상	-	텍스트(HTML태그포함)
reqstRcept	CLOB	신청방법	-	텍스트(HTML태그포함)
sportInsttNm	VARCHAR(100)	지원기관명	-	코드표 참조
sportInsttCd	VARCHAR(4)	지원기관코드	-	코드표 참조
refrnc	CLOB	문의처	-	텍스트(HTML태그포함)
refrncUrl	VARCHAR(1,000)	문의처 홈페이지	-	URL 텍스트
refrncDept	VARCHAR(200)	문의처 부서	-	텍스트
refrncTel	VARCHAR(100)	문의처 전화번호	-	텍스트
updDt	String	수정일시	-	yyyy-MM-dd HH:mm:ss 형식의 문자열
pblancBgnDt	String	신청시작일	-	yyyy-MM-dd 형식의 문자열
pblancEndDt	String	신청마감일	-	yyyy-MM-dd 형식의 문자열
pblancAttach	VARCHAR(4,000)	첨부파일URL	-	복수인 경우 '|' 기호로 구분하여 제공
pblancAttachNm	VARCHAR(4,000)	첨부파일명	-	복수인 경우 '|' 기호로 구분하여 제공
reqstLinkInfo	VARCHAR(1,000)	온라인 신청 URL	-	URL 텍스트
bizType	VARCHAR(100)	사업유형	-	텍스트
bizTypeCd	VARCHAR(4)	사업유형코드	-	코드표 참조
sportType	VARCHAR(100)	지원유형	-	코드표 참조
sportTypeCd	VARCHAR(4)	지원유형코드	-	코드표 참조
lifeCyclDvsn	VARCHAR(100)	생애주기구분	-	코드표 참조, 복수는 '|' 구분
lifeCyclDvsnCd	VARCHAR(4)	생애주기구분코드	-	코드표 참조, 복수는 '|' 구분
areaNm	VARCHAR(100)	지역명	-	코드표 참조, 복수는 '|' 구분
areaCd	VARCHAR(10)	지역코드	-	코드표 참조, 복수는 '|' 구분
salsAmt	VARCHAR(100)	매출액	-	코드표 참조, 복수는 '|' 구분
salsAmtCd	VARCHAR(4)	매출액코드	-	코드표 참조, 복수는 '|' 구분
minSalsAmt	NUMBER	최소 매출액	-	제한 없는 경우 빈값
maxSalsAmt	NUMBER	최대 매출액	-	제한 없는 경우 빈값
ablbiz	VARCHAR(100)	업력	-	코드표 참조, 복수는 '|' 구분
ablbizCd	VARCHAR(4)	업력코드	-	코드표 참조, 복수는 '|' 구분
minAblbiz	NUMBER	최소 업력	-	제한 없는 경우 빈값
maxAblbiz	NUMBER	최대 업력	-	제한 없는 경우 빈값
emplyCnt	VARCHAR(100)	종업원수	-	코드표 참조, 복수는 '|' 구분
emplyCntCd	VARCHAR(4)	종업원수코드	-	코드표 참조, 복수는 '|' 구분
minEmplyCnt	NUMBER	최소 종업원수	-	제한 없는 경우 빈값
mixEmplyCnt	NUMBER	최대 종업원수	-	제한 없는 경우 빈값
cmpScale	VARCHAR(100)	기업규모	-	코드표 참조, 복수는 '|' 구분
cmpScaleCd	VARCHAR(4)	기업규모코드	-	코드표 참조, 복수는 '|' 구분
needCrtfn	VARCHAR(100)	필요인증	-	코드표 참조, 복수는 '|' 구분
needCrtfnCd	VARCHAR(4)	필요인증코드	-	코드표 참조, 복수는 '|' 구분
cntcInsttNm	VARCHAR(100)	연계기관명	-	코드표 참조
cntcInsttCd	VARCHAR(4)	연계기관코드	-	코드표 참조
induty	VARCHAR(100)	업종	-	코드 OR 텍스트
rpsntAge	NUMBER	대표자 연령	-	코드 OR 텍스트
minRpsntAge	NUMBER	최소 대표자 연령	-	제한 없는 경우 빈값
maxRpsntAge	NUMBER	최대 대표자 연령	-	제한 없는 경우 빈값
minInrst	NUMBER	최소 금리	-	제한 없는 경우 빈값
maxInrst	NUMBER	최대 금리	-	제한 없는 경우 빈값
minSportAmt	NUMBER	최소 지원금액	-	제한 없는 경우 빈값
maxSportAmt	NUMBER	최대 지원금액	-	제한 없는 경우 빈값
refntnYn	CHAR(1)	재창업여부	-	Y 또는 N
fntnYn	CHAR(1)	(예비)창업여부	-	Y 또는 N
fmleRpsntYn	CHAR(1)	여성대표여부	-	Y 또는 N
pblancFileUrl	VARCHAR(200)	공고문 URL	-	공고문 첨부파일 URL
pblancFileNm	VARCHAR(200)	공고문 파일명	-	공고문 첨부파일 명
resultMsg	String	결과 메시지	Y	처리 결과 메시지 출력
결과 데이터 예시
{
  "resultCd": "0",
  "data": [
    {
      "pblancSeq": ,
      "creatDt": "",
      "pblancDtlUrl": ""
      // ... (응답메시지 필드 참고)
    },
    {
      "pblancSeq": ,
      "creatDt": "",
      "pblancDtlUrl": ""
    }
  ],
  "resultMsg": "정상적으로 조회되었습니다."
}
코드 참조표
기업분류기준코드
코드구분	코드	코드명
기업분류기준코드	CC10	중소기업
CC30	소상공인
CC50	1인기업
CC60	창업기업
CC70	예비창업자
CC80	기타기업
인증/확인유형코드
코드구분	코드	코드명
인증/확인유형코드	EC01	수출유망중소기업
EC02	여성기업
EC03	장애인기업
EC04	중소기업
EC05	소상공인
EC06	기술혁신형중소기업
EC07	경영혁신형중소기업
EC08	벤처기업
EC09	우수그린비즈
EC10	사회적기업
EC11	연구소보유
EC12	지식재산경영인증 기업
EC13	부품소재기업
EC14	뿌리기술기업
EC15	에너지기술기업
EC16	기술전문기업
EC17	직접생산확인기업
근로자수구간코드
코드구분	코드	코드명
근로자수구간코드	EI01	1~5명미만
EI02	5~10명미만
EI03	10~20명미만
EI04	20~50명미만
EI05	50~100명미만
EI06	100명이상
생애주기구분코드
코드구분	코드	코드명
생애주기구분코드	LC01	창업
LC02	성장
LC03	폐업·재기
업력구간코드
코드구분	코드	코드명
업력구간코드	OI01	3년미만
OI02	3년이상~5년미만
OI03	5년이상~7년미만
OI04	7년이상~10년미만
OI05	10년이상~20년미만
OI06	20년이상
사업유형코드
코드구분	코드	코드명
사업유형코드	PC10	금융
PC20	기술
PC30	인력
PC40	수출
PC50	내수
PC60	창업
PC70	경영
PC80	소상공인
PC90	지원
PC11	벤처
지원유형코드
코드구분	코드	코드명
지원유형코드	RT01	창업
RT02	기술개발
RT03	정책자금
RT04	기술보증
RT05	스마트공장
RT06	소상공인
RT07	인력지원
RT08	수출지원
RT09	기업지원
RT10	정보
매출액구간코드
코드구분	코드	코드명
매출액구간코드	SI01	5억미만
SI02	5억이상~10억미만
SI03	10억이상~20억미만
SI04	20억이상~50억미만
SI05	50억이상~100억미만
SI06	100억이상~300억미만
SI07	300억이상
지원기관코드
코드구분	코드	코드명
지원기관코드	SP01	중소벤처기업진흥공단
SP02	중소기업기술정보진흥원
SP03	중소기업유통센터
SP04	창업진흥원
SP05	소상공인시장진흥공단
SP06	기술보증기금
SP10	대·중소기업·농어업협력재단
SP12	여성기업종합지원센터
SP13	(재)장애인기업종합지원센터
SP14	한국산업기술진흥원
SP15	지역신용보증재단
SP16	중소벤처기업부
SP17	중소기업중앙회
SP18	중소기업융합중앙회
SP19	한국창업보육협회
SP20	이노비즈협회
SP21	한국경영혁신중소기업협회
SP22	대한무역투자진흥공사
SP99	기타
지역코드
코드구분	코드	코드명
지역코드	1000	전국
1100	서울특별시
2600	부산광역시
2700	대구광역시
2800	인천광역시
2900	광주광역시
3000	대전광역시
3100	울산광역시
3611	세종특별자치시
4100	경기도
4200	강원도
4300	충청북도
4400	충청남도
4500	전라북도
4600	전라남도
4700	경상북도
4800	경상남도
5000	제주특별자치도
연계기관코드
코드구분	코드	코드명
연계기관코드	BI01	SMTECH
BI02	K-STARTUP
BI03	스마트공장
BI04	소상공인 마당
BI05	중소기업 벤처진흥공단(정책자금)
BI06	기술보증기금
BI07	판판대로
BI08	기술보호울타리
BI09	중소기업인력지원사업종합관리시스템
BI10	중소기업해외전시포탈
BI11	협업정보시스템
BI12	중소기업수출지원센터
BI13	IRIS
BI14	소셜벤처스퀘어
BI15	무역24
BI90	중소기업 벤처진흥공단(기타)
JavaScript(Ajax) 호출 예시
$.ajax({
  url: 'https://portal.smes.go.kr/ione-gw/api/pblanc/list',
  data: {
    'token': '{인증키}',
    'strDt': '20260101',
    'endDt': '20260110'
  },
  dataType: 'json',
  type: 'GET',
  success: function(data) {
    console.dir(data);
  }
});
Java(HttpURLConnection) 호출 예시
String apiUrl = "https://portal.smes.go.kr/ione-gw/api/pblanc/list?token={URL_ENCODED_인증키}";
URL url = new URL(apiUrl);
HttpURLConnection con = (HttpURLConnection) url.openConnection();
con.setRequestMethod("GET");
con.setRequestProperty("Content-Type", "application/json");
int responseCode = con.getResponseCode();

BufferedReader br;
if (responseCode == 200) {
  br = new BufferedReader(new InputStreamReader(con.getInputStream()));
} else {
  br = new BufferedReader(new InputStreamReader(con.getErrorStream()));
}

String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = br.readLine()) != null) {
  response.append(inputLine);
}
br.close();

Gson gson = new GsonBuilder().setPrettyPrinting().create();
JsonParser jsonParser = new JsonParser();
JsonElement jsonElement = jsonParser.parse(response.toString());
System.out.println(gson.toJson(jsonElement));