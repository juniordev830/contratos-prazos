from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta

@dataclass(frozen=True, slots=True)
class Contrato:
    nome: str
    vencimento: date
    def __post_init__(self) -> None:
        if not self.nome.strip(): raise ValueError("nome obrigatório")

def proximos_vencimentos(contratos: list[Contrato], hoje: date, dias: int = 30) -> list[Contrato]:
    if dias < 0 or dias > 3650: raise ValueError("dias deve estar entre 0 e 3650")
    limite = hoje + timedelta(days=dias)
    return sorted((contrato for contrato in contratos if hoje <= contrato.vencimento <= limite), key=lambda contrato: contrato.vencimento)
