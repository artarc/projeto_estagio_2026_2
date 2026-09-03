## Resumo

Implementa o AssetFlow, uma aplicação Django para solicitação pública e gerenciamento autenticado de empréstimos de equipamentos de TI.

## Funcionalidades entregues

- formulário público com validações no backend e feedback visual;
- catálogo inicial de equipamentos carregado por fixture;
- autenticação, logout e proteção de acesso direto ao dashboard;
- contadores, tabela responsiva, busca, filtro e estado vazio;
- confirmação e cancelamento de solicitações pendentes;
- bloqueio de períodos confirmados conflitantes para o mesmo equipamento;
- testes automatizados, Docker e documentação de execução.

## Além do mínimo

Foram adicionados o controle de conflito, os filtros, os contadores e a seleção visual integrada entre catálogo e formulário. Esses pontos tornam o fluxo administrativo utilizável sem ampliar o domínio do produto.

## Decisões e cortes de escopo

O projeto mantém SQLite, Django Templates e um único serviço Docker. Não foram implementados CRUD de equipamentos, inventário completo, notificações, permissões complexas, API separada, multiempresa ou infraestrutura adicional. Os motivos estão detalhados em `DECISOES.md`.

## Principais dificuldades

<!-- Preencha antes de abrir o PR com dificuldades reais encontradas e como foram tratadas. -->

## Como executar

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata equipamentos
python manage.py createsuperuser
python manage.py runserver
```

Também é possível usar `docker compose up --build`. Consulte o `README.md` para o passo a passo completo e os testes.

