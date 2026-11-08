from dataclasses import replace
from datetime import date, timedelta

import pytest

from contratos_prazos.records import (
    ContractRecord, parse_date, add_contract, remove_contract,
    renew_contract, search_contracts, contract_status, registry_summary,
)


TODAY = date(2026, 11, 7)


def make_contract(**overrides):
    values = {
        "id": "contract-001",
        "title": "Manutenção de equipamentos",
        "counterparty": "Empresa Exemplo",
        "started_on": date(2026, 1, 1),
        "expires_on": date(2026, 11, 17),
        "amount_cents": 150_000,
        "renewal_days": 30,
    }
    values.update(overrides)
    return ContractRecord(**values)


def test_parse_date_is_strict_and_handles_leap_years():
    assert parse_date("2024-02-29") == date(2024, 2, 29)
    for invalid in ("2026-02-29", "2026-04-31", "2026-2-1", "", "not-a-date"):
        with pytest.raises(ValueError):
            parse_date(invalid)


def test_record_validation_rejects_invalid_data():
    invalid = [
        {"id": "bad id"},
        {"title": ""},
        {"counterparty": " \n bad"},
        {"started_on": date(2027, 1, 1)},
        {"amount_cents": -100},
        {"amount_cents": 1.5},
        {"renewal_days": 3651},
        {"renewal_count": -1},
        {"notes": "x" * 1001},
    ]
    for changes in invalid:
        with pytest.raises(ValueError):
            make_contract(**changes)


def test_record_serialization_round_trip():
    original = make_contract(notes="dados fictícios")
    loaded = ContractRecord.from_dict(original.to_dict())
    assert original == loaded
    with pytest.raises(ValueError):
        ContractRecord.from_dict({**original.to_dict(), "unexpected": True})


def test_registry_is_immutable_and_rejects_duplicates():
    original = []
    first = make_contract()
    added = add_contract(original, first)
    assert original == []
    assert added == [first]
    with pytest.raises(ValueError, match="duplicado"):
        add_contract(added, first)
    assert remove_contract(added, first.id) == []
    assert added == [first]
    with pytest.raises(KeyError):
        remove_contract(added, "missing")


def test_renewal_changes_only_expiration_and_counter():
    original = make_contract()
    next_records = renew_contract([original], original.id)
    assert next_records[0].expires_on == date(2026, 12, 17)
    assert next_records[0].started_on == original.started_on
    assert next_records[0].renewal_count == 1
    assert original.renewal_count == 0
    again = renew_contract(next_records, original.id, 60)
    assert again[0].expires_on == date(2027, 2, 15)
    assert again[0].renewal_count == 2


def test_renewal_rejects_explicit_zero_or_missing_contract():
    original = make_contract()
    with pytest.raises(ValueError):
        renew_contract([original], original.id, 0)
    with pytest.raises(KeyError):
        renew_contract([original], "not-found")


def test_renewal_rejects_calendar_overflow():
    source = make_contract(
        started_on=date(9999, 12, 1),
        expires_on=date(9999, 12, 31),
    )
    with pytest.raises(ValueError):
        renew_contract([source], source.id)


def test_statuses_search_order_and_day_window():
    expired = make_contract(id="old", title="Contrato A", expires_on=TODAY - timedelta(days=1))
    due = make_contract(id="due", title="Contrato B", expires_on=TODAY + timedelta(days=5))
    active = make_contract(id="future", title="Contrato C", expires_on=TODAY + timedelta(days=200))
    entries = [active, expired, due]
    assert contract_status(expired, TODAY) == "expired"
    assert contract_status(due, TODAY) == "due"
    assert contract_status(active, TODAY) == "active"
    assert [item.id for item in search_contracts(entries, TODAY)] == ["old", "due", "future"]
    assert [item.id for item in search_contracts(entries, TODAY, status="due")] == ["due"]
    assert [item.id for item in search_contracts(entries, TODAY, query="EMPRESA")] == [
        "old", "due", "future"
    ]
    assert search_contracts(entries, TODAY, status="due", days=2) == []
    with pytest.raises(ValueError):
        search_contracts(entries, TODAY, status="wrong")
    with pytest.raises(ValueError):
        contract_status(due, TODAY, -1)


def test_registry_summary_counts_and_nearest_date():
    entries = [
        make_contract(id="a", expires_on=TODAY - timedelta(days=1), renewal_count=2),
        make_contract(id="b", expires_on=TODAY + timedelta(days=2)),
        make_contract(id="c", expires_on=TODAY + timedelta(days=80)),
    ]
    report = registry_summary(entries, TODAY)
    assert report["total"] == 3
    assert report["expired"] == report["due"] == report["active"] == 1
    assert report["amount_cents"] == 450_000
    assert report["renewals"] == 2
    assert report["next_expiration"] == (TODAY + timedelta(days=2)).isoformat()
    assert registry_summary([], TODAY)["next_expiration"] is None
