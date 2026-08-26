# 버팀AI V4

V3 서비스 구조와 UI를 독립 `v4/`로 복사한 뒤 V4 복사본만 확장한 정책금융 행동 트윈이다. V2 `app/`, 공용 `src/`, V3 `v3/`는 수정하지 않는다.

## 범위

- 5단계: 사업장·걱정 → 재무 입력 → 현금 진단 → 정책 비교·선택 → 신청 준비
- 기존 거래내역·대출 CSV 현금진단 보존
- 걱정 버튼 최대 2개, 질문·설명 우선순위에만 사용
- 재무값 문장 붙여넣기·구조화 입력은 사용자 화면 검토 후 V4 범위에서 제거
- 정책별 한 행동, 준비 진행률, 검수된 발표 문서 샘플, 로컬 문의문 초안
- `sessionStorage`만 사용하며 탭 종료 시 삭제
- 기존 Rule·Event·현금·자격·순위 엔진 계약 보존

임의 신청서류 업로드·OCR, 장기 저장, 자동 알림, 기관 전송, 자동 신청은 포함하지 않는다.

## 실행

```powershell
$p = Start-Process -FilePath 'C:\Program Files\Python313\python.exe' -ArgumentList '-m','uvicorn','v4.main:app','--host','127.0.0.1','--port','8002' -WorkingDirectory 'D:\대회\2026 금융 AI Challenge' -WindowStyle Hidden -PassThru
```

## 테스트

```powershell
$p = Start-Process -FilePath 'C:\Program Files\Python313\python.exe' -ArgumentList '-m','pytest','v4\tests\test_v4.py','-q' -WorkingDirectory 'D:\대회\2026 금융 AI Challenge' -Wait -PassThru -NoNewWindow
exit $p.ExitCode
```

V3 복사 기준은 `V3_COPY_BASELINE_SHA256.md`에 기록돼 있다.
