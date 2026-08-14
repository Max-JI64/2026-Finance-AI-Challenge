"""Audit and safely extract the Stage 1 Seoul commercial-area archives."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import struct
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO
from zipfile import ZipFile, ZipInfo


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"
EXTRACTED_ROOT = RAW_ROOT / "extracted"
REPORT_ROOT = PROJECT_ROOT / "reports" / "stage1"

SOURCE_INFO = {
    "추정매출-상권": {
        "organization": "서울신용보증재단 (서울 열린데이터광장)",
        "url": "https://data.seoul.go.kr/dataList/OA-15572/S/1/datasetView.do",
    },
    "점포-상권": {
        "organization": "서울신용보증재단 (서울 열린데이터광장)",
        "url": "https://data.seoul.go.kr/dataList/OA-15577/S/1/datasetView.do",
    },
    "영역-상권": {
        "organization": "서울신용보증재단 (서울 열린데이터광장)",
        "url": "https://data.seoul.go.kr/dataList/OA-15560/S/1/datasetView.do",
    },
}


@dataclass
class InventoryRow:
    dataset_priority: str
    dataset_name: str
    source_organization: str
    official_url: str
    downloaded_at: str
    reference_period: str
    original_filename: str
    extracted_path: str
    file_size_bytes: int
    file_format: str
    encoding: str
    delimiter: str
    coordinate_reference_system: str
    row_count: int
    column_count: int
    sha256: str
    status: str
    notes: str


@dataclass
class ContentRow:
    archive_filename: str
    member_filename: str
    member_size_bytes: int
    extracted_path: str


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_name_from(path: Path) -> str:
    for dataset_name in SOURCE_INFO:
        if dataset_name in path.name:
            return dataset_name
    raise ValueError(f"Unknown Stage 1 archive: {path.name}")


def reference_period_from(path: Path) -> str:
    for year in range(2021, 2031):
        if f"{year}년" in path.name:
            return str(year)
    return "current_spatial_snapshot"


def repaired_member_name(info: ZipInfo) -> str:
    """Repair CP949 names stored without the ZIP UTF-8 filename flag."""

    if info.flag_bits & 0x800:
        return info.filename
    try:
        return info.filename.encode("cp437").decode("cp949")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return info.filename


def safe_destination(root: Path, member_name: str) -> Path:
    destination = (root / member_name).resolve()
    resolved_root = root.resolve()
    if destination != resolved_root and resolved_root not in destination.parents:
        raise ValueError(f"Unsafe ZIP member path: {member_name}")
    return destination


def extract_member(zipped: BinaryIO, destination: Path, expected_size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.stat().st_size != expected_size:
            destination.unlink()
        else:
            return
    with destination.open("wb") as output:
        shutil.copyfileobj(zipped, output)


def inspect_csv(archive: ZipFile, info: ZipInfo) -> tuple[str, int, int, int]:
    with archive.open(info) as raw:
        sample_bytes = raw.read(256 * 1024)

    candidates = ("utf-8-sig", "cp949", "euc-kr")
    encoding = min(
        candidates,
        key=lambda candidate: sample_bytes.decode(candidate, errors="replace").count(
            "\ufffd"
        ),
    )

    row_count = 0
    column_count = 0
    replacement_rows = 0
    with archive.open(info) as raw:
        import io

        text = io.TextIOWrapper(raw, encoding=encoding, errors="replace", newline="")
        reader = csv.reader(text)
        header = next(reader)
        column_count = len(header)
        if any("\ufffd" in value for value in header):
            replacement_rows += 1
        for row in reader:
            row_count += 1
            if any("\ufffd" in value for value in row):
                replacement_rows += 1

    return encoding, row_count, column_count, replacement_rows


def inspect_dbf(archive: ZipFile, info: ZipInfo) -> tuple[int, int]:
    with archive.open(info) as raw:
        header = raw.read(32)
    if len(header) != 32:
        raise ValueError(f"Invalid DBF header: {info.filename}")
    row_count = struct.unpack("<I", header[4:8])[0]
    header_length = struct.unpack("<H", header[8:10])[0]
    column_count = max(0, (header_length - 33) // 32)
    return row_count, column_count


def write_csv(path: Path, rows: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def audit_archives(extract: bool) -> tuple[list[InventoryRow], list[ContentRow]]:
    inventory: list[InventoryRow] = []
    contents: list[ContentRow] = []

    for archive_path in sorted(RAW_ROOT.glob("*.zip")):
        dataset_name = dataset_name_from(archive_path)
        source = SOURCE_INFO[dataset_name]
        extracted_dir = EXTRACTED_ROOT / archive_path.stem
        encoding = ""
        delimiter = ""
        coordinate_reference_system = ""
        row_count = 0
        column_count = 0
        replacement_rows = 0
        formats: set[str] = set()

        with ZipFile(archive_path) as archive:
            for info in archive.infolist():
                member_name = repaired_member_name(info)
                suffix = Path(member_name).suffix.lower().lstrip(".")
                if suffix:
                    formats.add(suffix.upper())
                destination = safe_destination(extracted_dir, member_name)

                contents.append(
                    ContentRow(
                        archive_filename=archive_path.name,
                        member_filename=member_name,
                        member_size_bytes=info.file_size,
                        extracted_path=destination.relative_to(PROJECT_ROOT).as_posix(),
                    )
                )

                if info.is_dir():
                    if extract:
                        destination.mkdir(parents=True, exist_ok=True)
                    continue

                if extract:
                    with archive.open(info) as zipped:
                        extract_member(zipped, destination, info.file_size)

                if suffix == "csv":
                    encoding, row_count, column_count, replacement_rows = inspect_csv(
                        archive, info
                    )
                    delimiter = ","
                elif suffix == "dbf":
                    row_count, column_count = inspect_dbf(archive, info)
                elif suffix == "cpg":
                    with archive.open(info) as raw:
                        encoding = raw.read().decode("ascii", errors="replace").strip()
                elif suffix == "prj":
                    with archive.open(info) as raw:
                        wkt = raw.read().decode("ascii", errors="replace")
                    coordinate_reference_system = wkt.split(",", 1)[0].removeprefix(
                        'PROJCS["'
                    ).rstrip('"')

        notes = "ZIP CRC and content stream read completed"
        if replacement_rows:
            notes += f"; rows with replacement characters={replacement_rows}"

        inventory.append(
            InventoryRow(
                dataset_priority="P0",
                dataset_name=dataset_name,
                source_organization=source["organization"],
                official_url=source["url"],
                downloaded_at=datetime.fromtimestamp(
                    archive_path.stat().st_mtime
                ).astimezone().isoformat(timespec="minutes"),
                reference_period=reference_period_from(archive_path),
                original_filename=archive_path.name,
                extracted_path=extracted_dir.relative_to(PROJECT_ROOT).as_posix(),
                file_size_bytes=archive_path.stat().st_size,
                file_format="ZIP (" + "/".join(sorted(formats)) + ")",
                encoding=encoding,
                delimiter=delimiter,
                coordinate_reference_system=coordinate_reference_system,
                row_count=row_count,
                column_count=column_count,
                sha256=sha256_file(archive_path),
                status="downloaded_and_audited",
                notes=notes,
            )
        )

    return inventory, contents


def write_summary(inventory: list[InventoryRow]) -> None:
    archives = len(inventory)
    total_bytes = sum(row.file_size_bytes for row in inventory)
    replacement_items = [
        row for row in inventory if "replacement characters=" in row.notes
    ]
    lines = [
        "# Stage 1 원본 데이터 감사 요약",
        "",
        f"- 감사 시각: {datetime.now().astimezone().isoformat(timespec='minutes')}",
        f"- 원본 ZIP: {archives}개",
        f"- 원본 ZIP 총크기: {total_bytes:,} bytes",
        "- 필수 데이터셋: 추정매출-상권, 점포-상권, 영역-상권",
        "- 제공기간: 추정매출·점포 2021~2025년, 영역 현재 공간 Snapshot",
        "- 보존: ZIP은 `data/raw/`, 해제본은 `data/raw/extracted/`로 분리",
        "- 상세 목록: `data_inventory.csv`, `archive_contents.csv`",
        "",
        "## 문자 디코딩 주의",
        "",
    ]
    if replacement_items:
        lines.append(
            "아래 파일은 CP949 디코딩 중 대체 문자가 발생했습니다. Stage 2에서 원문 바이트와 해당 행을 별도 확인해야 합니다."
        )
        lines.append("")
        lines.extend(f"- `{row.original_filename}`: {row.notes}" for row in replacement_items)
    else:
        lines.append("감사한 CSV에서 디코딩 대체 문자가 발견되지 않았습니다.")

    lines.extend(
        [
            "",
            "## 좌표계",
            "",
            "영역-상권 PRJ의 좌표계 이름은 `Korea_2000_Korea_Central_Belt`입니다. EPSG 코드는 Stage 2 공간 QA에서 라이브러리 판독으로 재확인합니다.",
            "",
        ]
    )
    (REPORT_ROOT / "qa_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Safely extract copies under data/raw/extracted/.",
    )
    args = parser.parse_args()

    inventory, contents = audit_archives(extract=args.extract)
    write_csv(REPORT_ROOT / "data_inventory.csv", inventory)
    write_csv(REPORT_ROOT / "archive_contents.csv", contents)
    write_summary(inventory)
    print(f"audited_archives={len(inventory)}")
    print(f"inventory={REPORT_ROOT / 'data_inventory.csv'}")


if __name__ == "__main__":
    main()
