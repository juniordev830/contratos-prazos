from datetime import date, timedelta
import pytest
from contratos_prazos import Contrato, Renovacao, proximos_vencimentos, renovar_contrato

def test_lists_upcoming_contracts_in_date_order():
    today = date(2026, 11, 3)
    contracts = [Contrato("B", today + timedelta(days=20)), Contrato("A", today + timedelta(days=5)), Contrato("Expired", today - timedelta(days=1))]
    assert [item.nome for item in proximos_vencimentos(contracts, today)] == ["A", "B"]

def test_rejects_invalid_window():
    with pytest.raises(ValueError): proximos_vencimentos([], date(2026, 11, 3), -1)


def test_renewal_keeps_prior_contract_unchanged_and_records_dates():
    original = Contrato("Contrato de suporte", date(2026, 11, 30))
    first = renovar_contrato(original, date(2027, 11, 30), date(2026, 11, 3))
    second = renovar_contrato(first, date(2028, 11, 30), date(2027, 11, 3))

    assert original.vencimento == date(2026, 11, 30)
    assert original.renovacoes == ()
    assert first.vencimento == date(2027, 11, 30)
    assert len(first.renovacoes) == 1
    assert second.renovacoes == (
        Renovacao(date(2026, 11, 30), date(2027, 11, 30), date(2026, 11, 3)),
        Renovacao(date(2027, 11, 30), date(2028, 11, 30), date(2027, 11, 3)),
    )
    assert proximos_vencimentos([original, second], date(2026, 11, 3), 40) == [original]


def test_rejects_backward_and_out_of_order_renewals():
    original = Contrato("Serviço", date(2026, 11, 30))
    with pytest.raises(ValueError):
        renovar_contrato(original, date(2026, 11, 30), date(2026, 11, 3))
    with pytest.raises(ValueError):
        renovar_contrato(original, date(2026, 10, 1), date(2026, 11, 3))
    first = renovar_contrato(original, date(2027, 11, 30), date(2026, 11, 3))
    with pytest.raises(ValueError):
        renovar_contrato(first, date(2028, 11, 30), date(2026, 11, 2))
    with pytest.raises(TypeError):
        renovar_contrato(first, "2028-11-30", date(2027, 11, 3))


def test_rejects_forged_renewal_history():
    current = date(2027, 11, 30)
    with pytest.raises(ValueError):
        Contrato("Serviço", current, (Renovacao(date(2026, 11, 30),
                                                  date(2027, 12, 1), date(2026, 11, 3)),))
    with pytest.raises(ValueError):
        Contrato("Serviço", current, (Renovacao(date(2027, 11, 30),
                                                  date(2026, 11, 30), date(2026, 11, 3)),))
    with pytest.raises(ValueError):
        Contrato("Serviço", current, [Renovacao(date(2026, 11, 30),
                                                 current, date(2026, 11, 3))])
