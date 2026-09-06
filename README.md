# AssetFlow

Aplicação web para solicitar e gerenciar empréstimos temporários de equipamentos de TI. O catálogo de equipamentos já existe no sistema; o foco do projeto é o fluxo entre o envio público da solicitação e a análise feita em um painel autenticado.

Projeto desenvolvido para o teste técnico de Estágio em Tecnologia — Desenvolvimento Full Stack da Mupi Systems.

## Funcionalidades

- página pública responsiva com catálogo de equipamentos ativos;
- formulário com seletor visual por ícones para um ou mais equipamentos, validação no backend e novas solicitações sempre como `pendente`;
- login e logout usando a autenticação nativa do Django;
- dashboard protegido com contadores de estoque e solicitações, listagem, busca e filtro por status;
- confirmação, cancelamento e exclusão de solicitações no painel;
- devolução imediata ao estoque quando uma solicitação confirmada é excluída;
- estoque inicial de cinco unidades por equipamento, reduzido por solicitações confirmadas e liberado após a devolução prevista;
- bloqueio da confirmação quando a quantidade disponível de qualquer equipamento solicitado se esgota no período;
- indicação visual de disponibilidade na página pública;
- estado vazio e feedback visual para ações e erros;
- fixture com seis equipamentos iniciais;
- execução local ou com Docker.

## Stack

- Python 3.12+
- Django 5.2 LTS
- Django Templates
- SQLite
- HTML, CSS e JavaScript sem frameworks adicionais
- Docker e Docker Compose (opcionais)

O Django 5.2 foi escolhido por ser uma versão LTS e suportar Python 3.12. O SQLite já faz parte do Python e atende ao escopo pequeno deste teste sem exigir outro serviço.

## Estrutura principal

```text
assetflow/                  configurações e URLs do projeto
emprestimos/                models, forms, views, URLs, testes e migrations
emprestimos/fixtures/       equipamentos iniciais
templates/                  templates públicos, de login e dashboard
static/                     CSS, JavaScript e imagem do projeto
Dockerfile                  imagem da aplicação
docker-compose.yml          execução com um único serviço web
DECISOES.md                 decisões técnicas e cortes de escopo
```

## Execução local

### 1. Pré-requisitos

- Python 3.12 ou superior
- Git

### 2. Clone e acesse o projeto

```bash
git clone https://github.com/artarc/projeto_estagio_2026_2.git
cd projeto_estagio_2026_2
```

### 3. Crie e ative o ambiente virtual

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instale as dependências

```bash
python -m pip install -r requirements.txt
```

### 5. Prepare o banco

```bash
python manage.py migrate
python manage.py loaddata equipamentos
```

O segundo comando carrega os equipamentos iniciais. Como eles representam um catálogo mantido por outro processo, não há CRUD próprio no AssetFlow.

### 6. Crie o usuário administrador

```bash
python manage.py createsuperuser
```

Informe usuário, e-mail e senha quando solicitado. Esse usuário será usado em `/login/`.

### 7. Execute

```bash
python manage.py runserver
```

Acesse [http://localhost:8000/](http://localhost:8000/).

## Execução com Docker

Pré-requisitos: Docker e Docker Compose.

```bash
docker compose up --build
```

As migrations e a fixture são aplicadas automaticamente na inicialização. O SQLite fica persistido no volume nomeado `assetflow_data`.

Em outro terminal, crie o administrador:

```bash
docker compose exec web python manage.py createsuperuser
```

Depois, acesse [http://localhost:8000/](http://localhost:8000/). Para encerrar, use `Ctrl+C` no terminal do Compose.

## Variáveis de ambiente

O projeto possui valores seguros apenas para desenvolvimento local. Para personalizar, copie `.env.example` e defina as variáveis no ambiente:

| Variável | Finalidade | Padrão local |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | chave interna do Django | valor inseguro de desenvolvimento |
| `DJANGO_DEBUG` | ativa o modo de depuração | `True` |
| `DJANGO_ALLOWED_HOSTS` | hosts separados por vírgula | `localhost,127.0.0.1` |
| `SQLITE_PATH` | caminho opcional do banco SQLite | `db.sqlite3` na raiz |

Não use os valores de desenvolvimento em produção.

## URLs principais

| URL | Acesso | Descrição |
| --- | --- | --- |
| `/` | público | apresentação, equipamentos e formulário |
| `/login/` | público | autenticação do gestor |
| `/dashboard/` | autenticado | gestão das solicitações |
| `/logout/` | autenticado, via POST | encerramento da sessão |
| `/django-admin/` | superusuário | administração nativa do Django |

## Como testar o fluxo

1. Carregue os equipamentos e crie um superusuário.
2. Acesse `/`, selecione dois ou mais equipamentos e envie uma única solicitação.
3. Confirme que o feedback de sucesso é exibido.
4. Em uma sessão anônima, acesse `/dashboard/` e confirme o redirecionamento para `/login/`.
5. Entre com o superusuário e confirme, cancele ou exclua uma solicitação. A exclusão de uma solicitação confirmada devolve seus equipamentos ao estoque.
6. Para validar o estoque, confirme solicitações sobrepostas até ocupar as cinco unidades de um equipamento. Uma sexta solicitação para o mesmo período continuará pendente por inteiro.
7. Teste a busca por nome/equipamento e o filtro por status.

## Testes automatizados

```bash
python manage.py test
```

Os testes cobrem seleção múltipla, formulário público, equipamentos inativos e indisponíveis, estoque, status inicial, autenticação obrigatória, dashboard, filtros, cancelamento, exclusão, restrição de método HTTP e conflitos de período.

## Decisões

As escolhas, ambiguidades e funcionalidades conscientemente deixadas de fora estão registradas em [DECISOES.md](DECISOES.md).
