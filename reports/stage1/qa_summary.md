# Stage 1 원본 데이터 감사 요약

- 감사 시각: 2026-08-14T20:50+09:00
- 원본 ZIP: 11개
- 원본 ZIP 총크기: 84,772,697 bytes
- 필수 데이터셋: 추정매출-상권, 점포-상권, 영역-상권
- 제공기간: 추정매출·점포 2021~2025년, 영역 현재 공간 Snapshot
- 보존: ZIP은 `data/raw/`, 해제본은 `data/raw/extracted/`로 분리
- 상세 목록: `data_inventory.csv`, `archive_contents.csv`

## 문자 디코딩 주의

감사한 CSV에서 디코딩 대체 문자가 발견되지 않았습니다.

## 좌표계

영역-상권 PRJ의 좌표계 이름은 `Korea_2000_Korea_Central_Belt`입니다. EPSG 코드는 Stage 2 공간 QA에서 라이브러리 판독으로 재확인합니다.
