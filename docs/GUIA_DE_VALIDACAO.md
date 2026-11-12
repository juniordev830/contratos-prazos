# Desenvolvimento e validação — Contratos e Prazos

## Estado implementado

CLI Python para controle local de contratos, vencimentos e renovação com JSON.

## Estrutura relevante

`src/contratos_prazos/records.py`, `core.py`, `storage.py`, `cli.py` e `tests/`.

## Como reproduzir verificações

`python -m pip install -e . pytest` e `pytest -q`; exemplos no README usam `python -m contratos_prazos.cli`.

Os exemplos devem usar entradas fictícias. Registrar explicitamente o que foi de fato executado no ambiente e comparar com o CI.

## Regressão prioritária

Validar prazo de renovação, vencimentos em ano bissexto, data invertida, número de centavos inválido, arquivo JSON truncado e duplicidade de ID.

## Próximos limites a resolver

O JSON é local e não criptografado. Planejar backup, auditoria e controle de acesso antes de armazenar contratos reais.

## Revisão de contribuição

- [ ] Mudança melhora uma regra, teste ou integração real.
- [ ] Cenários de entrada, saída e erro estão documentados.
- [ ] Nada de dados pessoais, credenciais ou arquivos gerados versionados.
- [ ] PR separado antes de alterar a principal.
