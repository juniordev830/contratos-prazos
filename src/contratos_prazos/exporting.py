"""Read-only, filtered reports for JSON consumers and spreadsheet users."""
from __future__ import annotations

import csv
import io
import json
from datetime import date

from .records import ContractRecord, contract_status, search_contracts


def export_contracts(
    records: list[ContractRecord], today: date, *, format: str = "json",
    status: str = "all", query: str = "", days: int = 30,
) -> str:
    if format not in ("json", "csv"):
        raise ValueError("formato deve ser json ou csv")
    selected = search_contracts(records, today, status=status, query=query, days=days)
    rows = [dict(item.to_dict(), status=contract_status(item, today, days)) for item in selected]
    if format == "json":
        return json.dumps({"as_of": today.isoformat(), "alert_days": days,
                           "contracts": rows}, ensure_ascii=False, indent=2) + "\n"

    fields = ("id", "title", "counterparty", "started_on", "expires_on",
              "amount_cents", "renewal_days", "renewal_count", "notes", "status")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, delimiter=";", lineterminator="\r\n")
    writer.writeheader()
    for row in rows:
        # Quoting alone does not stop spreadsheet formula evaluation. Preserve
        # numeric values, but export formula-like user text as literal text.
        safe = {
            key: "'" + value if isinstance(value, str) and
            (value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")))
            else value for key, value in row.items()
        }
        writer.writerow(safe)
    return output.getvalue()
