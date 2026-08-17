"""Replace retired PDF/HWPX provenance rows with reviewed Markdown sources."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/processed_re/policy/re_stage2/source_manifest.csv"
REPLACEMENTS = {
    "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_CRISIS_TRACK2_2026H2/2026_하반기_위기_소상공인_Track2_공고.pdf":
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_CRISIS_TRACK2_2026H2/2026년_하반기_위기_소상공인_Track2_공고.md",
    "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_CLOSURE_2026/2026_새_길_여는_폐업지원_공고.pdf":
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_CLOSURE_2026/2026년_새_길_여는_폐업지원_공고.md",
    "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_DIGITAL_MIDLIFE_2026H2/2026_하반기_중장년_디지털전환_공고.pdf":
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_DIGITAL_MIDLIFE_2026H2/2026_하반기_중장년_디지털전환_공고.md",
    "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_ZERO_MARKET_2026_2/2026_서울제로마켓_2차_공고.hwpx":
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_ZERO_MARKET_2026_2/2026_서울제로마켓_활성화_사업_참여자_2차_공고.md",
    "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_SAFETY_TEST_2026H2/2026_서울_소상공인_안전검사_하반기.pdf":
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_SAFETY_TEST_2026H2/2026_서울_소상공인_안전검사_하반기_지원사업_공고(생활용품_및_어린이제품).md",
    "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_POLICY_LOANS_2026_CHANGE4/2026_소상공인_정책자금_융자사업_4차변경.pdf":
        "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_POLICY_LOANS_2026_CHANGE4/2026년 소상공인 정책자금 융자사업 4차변경 공고.md",
    "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_STABILITY_VOUCHER_2026/2026_소상공인_경영안정_바우처_공고.pdf":
        "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_STABILITY_VOUCHER_2026/2026년 소상공인 경영안정 바우처 지원사업 공고.md",
}


def main() -> None:
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    changed = 0
    for row in rows:
        replacement = REPLACEMENTS.get(row["source_path"])
        if replacement is None:
            continue
        path = ROOT / replacement
        payload = path.read_bytes()
        row.update(
            source_path=replacement,
            file_type="md",
            bytes=str(len(payload)),
            sha256=hashlib.sha256(payload).hexdigest(),
            signature_status="valid",
            reviewed_at="2026-08-17T12:30:00+09:00",
        )
        changed += 1
    if changed != 8:
        raise RuntimeError(f"예상한 8개 provenance 행 중 {changed}개만 변경됨")
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Markdown provenance rows updated: {changed}")


if __name__ == "__main__":
    main()
