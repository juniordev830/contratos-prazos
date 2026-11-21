from __future__ import annotations
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True, slots=True)
class Contrato:
    nome: str
    vencimento: date
    def __post_init__(self) -> None:
        if not isinstance(self.nome, str) or not 1 <= len(self.nome.strip()) <= 160:
            raise ValueError("nome deve conter de 1 a 160 caracteres")
        if any(ord(char) < 32 for char in self.nome):
            raise ValueError("nome contém caracteres de controle")
        if type(self.vencimento) is not date:
            raise ValueError("vencimento deve ser uma data")
        object.__setattr__(self, "nome", self.nome.strip())


def proximos_vencimentos(contratos: list[Contrato], hoje: date, dias: int = 30) -> list[Contrato]:
    if type(hoje) is not date:
        raise ValueError("hoje deve ser uma data")
    if type(dias) is not int or not 0 <= dias <= 3650:
        raise ValueError("dias deve estar entre 0 e 3650")
    if not isinstance(contratos, list) or len(contratos) > 3000:
        raise ValueError("contratos deve ser uma lista com até 3000 contratos")
    if any(not isinstance(item, Contrato) for item in contratos):
        raise ValueError("contratos deve conter somente objetos Contrato")
    proximos = (contrato for contrato in contratos if 0 <= (contrato.vencimento - hoje).days <= dias)
    return sorted(proximos, key=lambda contrato: (contrato.vencimento, contrato.nome.casefold()))
