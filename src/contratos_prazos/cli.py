"""Read-only queries and explicit local changes to contract deadlines."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

from .records import (
    ContractRecord, parse_date, add_contract, remove_contract,
    renew_contract, search_contracts, contract_status, registry_summary,
)
from .storage import load_contracts, save_contracts


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="contratos-prazos",
        description="Gerencie vencimentos contratuais em um arquivo JSON local.",
    )
    root.add_argument("--data", type=Path, default=None, help="caminho do arquivo JSON local")
    actions = root.add_subparsers(dest="command")

    add = actions.add_parser("add", help="cadastrar contrato")
    add.add_argument("id")
    add.add_argument("title")
    add.add_argument("counterparty")
    add.add_argument("started_on", help="AAAA-MM-DD")
    add.add_argument("expires_on", help="AAAA-MM-DD")
    add.add_argument("amount_cents", type=int)
    add.add_argument("--renewal-days", type=int, default=0)
    add.add_argument("--notes", default="")

    listing = actions.add_parser("list", help="listar e filtrar contratos")
    listing.add_argument("--status", choices=("all", "expired", "due", "active"), default="all")
    listing.add_argument("--days", type=int, default=30)
    listing.add_argument("--query", default="")
    listing.add_argument("--as-of", default=None, metavar="AAAA-MM-DD",
                         help="data de referência reproduzível para a consulta")

    renew = actions.add_parser("renew", help="registrar renovação")
    renew.add_argument("id")
    renew.add_argument("--days", type=int, default=None)

    remove = actions.add_parser("remove", help="excluir um contrato")
    remove.add_argument("id")

    summary = actions.add_parser("summary", help="relatório consolidado")
    summary.add_argument("--as-of", default=None, metavar="AAAA-MM-DD",
                         help="data de referência reproduzível para o relatório")
    return root


def main(argv: list[str] | None = None) -> int:
    root = parser()
    args = root.parse_args(argv)
    if args.command is None:
        root.print_help()
        return 0
    try:
        today = (parse_date(args.as_of)
                 if args.command in ("list", "summary") and args.as_of is not None
                 else date.today())
        entries = load_contracts(args.data)
        if args.command == "add":
            item = ContractRecord(
                id=args.id,
                title=args.title,
                counterparty=args.counterparty,
                started_on=parse_date(args.started_on),
                expires_on=parse_date(args.expires_on),
                amount_cents=args.amount_cents,
                renewal_days=args.renewal_days,
                notes=args.notes,
            )
            count = save_contracts(add_contract(entries, item), args.data)
            print(f"Contrato cadastrado: {item.id} (total: {count})")
        elif args.command == "renew":
            updated = renew_contract(entries, args.id, args.days)
            save_contracts(updated, args.data)
            item = next(item for item in updated if item.id == args.id)
            print(f"Renovação registrada: {item.id}; novo vencimento {item.expires_on}")
        elif args.command == "remove":
            save_contracts(remove_contract(entries, args.id), args.data)
            print(f"Contrato excluído: {args.id}")
        elif args.command == "list":
            selected = search_contracts(
                entries, today, status=args.status, query=args.query, days=args.days,
            )
            if not selected:
                print("Nenhum contrato encontrado.")
            for item in selected:
                status = contract_status(item, today, args.days)
                print(
                    f"{item.id} | {item.title} | {item.counterparty} | "
                    f"vencimento={item.expires_on} | status={status} | "
                    f"R$ {item.amount_cents // 100},{item.amount_cents % 100:02d}"
                )
        elif args.command == "summary":
            total = registry_summary(entries, today)
            print(f"Contratos: {total['total']}")
            print(f"Ativos: {total['active']}")
            print(f"A vencer: {total['due']}")
            print(f"Vencidos: {total['expired']}")
            print(f"Renovações registradas: {total['renewals']}")
            print(f"Próximo vencimento: {total['next_expiration'] or 'nenhum'}")
            print(f"Total em centavos: {total['amount_cents']}")
    except (ValueError, KeyError, OSError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
