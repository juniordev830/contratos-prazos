"""Immutable contract records with strict input validation."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
import re
from typing import Mapping, Any

MAX_RECORDS = 3000
_ID = re.compile(r"^[A-Za-z0-9_-]{1,50}$")


def parse_date(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("data deve estar em AAAA-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("data de calendário inválida") from error


@dataclass(frozen=True, slots=True)
class ContractRecord:
    id: str
    title: str
    counterparty: str
    started_on: date
    expires_on: date
    amount_cents: int = 0
    renewal_days: int = 0
    renewal_count: int = 0
    notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _ID.fullmatch(self.id):
            raise ValueError("id inválido")
        for name, text in (("título", self.title), ("contraparte", self.counterparty)):
            if not isinstance(text, str) or not text.strip() or len(text.strip()) > 160:
                raise ValueError(f"{name} inválido")
            if any(ord(char) < 32 for char in text):
                raise ValueError(f"{name} contém caracteres de controle")
        if not isinstance(self.started_on, date) or not isinstance(self.expires_on, date):
            raise ValueError("datas precisam ser instâncias date")
        if self.expires_on < self.started_on:
            raise ValueError("vencimento anterior ao início")
        if type(self.amount_cents) is not int or not 0 <= self.amount_cents <= 100_000_000_000:
            raise ValueError("valor em centavos fora do limite")
        if type(self.renewal_days) is not int or not 0 <= self.renewal_days <= 3650:
            raise ValueError("prazo de renovação inválido")
        if type(self.renewal_count) is not int or not 0 <= self.renewal_count <= 1000:
            raise ValueError("contagem de renovações inválida")
        if not isinstance(self.notes, str) or len(self.notes) > 1000:
            raise ValueError("observações inválidas")
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "counterparty", self.counterparty.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "counterparty": self.counterparty,
            "started_on": self.started_on.isoformat(),
            "expires_on": self.expires_on.isoformat(),
            "amount_cents": self.amount_cents,
            "renewal_days": self.renewal_days,
            "renewal_count": self.renewal_count,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ContractRecord":
        if not isinstance(payload, Mapping):
            raise ValueError("registro precisa ser objeto JSON")
        expected = {
            "id", "title", "counterparty", "started_on", "expires_on",
            "amount_cents", "renewal_days", "renewal_count", "notes",
        }
        if set(payload) - expected:
            raise ValueError("campos desconhecidos no contrato")
        values = dict(payload)
        values["started_on"] = parse_date(values["started_on"])
        values["expires_on"] = parse_date(values["expires_on"])
        return cls(**values)


def validate_registry(records: list[ContractRecord]) -> list[ContractRecord]:
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ValueError("registro deve ser lista com até 3000 contratos")
    seen: set[str] = set()
    for item in records:
        if not isinstance(item, ContractRecord):
            raise ValueError("registro contém contrato inválido")
        if item.id in seen:
            raise ValueError("identificador duplicado: " + item.id)
        seen.add(item.id)
    return list(records)


def add_contract(records: list[ContractRecord], new: ContractRecord) -> list[ContractRecord]:
    existing = validate_registry(records)
    if len(existing) >= MAX_RECORDS:
        raise ValueError("limite de contratos atingido")
    return validate_registry([*existing, new])


def remove_contract(records: list[ContractRecord], contract_id: str) -> list[ContractRecord]:
    existing = validate_registry(records)
    if not any(item.id == contract_id for item in existing):
        raise KeyError("contrato não encontrado: " + contract_id)
    return [item for item in existing if item.id != contract_id]


def renew_contract(
    records: list[ContractRecord], contract_id: str, days: int | None = None,
) -> list[ContractRecord]:
    existing = validate_registry(records)
    target = next((item for item in existing if item.id == contract_id), None)
    if target is None:
        raise KeyError("contrato não encontrado: " + contract_id)
    renewal_days = target.renewal_days if days is None else days
    if type(renewal_days) is not int or not 1 <= renewal_days <= 3650:
        raise ValueError("renovação precisa de 1 a 3650 dias")
    try:
        new_expiration = target.expires_on + timedelta(days=renewal_days)
    except OverflowError as error:
        raise ValueError("vencimento fora do calendário permitido") from error
    new = replace(
        target, expires_on=new_expiration, renewal_count=target.renewal_count + 1,
    )
    return [new if item.id == contract_id else item for item in existing]


def contract_status(item: ContractRecord, today: date, days: int = 30) -> str:
    if not isinstance(today, date):
        raise ValueError("data de referência inválida")
    if type(days) is not int or not 0 <= days <= 3650:
        raise ValueError("janela de alerta fora do limite")
    remaining = (item.expires_on - today).days
    return "expired" if remaining < 0 else "due" if remaining <= days else "active"


def search_contracts(
    records: list[ContractRecord], today: date, *,
    status: str = "all", query: str = "", days: int = 30,
) -> list[ContractRecord]:
    if status not in ("all", "expired", "due", "active"):
        raise ValueError("status inválido")
    if not isinstance(query, str) or len(query) > 120:
        raise ValueError("busca inválida")
    words = query.casefold().strip()
    return sorted(
        (
            item for item in validate_registry(records)
            if (status == "all" or contract_status(item, today, days) == status)
            and (not words or any(
                words in value.casefold()
                for value in (item.title, item.counterparty, item.id)
            ))
        ),
        key=lambda item: (item.expires_on, item.id),
    )


def registry_summary(records: list[ContractRecord], today: date) -> dict[str, Any]:
    entries = search_contracts(records, today)
    counts = {
        status: sum(contract_status(item, today) == status for item in entries)
        for status in ("expired", "due", "active")
    }
    return {
        "total": len(entries),
        **counts,
        "amount_cents": sum(item.amount_cents for item in entries),
        "next_expiration": next(
            (item.expires_on.isoformat() for item in entries if item.expires_on >= today),
            None,
        ),
        "renewals": sum(item.renewal_count for item in entries),
    }
