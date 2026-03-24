from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Mapping, TypedDict
from urllib.request import urlopen


class DatasetState(TypedDict):
    type: str
    shape: list[int]
    data: object


class DatasetRecord(TypedDict):
    source: str
    dataset: str
    time: float
    state: DatasetState
    operator: str
    invariants: dict[str, object]
    boundary: dict[str, object]
    metadata: dict[str, object]


@dataclass(frozen=True)
class DatasetManifest:
    schema_version: str
    source: str
    dataset: str
    record_path: str
    records: int
    state_type: str
    chunk_shape: tuple[int, ...]
    operator: str
    metadata: dict[str, str] = field(default_factory=dict)


def _json_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def fetch_binary_payload(url: str, timeout: float = 30.0) -> bytes:
    with urlopen(url, timeout=timeout) as response:
        return response.read()


def decode_float32_buffer(payload: bytes) -> list[float]:
    if len(payload) % 4 != 0:
        raise ValueError("binary payload length must be divisible by 4 for float32 decoding")
    return [value[0] for value in struct.iter_unpack("<f", payload)]


def expected_values(shape: tuple[int, int, int, int]) -> int:
    nx, ny, nz, channels = shape
    return nx * ny * nz * channels


def reshape_velocity_field(
    values: list[float], shape: tuple[int, int, int, int]
) -> list[list[list[list[float]]]]:
    nx, ny, nz, channels = shape
    expected = expected_values(shape)
    if len(values) != expected:
        raise ValueError(f"expected {expected} float32 values, received {len(values)}")
    cursor = 0
    volume: list[list[list[list[float]]]] = []
    for _ in range(nx):
        plane: list[list[list[float]]] = []
        for _ in range(ny):
            row: list[list[float]] = []
            for _ in range(nz):
                cell = values[cursor : cursor + channels]
                cursor += channels
                row.append(cell)
            plane.append(row)
        volume.append(plane)
    return volume


def chunk_velocity_field(
    volume: list[list[list[list[float]]]], chunk_size: int
) -> list[tuple[tuple[int, int, int], list[list[list[list[float]]]]]]:
    nx = len(volume)
    ny = len(volume[0]) if volume else 0
    nz = len(volume[0][0]) if volume and volume[0] else 0
    chunks: list[tuple[tuple[int, int, int], list[list[list[list[float]]]]]] = []
    for i in range(0, nx, chunk_size):
        for j in range(0, ny, chunk_size):
            for k in range(0, nz, chunk_size):
                chunk = [
                    [
                        [list(cell) for cell in row[k : k + chunk_size]]
                        for row in plane[j : j + chunk_size]
                    ]
                    for plane in volume[i : i + chunk_size]
                ]
                chunks.append(((i, j, k), chunk))
    return chunks


def make_dataset_record(
    *,
    dataset: str,
    time: float,
    chunk: list[list[list[list[float]]]],
    chunk_index: tuple[int, int, int],
    query_url: str,
    boundary_type: str = "periodic",
) -> DatasetRecord:
    shape = [
        len(chunk),
        len(chunk[0]) if chunk else 0,
        len(chunk[0][0]) if chunk and chunk[0] else 0,
        len(chunk[0][0][0]) if chunk and chunk[0] and chunk[0][0] else 0,
    ]
    return {
        "source": "JHTDB",
        "dataset": dataset,
        "time": time,
        "state": {
            "type": "velocity_field",
            "shape": shape,
            "data": chunk,
        },
        "operator": "NavierStokes",
        "invariants": {},
        "boundary": {"type": boundary_type},
        "metadata": {
            "chunk_index": list(chunk_index),
            "query_url": query_url,
        },
    }


def dataset_output_dir(root: Path, dataset: str, metadata: Mapping[str, object]) -> Path:
    slug = _json_hash({"dataset": dataset, **dict(metadata)})
    path = root / dataset / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_jsonl(path: Path, records: list[DatasetRecord]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def write_dataset_manifest(path: Path, manifest: DatasetManifest) -> None:
    path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True), encoding="utf-8")


def flatten_nested(values: object) -> list[float]:
    if isinstance(values, list):
        flat: list[float] = []
        for item in values:
            flat.extend(flatten_nested(item))
        return flat
    if isinstance(values, (int, float)):
        return [float(values)]
    raise ValueError("dataset values must be nested lists of numeric values")


def summarize_jsonl(path: Path) -> dict[str, object]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = [json.loads(line) for line in lines]
    if not records:
        raise ValueError("dataset JSONL must contain at least one record")
    shapes = sorted({tuple(record["state"]["shape"]) for record in records})
    return {
        "dataset": records[0]["dataset"],
        "source": records[0]["source"],
        "records": len(records),
        "shapes": [list(shape) for shape in shapes],
        "state_type": records[0]["state"]["type"],
    }


def validate_dataset_record(record: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    for field_name in ("source", "dataset", "time", "state", "operator", "invariants", "boundary"):
        if field_name not in record:
            errors.append(f"missing field: {field_name}")
    state = record.get("state")
    if not isinstance(state, dict):
        errors.append("state must be a mapping")
        return errors
    for field_name in ("type", "shape", "data"):
        if field_name not in state:
            errors.append(f"missing state field: {field_name}")
    shape = state.get("shape")
    data = state.get("data")
    if isinstance(shape, list) and len(shape) == 4:
        try:
            observed = len(flatten_nested(data))
            dims = [int(value) for value in shape]
            expected = expected_values((dims[0], dims[1], dims[2], dims[3]))
            if observed != expected:
                errors.append(f"state.data contains {observed} values but shape expects {expected}")
        except ValueError as exc:
            errors.append(str(exc))
    else:
        errors.append("state.shape must be a 4D list")
    return errors


def validate_dataset_artifacts(manifest_path: Path, data_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lines = [line for line in data_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors: list[str] = []
    if manifest.get("schema_version") != "1":
        errors.append("manifest schema_version must be '1'")
    if manifest.get("record_path") != str(data_path):
        errors.append("manifest record_path does not match dataset path")
    if manifest.get("records") != len(lines):
        errors.append("manifest record count does not match dataset JSONL")
    for index, line in enumerate(lines):
        errors.extend(
            f"record {index}: {error}" for error in validate_dataset_record(json.loads(line))
        )
    return {"valid": not errors, "errors": errors, "records": len(lines)}


def build_dataset_manifest(
    *,
    dataset: str,
    record_path: Path,
    records: int,
    chunk_shape: tuple[int, ...],
    metadata: dict[str, str],
) -> DatasetManifest:
    return DatasetManifest(
        schema_version="1",
        source="JHTDB",
        dataset=dataset,
        record_path=str(record_path),
        records=records,
        state_type="velocity_field",
        chunk_shape=chunk_shape,
        operator="NavierStokes",
        metadata=metadata,
    )


def ingest_jhtdb_dataset(
    *,
    url: str,
    dataset: str,
    time: float,
    shape: tuple[int, int, int, int],
    chunk_size: int,
    output_root: Path,
) -> dict[str, object]:
    metadata = {
        "query_url": url,
        "shape": "x".join(str(value) for value in shape),
        "chunk_size": str(chunk_size),
    }
    destination = dataset_output_dir(output_root, dataset, metadata)
    payload = fetch_binary_payload(url)
    decoded = decode_float32_buffer(payload)
    volume = reshape_velocity_field(decoded, shape)
    chunks = chunk_velocity_field(volume, chunk_size)
    records = [
        make_dataset_record(
            dataset=dataset,
            time=time,
            chunk=chunk,
            chunk_index=chunk_index,
            query_url=url,
        )
        for chunk_index, chunk in chunks
    ]
    data_path = destination / "velocity.jsonl"
    write_jsonl(data_path, records)
    manifest = build_dataset_manifest(
        dataset=dataset,
        record_path=data_path,
        records=len(records),
        chunk_shape=tuple(records[0]["state"]["shape"]) if records else (0, 0, 0, 0),
        metadata=metadata,
    )
    manifest_path = destination / "manifest.json"
    write_dataset_manifest(manifest_path, manifest)
    summary = summarize_jsonl(data_path)
    summary_path = destination / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "dataset": dataset,
        "output_dir": str(destination),
        "data_path": str(data_path),
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
        "records": len(records),
        "chunk_shape": list(manifest.chunk_shape),
    }
