# Contratos e Prazos

Núcleo Python 3.10+ para controlar datas de vencimento e registrar renovações contratuais de forma imutável, sem alterar os contratos anteriores.

## Funcionalidades

- `proximos_vencimentos(contratos, hoje, dias=30)`: lista contratos que vencem dentro da janela de 0 a 3.650 dias, ordenados por data e nome.
- `renovar_contrato(contrato, novo_vencimento, registrada_em)`: cria **novo objeto** com vencimento atualizado e evento de renovação no histórico.
- Registra data anterior, nova data e data de registro. Rejeita renovação sem aumento do prazo, histórico inconsistente e datas de registro anteriores ao último evento.

## Exemplo

```python
from datetime import date
from contratos_prazos import Contrato, renovar_contrato, proximos_vencimentos

original = Contrato("Serviço fictício", date(2026, 11, 30))
renovado = renovar_contrato(original, date(2027, 11, 30), date(2026, 11, 3))
print(original.vencimento)           # 2026-11-30
print(renovado.vencimento)           # 2027-11-30
print(renovado.renovacoes)           # Histórico imutável
```

## Testar

```bash
python -m pip install -e . pytest
pytest -q
```

O GitHub Actions executa os testes automaticamente. A suíte verifica inclusão de renovação, imutabilidade, ordem do histórico, rejeição de dados inválidos e vencimentos.

## Limites

Biblioteca em memória sem API, autenticação, arquivos, banco de dados, notificações ou integração com assinatura digital. A renovação é um registro de domínio, **não** efetiva juridicamente a renovação de um contrato. Não inclua dados pessoais nos exemplos.

Licença: ainda não definida.
