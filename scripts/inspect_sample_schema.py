"""Inspect raw-data schemas without loading complete datasets.

The script reads at most 64 KiB for encoding detection and at most five data
rows per CSV. For the shapefile attributes, it reads the DBF header and at most
five fixed-width records.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import struct
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"
MAX_ENCODING_BYTES = 64 * 1024
MAX_SAMPLE_ROWS = 5

PRIMARY_DATASETS = (
    "추정매출-상권",
    "점포-상권",
    "영역-상권",
    "길단위인구-상권",
    "상권변화지표-상권",
    "상주인구-상권",
    "직장인구-상권",
    "집객시설-상권",
    "아파트-상권",
)


def detect_encoding(path: Path) -> str:
    sample = path.read_bytes()[:MAX_ENCODING_BYTES]
    candidates = ("utf-8-sig", "cp949", "euc-kr")
    return min(
        candidates,
        key=lambda encoding: sample.decode(encoding, errors="replace").count("\ufffd"),
    )


def infer_type(values: list[str]) -> str:
    nonempty = [value.strip() for value in values if value.strip()]
    if not nonempty:
        return "empty_in_sample"

    try:
        for value in nonempty:
            int(value)
        return "integer"
    except ValueError:
        pass

    try:
        for value in nonempty:
            float(value)
        return "number"
    except ValueError:
        return "text"


def inspect_csv(path: Path) -> dict[str, Any]:
    encoding = detect_encoding(path)
    with path.open("r", encoding=encoding, errors="replace", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        rows = []
        for _ in range(MAX_SAMPLE_ROWS):
            try:
                rows.append(next(reader))
            except StopIteration:
                break

    columns = []
    for index, name in enumerate(header):
        values = [row[index] for row in rows if index < len(row)]
        example = next((value for value in values if value != ""), "")
        columns.append(
            {
                "name": name,
                "inferred_type": infer_type(values),
                "example": example,
            }
        )

    return {
        "path": path.relative_to(PROJECT_ROOT).as_posix(),
        "size_bytes": path.stat().st_size,
        "encoding": encoding,
        "sample_rows": len(rows),
        "column_count": len(header),
        "header": header,
        "columns": columns,
    }


def read_dbf_fields(path: Path) -> tuple[int, list[dict[str, Any]], list[list[str]]]:
    cpg_path = path.with_suffix(".cpg")
    encoding = (
        cpg_path.read_text(encoding="ascii").strip() if cpg_path.exists() else "cp949"
    )

    with path.open("rb") as stream:
        header = stream.read(32)
        row_count = struct.unpack("<I", header[4:8])[0]
        header_length = struct.unpack("<H", header[8:10])[0]
        fields = []
        while stream.tell() < header_length - 1:
            descriptor = stream.read(32)
            if not descriptor or descriptor[0] == 0x0D:
                break
            name = descriptor[:11].split(b"\x00", 1)[0].decode("ascii")
            fields.append(
                {
                    "name": name,
                    "dbf_type": chr(descriptor[11]),
                    "length": descriptor[16],
                    "decimals": descriptor[17],
                }
            )

        stream.seek(header_length)
        rows = []
        for _ in range(min(MAX_SAMPLE_ROWS, row_count)):
            deleted_flag = stream.read(1)
            if not deleted_flag:
                break
            values = []
            for field in fields:
                raw_value = stream.read(field["length"])
                values.append(raw_value.decode(encoding, errors="replace").strip())
            if deleted_flag != b"*":
                rows.append(values)

    return row_count, fields, rows


def inspect_shapefile(directory: Path) -> dict[str, Any]:
    dbf_path = next(directory.glob("*.dbf"))
    row_count, fields, rows = read_dbf_fields(dbf_path)
    columns = []
    for index, field in enumerate(fields):
        values = [row[index] for row in rows if index < len(row)]
        example = next((value for value in values if value != ""), "")
        columns.append(
            {
                "name": field["name"],
                "inferred_type": {
                    "C": "text",
                    "N": "number",
                    "F": "number",
                    "D": "date",
                    "L": "boolean",
                }.get(field["dbf_type"], f"dbf_{field['dbf_type']}"),
                "example": example,
                "dbf_length": field["length"],
                "dbf_decimals": field["decimals"],
            }
        )

    prj_path = next(directory.glob("*.prj"), None)
    projection = prj_path.read_text(encoding="ascii") if prj_path else ""
    component_files = sorted(
        path.relative_to(PROJECT_ROOT).as_posix() for path in directory.iterdir() if path.is_file()
    )
    return {
        "path": directory.relative_to(PROJECT_ROOT).as_posix(),
        "size_bytes": sum(path.stat().st_size for path in directory.iterdir() if path.is_file()),
        "encoding": "UTF-8",
        "sample_rows": len(rows),
        "known_row_count_from_dbf_header": row_count,
        "column_count": len(fields),
        "columns": columns,
        "projection_wkt": projection,
        "component_files": component_files,
    }


def classify_csv(path: Path) -> str | None:
    for dataset_name in PRIMARY_DATASETS:
        if dataset_name in path.name:
            return dataset_name
    return None


def file_year(path: Path) -> int:
    match = re.search(r"(20\d{2})년", path.name)
    return int(match.group(1)) if match else 0


def build_report() -> dict[str, Any]:
    csv_files = sorted(RAW_ROOT.glob("*.csv"))
    grouped: dict[str, list[Path]] = defaultdict(list)
    extras: list[Path] = []
    for path in csv_files:
        dataset_name = classify_csv(path)
        if dataset_name is None:
            extras.append(path)
        elif "상권배후지" in path.name or "자치구" in path.name:
            extras.append(path)
        else:
            grouped[dataset_name].append(path)

    datasets = []
    for dataset_name in PRIMARY_DATASETS:
        if dataset_name == "영역-상권":
            directory = RAW_ROOT / "서울시 상권분석서비스(영역-상권)"
            datasets.append({"dataset_name": dataset_name, **inspect_shapefile(directory)})
            continue

        paths = sorted(grouped.get(dataset_name, []), key=file_year)
        inspected = [inspect_csv(path) for path in paths]
        if not inspected:
            datasets.append({"dataset_name": dataset_name, "missing": True})
            continue

        representative = inspected[-1]
        header_match = all(item["header"] == representative["header"] for item in inspected)
        schema_variants = []
        seen_headers: set[tuple[str, ...]] = set()
        for item in inspected:
            header_key = tuple(item["header"])
            if header_key in seen_headers:
                continue
            seen_headers.add(header_key)
            schema_variants.append(
                {
                    "path": item["path"],
                    "column_count": item["column_count"],
                    "columns": item["columns"],
                }
            )
        datasets.append(
            {
                "dataset_name": dataset_name,
                "path": representative["path"],
                "files": [item["path"] for item in inspected],
                "file_count": len(inspected),
                "total_size_bytes": sum(item["size_bytes"] for item in inspected),
                "encoding": representative["encoding"],
                "sample_rows": representative["sample_rows"],
                "column_count": representative["column_count"],
                "headers_match_across_files": header_match,
                "columns": representative["columns"],
                "schema_variants": schema_variants,
            }
        )

    return {
        "inspection_policy": {
            "full_dataset_loaded": False,
            "max_encoding_bytes_per_csv": MAX_ENCODING_BYTES,
            "max_sample_rows_per_file": MAX_SAMPLE_ROWS,
            "csv_files_examined": len(csv_files),
        },
        "datasets": datasets,
        "extra_files": [path.relative_to(PROJECT_ROOT).as_posix() for path in extras],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build_report(), ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
