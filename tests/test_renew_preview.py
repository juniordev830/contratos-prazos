"""Integração da prévia de renovação: não deve modificar o cadastro."""
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def command(path: Path, *arguments: str):
    return subprocess.run(
        [sys.executable, "-m", "contratos_prazos.cli", "--data", str(path),
         *arguments],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        timeout=10,
    )


def test_renew_dry_run_calculates_new_date_without_writing(tmp_path):
    path = tmp_path / "contracts.json"
    created = command(
        path, "add", "demo01", "Contrato fictício", "Empresa de Teste",
        "2026-01-01", "2026-12-31", "10000", "--renewal-days", "30",
    )
    assert created.returncode == 0, created.stderr
    before = path.read_bytes()
    before_mtime = path.stat().st_mtime_ns

    preview = command(path, "renew", "demo01", "--dry-run")
    assert preview.returncode == 0, preview.stderr
    assert "Simulação sem gravação" in preview.stdout
    assert "2026-12-31" in preview.stdout
    assert "2027-01-30" in preview.stdout
    assert "0 -> 1" in preview.stdout
    assert path.read_bytes() == before
    assert path.stat().st_mtime_ns == before_mtime

    override = command(path, "renew", "demo01", "--days", "60", "--dry-run")
    assert override.returncode == 0, override.stderr
    assert "2027-03-01" in override.stdout
    assert path.read_bytes() == before

    committed = command(path, "renew", "demo01", "--days", "60")
    assert committed.returncode == 0, committed.stderr
    assert "2027-03-01" in committed.stdout
    assert path.read_bytes() != before
    assert command(path, "list", "--as-of", "2027-02-01").returncode == 0


def test_invalid_dry_run_leaves_previous_state_intact(tmp_path):
    path = tmp_path / "contracts.json"
    assert command(
        path, "add", "x1", "Serviço", "Empresa",
        "2026-01-01", "2026-11-30", "2500", "--renewal-days", "7",
    ).returncode == 0
    before = path.read_bytes()
    for arguments in (
        ("renew", "not-found", "--dry-run"),
        ("renew", "x1", "--days", "0", "--dry-run"),
        ("renew", "x1", "--days", "3651", "--dry-run"),
    ):
        result = command(path, *arguments)
        assert result.returncode == 2
        assert "Traceback" not in result.stderr
        assert path.read_bytes() == before

    new_file = tmp_path / "missing.json"
    missing = command(new_file, "renew", "missing", "--dry-run")
    assert missing.returncode == 2
    assert not new_file.exists()
