from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class Renovacao:
    vencimento_anterior: date
    novo_vencimento: date
    registrada_em: date


@dataclass(frozen=True, slots=True)
class Contrato:
    nome: str
    vencimento: date
    renovacoes: tuple[Renovacao, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nome, str) or not self.nome.strip():
            raise ValueError("nome obrigatório")
        if not isinstance(self.vencimento, date):
            raise TypeError("vencimento deve ser data")
        if not isinstance(self.renovacoes, tuple):
            raise ValueError("renovacoes devem ser uma tupla imutável")
        previous_new_date = None
        previous_registration = None
        for index, record in enumerate(self.renovacoes):
            if not isinstance(record, Renovacao) or any(
                not isinstance(day, date)
                for day in (record.vencimento_anterior, record.novo_vencimento, record.registrada_em)
            ):
                raise ValueError("registro de renovação inválido")
            if record.novo_vencimento <= record.vencimento_anterior:
                raise ValueError("renovação deve aumentar o vencimento")
            if previous_new_date is not None and record.vencimento_anterior != previous_new_date:
                raise ValueError("histórico de renovação inconsistente")
            if previous_registration is not None and record.registrada_em < previous_registration:
                raise ValueError("datas de registro fora de ordem")
            previous_new_date = record.novo_vencimento
            previous_registration = record.registrada_em
        if self.renovacoes and self.renovacoes[-1].novo_vencimento != self.vencimento:
            raise ValueError("vencimento atual diverge do histórico")


def renovar_contrato(contrato: Contrato, novo_vencimento: date, registrada_em: date) -> Contrato:
    """Returns a new contract with an immutable, traceable renewal record."""
    if not isinstance(contrato, Contrato):
        raise TypeError("contrato inválido")
    if not isinstance(novo_vencimento, date) or not isinstance(registrada_em, date):
        raise TypeError("datas inválidas")
    if novo_vencimento <= contrato.vencimento:
        raise ValueError("nova data deve ser posterior ao vencimento atual")
    if contrato.renovacoes and registrada_em < contrato.renovacoes[-1].registrada_em:
        raise ValueError("registro anterior à renovação existente")
    renewal = Renovacao(contrato.vencimento, novo_vencimento, registrada_em)
    return Contrato(contrato.nome, novo_vencimento, contrato.renovacoes + (renewal,))


def proximos_vencimentos(contratos: list[Contrato], hoje: date, dias: int = 30) -> list[Contrato]:
    if dias < 0 or dias > 3650:
        raise ValueError("dias deve estar entre 0 e 3650")
    limite = hoje + timedelta(days=dias)
    return sorted(
        (contrato for contrato in contratos if hoje <= contrato.vencimento <= limite),
        key=lambda contrato: (contrato.vencimento, contrato.nome),
    )
