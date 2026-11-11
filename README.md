# Contratos e Prazos

Gerenciador local em **Python 3.10+**, com cadastro, renovação e alertas de vencimento. O núcleo antigo (`Contrato` e `proximos_vencimentos`) permanece compatível.

## Funcionalidades implementadas nesta branch

- Cadastro e exclusão de contratos com identificação única.
- Validação de datas reais, valores em centavos, nomes e prazos.
- Registro de renovações, acrescentando dias ao vencimento anterior.
- Consulta de contratos vencidos, prestes a vencer e ativos.
- Pesquisa por nome, contraparte ou identificador.
- Resumo com totais, valores, renovações e próximo vencimento.
- Armazenamento local em JSON versionado, com escrita atômica.
- Testes de regras de negócio, persistência e comandos de terminal.

**Limitações:** não há alertas automáticos, envio de mensagens, armazenamento de PDFs ou autenticação individual. Não é um gestor jurídico completo.

## Instalar e testar

```bash
python -m pip install -e . pytest
pytest -q
```

## Exemplo de uso no terminal

Com dados **fictícios**:

```bash
python -m contratos_prazos.cli add DEMO-001 "Contrato de suporte" "Empresa Fictícia" 2026-11-01 2027-11-01 120000 --renewal-days 30
python -m contratos_prazos.cli list
python -m contratos_prazos.cli list --status due --days 90
python -m contratos_prazos.cli list --query suporte
python -m contratos_prazos.cli list --status due --as-of 2026-11-11
python -m contratos_prazos.cli summary --as-of 2026-11-11
python -m contratos_prazos.cli renew DEMO-001
python -m contratos_prazos.cli remove DEMO-001
```

O valor `120000` significa **R$ 1.200,00** em centavos. Datas usam `AAAA-MM-DD`. Os comandos `list` e `summary` aceitam `--as-of AAAA-MM-DD` para reproduzir a situação em uma data de referência, sem depender do relógio do computador. Sem `--as-of`, utilizam a data local do sistema. O intervalo de alerta `--days` deve estar entre 0 e 3650 mesmo quando não há contratos. Renovar adiciona o prazo informado ao vencimento anterior, independentemente da data de execução.

## Onde o registro fica

Por padrão, os dados são gravados em:

```text
~/.gx-contratos/contratos.json
```

Para escolher um caminho diferente, use a opção global `--data` **antes** do comando, ou a variável de ambiente `GX_CONTRACTS_FILE`. Exemplos:

```bash
python -m contratos_prazos.cli --data /tmp/contratos-demo.json summary
GX_CONTRACTS_FILE=/tmp/contratos-demo.json python -m contratos_prazos.cli list
```

Evite publicar arquivos JSON reais no GitHub: podem conter dados confidenciais de empresas ou clientes. O programa não criptografa os dados nem mantém backup automático.

## API para outros aplicativos

```python
from datetime import date
from contratos_prazos.records import ContractRecord, add_contract, registry_summary

item = ContractRecord(
    id="suporte-01",
    title="Suporte técnico",
    counterparty="Empresa fictícia",
    started_on=date(2026, 1, 1),
    expires_on=date(2026, 12, 31),
    amount_cents=25000,
)
registry = add_contract([], item)
print(registry_summary(registry, date(2026, 11, 7)))
```

As operações de cadastro e renovação retornam novas listas, sem modificar as anteriores.

## Licença

Ainda não definida.

## Exportar consultas

`export` usa os mesmos filtros de `list`, preserva o JSON original e escreve somente o relatório na saída padrão:

```bash
python -m contratos_prazos.cli export --format json --as-of 2026-11-11
python -m contratos_prazos.cli export --format csv --status due --days 90 --query suporte --as-of 2026-11-11 > consulta.csv
```

O JSON informa a data de referência, janela de alerta e situação de cada contrato. O CSV usa ponto e vírgula, valores inteiros em centavos e cabeçalho mesmo quando não há resultados. Textos que poderiam ser interpretados como fórmulas recebem apóstrofo no CSV; os valores armazenados e a exportação JSON permanecem originais.
