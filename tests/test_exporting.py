import csv
import io
import json
from datetime import date

import pytest

from contratos_prazos.exporting import export_contracts
from contratos_prazos.records import ContractRecord
from test_cli import run_cli

TODAY = date(2026,11,11)


def contract(id="one", title="Suporte", notes="", expiration=date(2026,11,20)):
    return ContractRecord(id,title,'Empresa "A"; teste',date(2026,1,1),expiration,12345,notes=notes)


def test_filtered_export_matches_reference_date_and_does_not_mutate():
    records=[contract(),contract("two","Hospedagem",expiration=date(2027,1,1))]
    before=list(records)
    report=json.loads(export_contracts(records,TODAY,status="due",query="SUPORTE"))
    assert report["as_of"]=="2026-11-11" and report["alert_days"]==30
    assert [item["id"] for item in report["contracts"]]==["one"]
    assert report["contracts"][0]["status"]=="due"
    assert records==before


@pytest.mark.parametrize("text",["=1+1","+SUM(1;2)","-1+2","@SUM(A1)"," \t=1", "\tplain", "\nplain"])
def test_spreadsheet_formula_text_is_literal_and_json_is_unchanged(text):
    records=[contract(notes=text)]
    csv_row=next(csv.DictReader(io.StringIO(export_contracts(records,TODAY,format="csv")),delimiter=";"))
    assert csv_row["notes"]=="'"+text
    assert csv_row["counterparty"]=='Empresa "A"; teste'
    assert csv_row["amount_cents"]=="12345"
    assert json.loads(export_contracts(records,TODAY))["contracts"][0]["notes"]==text


def test_empty_export_has_header_and_validates_filters():
    assert export_contracts([],TODAY,format="csv").startswith("id;title;")
    assert json.loads(export_contracts([],TODAY))["contracts"]==[]
    for kwargs in ({"format":"xml"},{"days":-1},{"status":"unknown"}):
        with pytest.raises(ValueError):export_contracts([],TODAY,**kwargs)


def test_cli_export_preserves_file_and_has_no_human_text_in_json(tmp_path):
    path=tmp_path/"contracts.json"
    assert run_cli(path,"add","one","Suporte","Empresa","2026-01-01","2026-11-20","12345").returncode==0
    before=path.read_bytes()
    result=run_cli(path,"export","--format","json","--as-of","2026-11-11","--status","due")
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)["contracts"][0]["amount_cents"]==12345
    result=run_cli(path,"export","--format","csv","--as-of","2026-11-11","--query","missing")
    assert result.returncode==0 and len(result.stdout.splitlines())==1
    assert run_cli(path,"export","--days","-1").returncode==2
    assert path.read_bytes()==before
