# AssetFlow

Sistema desenvolvido para o teste técnico de Estágio Full Stack da Mupi Systems. Permite solicitar empréstimos de equipamentos de TI e gerenciar os pedidos em um painel autenticado.

## Funcionalidades

- solicitação pública de um ou mais equipamentos, com quantidade por item;
- consulta de disponibilidade por período e sugestão de novas datas;
- painel protegido por login, com busca e filtro por status;
- confirmação, cancelamento e exclusão de solicitações;
- atualização automática do estoque ao confirmar, cancelar ou excluir pedidos;
- interface responsiva para desktop e celular.
## Stack

- Python 3.12+
- Django 5.2 LTS
- Django Templates
- SQLite
- HTML, CSS e JavaScript
- Docker e Docker Compose

## Requisitos

- Python 3.12 ou superior;
- Git;
- Docker, apenas se optar pela execução em contêiner.

## Execução local

```bash
git clone https://github.com/artarc/projeto_estagio_2026_2.git
cd projeto_estagio_2026_2
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux ou macOS
source .venv/bin/activate
```

Instale e prepare o projeto:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata equipamentos
python manage.py createsuperuser
python manage.py runserver
```

A aplicação estará disponível em [http://localhost:8000/](http://localhost:8000/).

## Execução com Docker

```bash
docker compose up --build
```

As migrations e os equipamentos iniciais são carregados automaticamente. Para criar o administrador:

```bash
docker compose exec web python manage.py createsuperuser
```

O banco SQLite fica persistido no volume `assetflow_data`.

## URLs

| URL | Descrição |
| --- | --- |
| `/` | página pública e formulário |
| `/login/` | login administrativo |
| `/dashboard/` | gerenciamento das solicitações |
| `/logout/` | encerramento da sessão |

## Teste rápido

1. Envie uma solicitação pela página pública.
2. Entre em `/login/` com o administrador criado.
3. Confirme ou cancele o pedido no painel.
4. Verifique a atualização do status e do estoque.

## Testes automatizados

```bash
python manage.py test
```

As principais decisões técnicas e os cortes de escopo estão em [DECISOES.md](DECISOES.md).
