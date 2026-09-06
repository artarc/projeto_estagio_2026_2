# Decisões do AssetFlow

## Tema

Empréstimos de equipamentos de TI representam bem o fluxo pedido: uma pessoa externa ao painel envia uma solicitação e uma pessoa gestora analisa. O tema permite demonstrar uma regra de negócio útil sem transformar o teste em um sistema de inventário.

## Django e Django Templates

O Django reúne formulários, validação, ORM, proteção CSRF e autenticação pronta em uma estrutura convencional. Isso reduz código próprio e deixa o fluxo fácil de explicar. Como limitação, a aplicação fica mais acoplada ao framework e não oferece uma API separada, algo desnecessário neste escopo.

Foi usada a série 5.2 por ser LTS e compatível com Python 3.12. Templates renderizados no servidor evitam um frontend separado e dependências de build.

## SQLite

O SQLite atende ao volume e à finalidade demonstrativa do teste, simplifica a instalação e permite executar tudo com um único processo. Ele não é a escolha indicada para alta concorrência; se o produto crescesse, a migração para um banco servidor seria reavaliada.

## Equipamentos previamente cadastrados

O AssetFlow possui apenas o model necessário para identificar e selecionar equipamentos. Não foi criado CRUD próprio, pois o catálogo é considerado responsabilidade de outro processo da empresa. Uma fixture reproduz o estado inicial para avaliação.

Uma solicitação pode reunir vários equipamentos com o mesmo período e finalidade. A relação muitos-para-muitos evita duplicar os dados da pessoa solicitante e mantém a análise do conjunto em uma única ação. A migration converte automaticamente o equipamento das solicitações antigas para essa nova relação.

Cada item do catálogo representa um tipo de equipamento e começa com cinco unidades. O painel exibe o total e a quantidade disponível usando os mesmos ícones da página pública. Uma solicitação confirmada consome uma unidade de cada equipamento selecionado; quando a data prevista de devolução fica no passado, a unidade volta automaticamente ao contador. Não foi criado um fluxo separado de devolução física para manter o escopo simples.

## Status e acesso ao painel

Toda solicitação pública nasce como `pendente`; o campo de status não faz parte do formulário. Confirmar e cancelar são ações via POST e protegidas por login e CSRF. Para manter as permissões simples, qualquer usuário autenticado acessa o painel; o README orienta criar um superusuário para a avaliação.

Confirmação e cancelamento são transições finais neste escopo. Reabrir solicitações exigiria novas regras e não foi incluído.

## Datas e conflito

Períodos são inclusivos: se uma reserva termina no dia em que outra começa, há conflito, pois o equipamento ainda está emprestado nessa data. A verificação usa a condição direta `início existente <= fim novo` e `fim existente >= início novo`.

Somente solicitações confirmadas consomem estoque. Pendências podem se sobrepor para que o gestor decida quais atender. A confirmação é permitida enquanto a quantidade de reservas sobrepostas for menor que o estoque total do equipamento. Quando uma solicitação possui vários equipamentos, a falta de estoque de qualquer um deles bloqueia a confirmação do conjunto inteiro; não há confirmação parcial. Em caso de indisponibilidade, a solicitação permanece pendente e uma mensagem explica o motivo. A retirada no formulário público também não pode estar no passado.

## Ordenação, filtros e estado vazio

A listagem é ordenada pela data de retirada e, em empate, pela criação. A busca cobre nome da pessoa e nome do equipamento; o filtro de status é propositalmente simples. Contadores e estado vazio foram incluídos para o painel continuar útil nos cenários comuns.

## Interface

A interface usa HTML semântico, CSS próprio e um pequeno JavaScript apenas para atualizar o estado e o contador da seleção múltipla. Os cards com ícones são os próprios checkboxes do formulário, evitando repetir o catálogo em outro controle. Um fragmento de template centraliza os ícones usados na home e no painel para manter os desenhos idênticos. O dashboard mantém tabela no desktop, lista os equipamentos de cada solicitação na mesma célula e transforma cada linha em um bloco rotulado no celular. Não foi adicionada biblioteca de componentes ou toolchain de frontend.

## Docker

O Docker padroniza a execução, mas mantém apenas um serviço web. O banco SQLite é persistido em um volume nomeado. Redis, Celery, Nginx e outros serviços não agregariam valor ao teste e aumentariam a explicação e manutenção.

## Cortes de escopo

Ficaram conscientemente fora: CRUD de equipamentos, movimentações manuais e histórico detalhado de estoque, fornecedores, clientes, notificações por e-mail, recuperação de senha personalizada, níveis complexos de permissão, API REST, integrações externas, relatórios avançados, multiempresa e atualização em tempo real.

## Uso de IA — preencher antes da entrega

Esta seção deve refletir sua experiência real. Substitua os campos abaixo antes de abrir o Pull Request; não mantenha exemplos inventados.

1. **O que deleguei para IA e o que fiz à mão:** [descreva aqui quais partes foram delegadas, quais você revisou ou produziu e por quê].
2. **Uma sugestão ou implementação ruim da IA:** [descreva o que estava errado, como você percebeu e o que fez no lugar].
3. **Uma decisão tomada contra a sugestão da IA:** [descreva a decisão e o motivo].
