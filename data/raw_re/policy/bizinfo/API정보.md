중앙부처, 지자체, 유관기관의 최신 지원사업 공고 정보 제공


서비스 정보
데이터포맷
JSON+XML
End Point
https://apis.data.go.kr/1421000/bizinfo
일반 인증키
gR9efoM90FwF0PklBCvwsoDUOCQy8FMzFbsJLI8ARdJHTCPCD32vV40mNCVXUDtO0CjcDfd8rgHQZcMSxhOcmg%3D%3D

API 목록


GET
/pblancBsnsService
중소기업 지원사업 공고 조회 서비스
중앙부처, 지자체, 유관기관의 최신 지원사업 공고 정보 제공

Parameters
OpenAPI 실행 준비
Name	Description
serviceKey *
string
(query)
공공데이터포털에서 받은 인증키

serviceKey
dataType
string
(query)
응답데이터 형식

dataType
pageNo
string
(query)
페이지번호

pageNo
numOfRows
string
(query)
한 페이지 결과 수

numOfRows
searchLclasId
string
(query)
분야를 조회하는 설정값

searchLclasId
hashtags
string
(query)
해시태그를 지정하여 조회하는 설정값

hashtags
pblancId
string
(query)
공고 조회를 위한 고유 식별값 설정값

pblancId
registDe
string
(query)
공고를 등록한 일자

registDe
updtPnttm
string
(query)
공고를 수정한 일자

updtPnttm
Responses
Response content type

application/json
Code	Description
200	
성공

Example Value
Model
{
  "header": {
    "resultCode": "string",
    "resultMsg": "string"
  },
  "body": {
    "items": {
      "item": {
        "pblancNm": "string",
        "pblancUrl": "string",
        "pblancId": "string",
        "jrsdInsttNm": "string",
        "excInsttNm": "string",
        "bsnsSumryCn": "string",
        "pldirSportRealmLclasCodeNm": "string",
        "creatPnttm": "string",
        "reqstBeginEndDe": "string",
        "updtPnttm": "string",
        "trgetNm": "string",
        "inqireCo": "string",
        "flpthNm": "string",
        "fileNm": "string",
        "printFlpthNm": "string",
        "printFileNm": "string",
        "hashtags": "string",
        "reqstMthPapersCn": "string",
        "refrncNm": "string",
        "rceptEngnHmpgUrl": "string"
      }
    },
    "numOfRows": "string",
    "pageNo": "string",
    "totalCount": "string"
  }
}

Models

pblancBsnsService_response{
header	{
description:	
header

resultCode	string
결과코드

resultMsg	string
결과메세지

}
body	{
description:	
body

items	{
description:	
items

item	{
description:	
item

pblancNm	string
공고명

pblancUrl	string
기업마당URL

pblancId	string
공고ID

jrsdInsttNm	string
소관기관명

excInsttNm	string
수행기관명

bsnsSumryCn	string
사업개요내용

pldirSportRealmLclasCodeNm	string
정책디렉토리지원분야대분류명

creatPnttm	string
등록일시

reqstBeginEndDe	string
신청기간

updtPnttm	string
수정일시

trgetNm	string
지원대상

inqireCo	string
조회수

flpthNm	string
파일경로명

fileNm	string
파일명

printFlpthNm	string
본문출력파일경로명

printFileNm	string
본문출력파일명

hashtags	string
해시태그

reqstMthPapersCn	string
사업신청방법내용

refrncNm	string
문의처

rceptEngnHmpgUrl	string
사업신청URL

}
}
numOfRows	string
한페이지 결과수

pageNo	string
페이지번호

totalCount	string
총건수

}
}