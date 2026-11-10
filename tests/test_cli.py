import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_cli(data_path, *args):
    return subprocess.run(
        [
            sys.executable, "-m", "contratos_prazos.cli",
            "--data", str(data_path), *args,
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_cli_add_list_renew_summary_and_remove(tmp_path):
    path = tmp_path / "contracts.json"
    add = run_cli(
        path, "add", "demo1", "Contrato fictício", "Empresa X",
        "2026-01-01", "2027-01-01", "125000", "--renewal-days", "30",
    )
    assert add.returncode == 0, add.stderr
    assert "cadastrado" in add.stdout
    listing = run_cli(path, "list")
    assert listing.returncode == 0
    assert "Contrato fictício" in listing.stdout
    summary = run_cli(path, "summary")
    assert summary.returncode == 0
    assert "Contratos: 1" in summary.stdout
    renewal = run_cli(path, "renew", "demo1")
    assert renewal.returncode == 0
    assert "2027-01-31" in renewal.stdout
    assert run_cli(path, "remove", "demo1").returncode == 0
    assert "Nenhum contrato" in run_cli(path, "list").stdout


def test_cli_rejects_bad_dates_and_duplicate_ids(tmp_path):
    path = tmp_path / "contracts.json"
    invalid = run_cli(
        path, "add", "id1", "Exemplo", "Empresa X",
        "2026-02-30", "2027-01-01", "1000",
    )
    assert invalid.returncode != 0
    assert not path.exists()

    args = (
        "add", "id1", "Exemplo", "Empresa X",
        "2026-01-01", "2027-01-01", "1000",
    )
    assert run_cli(path, *args).returncode == 0
    duplicate = run_cli(path, *args)
    assert duplicate.returncode != 0
    assert "duplicado" in duplicate.stderr
    assert run_cli(path, "renew", "missing").returncode != 0


def test_cli_help_on_no_subcommand(tmp_path):
    help_result = run_cli(tmp_path / "db.json")
    assert help_result.returncode == 0
    assert "usage:" in help_result.stdout


def test_cli_rejects_invalid_utf8_without_traceback_or_file_changes(tmp_path):
    path = tmp_path / "contracts.json"
    original = b'{"version":1,"contracts":["\xff"]}'
    path.write_bytes(original)
    result = run_cli(path, "list")
    assert result.returncode == 2
    assert "JSON" in result.stderr
    assert "Traceback" not in result.stderr
    assert path.read_bytes() == original
