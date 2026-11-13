import json
from datetime import date

import pytest

from contratos_prazos.records import ContractRecord
from contratos_prazos.storage import MAX_BYTES, load_contracts, save_contracts


def example():
    return ContractRecord(
        id="first",
        title="Aluguel demonstrativo",
        counterparty="Cliente Fictício",
        started_on=date(2026, 1, 1),
        expires_on=date(2026, 12, 31),
        amount_cents=12_500,
        renewal_days=30,
        notes="Exemplo sem dados reais",
    )


def test_missing_file_yields_empty_registry(tmp_path):
    assert load_contracts(tmp_path / "missing.json") == []


def test_save_and_reload_versioned_file(tmp_path):
    file = tmp_path / "private" / "contracts.json"
    assert save_contracts([example()], file) == 1
    data = json.loads(file.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["contracts"][0]["id"] == "first"
    assert load_contracts(file) == [example()]
    assert save_contracts([], file) == 0
    assert load_contracts(file) == []


def test_invalid_new_data_keeps_original_file(tmp_path):
    file = tmp_path / "contracts.json"
    save_contracts([example()], file)
    previous = file.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        save_contracts([example(), example()], file)
    assert file.read_text(encoding="utf-8") == previous


def test_rejects_unsupported_or_corrupt_json(tmp_path):
    file = tmp_path / "contracts.json"
    for data in (
        "{invalid",
        '{"version":2,"contracts":[]}',
        '{"version":1,"contracts":"bad"}',
    ):
        file.write_text(data, encoding="utf-8")
        with pytest.raises(ValueError):
            load_contracts(file)


def test_rejects_invalid_contract_in_json(tmp_path):
    file = tmp_path / "contracts.json"
    document = {"version": 1, "contracts": [{**example().to_dict(), "amount_cents": -1}]}
    file.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        load_contracts(file)


def test_rejects_boolean_schema_version(tmp_path):
    file = tmp_path / "contracts.json"
    file.write_text('{"version":true,"contracts":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="estrutura de armazenamento"):
        load_contracts(file)


def test_rejects_oversized_json_without_parsing(tmp_path):
    file = tmp_path / "large.json"
    file.write_bytes(b" " * (MAX_BYTES + 1))
    with pytest.raises(ValueError, match="muito grande"):
        load_contracts(file)
