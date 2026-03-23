param(
    [Parameter(Position = 0)]
    [string]$Task = "help"
)

switch ($Task) {
    "sync" { uv sync --dev }
    "format" { uv run ruff format src tests }
    "check" {
        uv run ruff check src tests
        uv run ruff format --check src tests
        uv run mypy src tests
        uv run pytest -q
    }
    "smoke" { uv run sentinel smoke grid --config configs/tasks/turbulence2d_baseline.yaml }
    "bench" { uv run sentinel bench turbulence2d --suite configs/benchmarks/turbulence_horizon.yaml --seed 7 }
    "native-configure" { cmake --preset native-debug }
    default {
        Write-Host "Tasks: sync, format, check, smoke, bench, native-configure"
    }
}
