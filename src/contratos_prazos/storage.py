"""Versioned, locally stored JSON contracts; no network or external services."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .records import ContractRecord, validate_registry

MAX_BYTES = 1_000_000
SCHEMA = 1


def default_path() -> Path:
    return Path(
        os.environ.get("GX_CONTRACTS_FILE", str(Path.home() / ".gx-contratos" / "contratos.json"))
    ).expanduser()


def load_contracts(path: Path | None = None) -> list[ContractRecord]:
    target = path if path is not None else default_path()
    try:
        if target.stat().st_size > MAX_BYTES:
            raise ValueError("arquivo de contratos muito grande")
        payload = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError("arquivo JSON inválido") from error
    if (
        not isinstance(payload, dict)
        or payload.get("version") != SCHEMA
        or not isinstance(payload.get("contracts"), list)
    ):
        raise ValueError("estrutura de armazenamento inválida")
    return validate_registry([
        ContractRecord.from_dict(item) for item in payload["contracts"]
    ])


def save_contracts(records: list[ContractRecord], path: Path | None = None) -> int:
    catalog = validate_registry(records)
    target = path if path is not None else default_path()
    document = {
        "version": SCHEMA,
        "contracts": [item.to_dict() for item in catalog],
    }
    encoded = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAX_BYTES:
        raise ValueError("catálogo excede 1 MB")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    # Atomic replace keeps a valid older version if the write fails.
    temporary: str | None = None
    try:
        with NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=".contratos-", suffix=".tmp",
            delete=False,
        ) as output:
            temporary = output.name
            os.chmod(temporary, 0o600)
            output.write(encoded)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    return len(catalog)
