from __future__ import annotations

import struct
from pathlib import Path

from src.sentinel_core.data import (
    build_dataset_manifest,
    chunk_velocity_field,
    decode_float32_buffer,
    make_dataset_record,
    reshape_velocity_field,
    validate_dataset_record,
)
from src.sentinel_core.interfaces import FieldState
from src.sentinel_core.operator_adapter import (
    OperatorModel,
    state_from_dataset_record,
    state_from_field_state,
)


def test_decode_float32_buffer_round_trips_values() -> None:
    payload = struct.pack("<4f", 1.0, 2.5, -3.0, 4.25)

    decoded = decode_float32_buffer(payload)

    assert decoded == [1.0, 2.5, -3.0, 4.25]


def test_reshape_and_chunk_velocity_field() -> None:
    values = [float(index) for index in range(24)]

    volume = reshape_velocity_field(values, (2, 2, 2, 3))
    chunks = chunk_velocity_field(volume, 1)

    assert volume[0][0][0] == [0.0, 1.0, 2.0]
    assert len(chunks) == 8
    assert chunks[0][0] == (0, 0, 0)
    assert chunks[0][1][0][0][0] == [0.0, 1.0, 2.0]


def test_dataset_record_validation_accepts_consistent_shape() -> None:
    chunk = [[[[0.0, 1.0, 2.0]]]]
    record = make_dataset_record(
        dataset="isotropic1024coarse",
        time=0.1,
        chunk=chunk,
        chunk_index=(0, 0, 0),
        query_url="https://example.invalid/jhtdb",
    )
    manifest = build_dataset_manifest(
        dataset="isotropic1024coarse",
        record_path=Path("data/jhtdb/isotropic/velocity.jsonl"),
        records=1,
        chunk_shape=(1, 1, 1, 3),
        metadata={"query_url": "https://example.invalid/jhtdb"},
    )

    assert validate_dataset_record(record) == []
    assert manifest.chunk_shape == (1, 1, 1, 3)


def test_operator_model_accepts_adapter_state_from_runtime_and_dataset() -> None:
    runtime_state: FieldState = {
        "kind": "grid",
        "channels": {"velocity": [[1.0]], "vorticity": [[0.5]]},
        "geometry_id": "grid16",
        "time_index": 0,
        "metadata": {"boundary": "periodic"},
    }
    dataset_record = make_dataset_record(
        dataset="isotropic1024coarse",
        time=0.1,
        chunk=[[[[0.0, 1.0, 2.0]]]],
        chunk_index=(0, 0, 0),
        query_url="https://example.invalid/jhtdb",
    )
    input_schema = state_from_field_state(runtime_state)
    output_schema = state_from_dataset_record(dataset_record)

    model = OperatorModel(
        type="DiffFNO",
        input_schema=input_schema,
        output_schema=output_schema,
        invariants_preserved=("energy",),
        boundary_behavior={"periodic_match": 1.0},
    )

    assert model.type == "DiffFNO"
    assert model.input_schema.channels == ("velocity", "vorticity")
    assert model.output_schema.shape == (1, 1, 1, 3)
