from datetime import date, timedelta
import pytest
from contratos_prazos import Contrato, proximos_vencimentos

def test_lists_upcoming_contracts_in_date_order():
    today = date(2026, 11, 3)
    contracts = [Contrato("B", today + timedelta(days=20)), Contrato("A", today + timedelta(days=5)), Contrato("Expired", today - timedelta(days=1))]
    assert [item.nome for item in proximos_vencimentos(contracts, today)] == ["A", "B"]

def test_rejects_invalid_window():
    with pytest.raises(ValueError): proximos_vencimentos([], date(2026, 11, 3), -1)
