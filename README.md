# Contratos e Prazos

Organização de contratos com destaque para vencimentos e renovações.

## Estado atual

MVP executável em branch de desenvolvimento, com testes automatizados. Consulta em memória de vencimentos dentro de uma janela configurável. Ainda não há notificações ou persistência.

## Tecnologias implementadas

Python 3.11+ e pytest.

## Escopo da primeira versão

- [ ] Cadastrar metadados de contratos
- [x] Consultar próximos vencimentos
- [ ] Registrar renovações

## Critérios para concluir a primeira versão

- [ ] Implementar o fluxo principal com validação de entradas e tratamento de erros.
- [ ] Documentar instalação, configuração e execução com comandos reproduzíveis.
- [ ] Adicionar exemplos de uso e dados fictícios.
- [ ] Verificar os casos principais e limites e registrar os resultados.

## Desenvolvimento

Execute na raiz do repositório:

```bash
python -m pip install pytest
pytest -q
```

O GitHub Actions executa a validação em pushes e pull requests. Este é um núcleo demonstrativo; as funcionalidades ainda marcadas como pendentes na lista acima continuam planejadas.

## Privacidade e configuração

Usar dados fictícios nos exemplos e manter senhas, tokens, arquivos pessoais e credenciais fora do controle de versão.

## Licença

Ainda não definida.
