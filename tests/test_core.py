from datetime import date, timedelta
import pytest
from contratos_prazos import Contrato, proximos_vencimentos

def test_lists_upcoming_contracts_in_date_order():
    today = date(2026, 11, 3)
    contracts = [Contrato("B", today + timedelta(days=20)), Contrato("A", today + timedelta(days=5)), Contrato("Expired", today - timedelta(days=1))]
    assert [item.nome for item in proximos_vencimentos(contracts, today)] == ["A", "B"]

def test_rejects_invalid_window():
    with pytest.raises(ValueError): proximos_vencimentos([], date(2026, 11, 3), -1)


def test_upcoming_window_includes_last_calendar_day_without_overflow():
    today = date(9999, 12, 30)
    contracts = [Contrato("Amanhã", date.max), Contrato("Ontem", date(9999, 12, 29))]
    assert proximos_vencimentos(contracts, today, 30) == [contracts[0]]
    assert proximos_vencimentos(contracts, today, 0) == []

def test_legacy_contract_validates_name_and_expiration_type():
    today = date(2026, 11, 21)
    for name in (" ", chr(10) + "Invalido", "N" * 161, None):
        with pytest.raises(ValueError):
            Contrato(name, today)
    with pytest.raises(ValueError):
        Contrato("Suporte", "2026-11-21")
    assert Contrato(" Suporte ", today).nome == "Suporte"


def test_legacy_deadline_rejects_boolean_or_bad_input_shapes():
    today = date(2026, 11, 21)
    for window in (True, 1.5, "30"):
        with pytest.raises(ValueError):
            proximos_vencimentos([], today, window)
    with pytest.raises(ValueError):
        proximos_vencimentos([], "2026-11-21")
    with pytest.raises(ValueError):
        proximos_vencimentos([None], today)


def test_legacy_due_date_ties_have_stable_name_order():
    today = date(2026, 11, 21)
    entries = [Contrato("Zeta", today), Contrato("Alfa", today)]
    assert [x.nome for x in proximos_vencimentos(entries, today)] == ["Alfa", "Zeta"]


def test_legacy_upcoming_deadlines_reject_overlarge_registry():
    today = date(2026, 11, 21)
    example = Contrato("Exemplo", today)
    with pytest.raises(ValueError, match="3000"):
        proximos_vencimentos([example] * 3001, today)
    assert len(proximos_vencimentos([example] * 3000, today)) == 3000
