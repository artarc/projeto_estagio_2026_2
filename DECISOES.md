## Tema
Escolhi desenvolver um sistema de **solicitação e aluguel de equipamentos de TI**, com um fluxo simples: o usuário solicita os equipamentos e o gestor analisa, confirma ou cancela o pedido.

## Tecnologias
Utilizei **Django 5.2 LTS com Python 3.12**, aproveitando recursos nativos como autenticação, formulários, ORM, validações e proteção CSRF.
Optei por **Django Templates** para evitar um frontend separado e manter o projeto mais simples.
O banco escolhido foi o **SQLite**, suficiente para o escopo demonstrativo. Em um cenário maior, poderia ser substituído por PostgreSQL.

## Equipamentos e solicitações
Mantive os equipamentos previamente cadastrados e decidi não criar um CRUD completo, pois isso aumentaria o escopo sem necessidade.
As solicitações são criadas como **pendentes** e podem ser confirmadas, canceladas ou excluídas pelo painel.
Implementei regras para que somente solicitações confirmadas consumam estoque e para impedir confirmações quando não houver quantidade suficiente.
Também adaptei o sistema para permitir **vários equipamentos e diferentes quantidades em uma mesma solicitação**.

## Disponibilidade
Implementei a validação de conflitos de datas e disponibilidade de estoque.
O formulário verifica a disponibilidade automaticamente e, quando necessário, sugere uma nova data em que todos os equipamentos estarão disponíveis.
As validações principais também são refeitas no backend para garantir segurança e consistência.

## Interface e painel
Desenvolvi a interface com **HTML, CSS e JavaScript**, mantendo poucas dependências.
O painel possui busca, filtros, indicadores e adaptação para desktop e celular.
Também realizei ajustes de responsividade, posicionamento de elementos e experiência do usuário.

## Docker
Utilizei **Docker** para padronizar a execução do projeto, mantendo uma estrutura simples com um único serviço web e persistência do SQLite em volume.

##Cortes de escopo
Decidi não implementar cadastro completo de equipamentos, notificações por e-mail, recuperação de senha, níveis diferentes de permissão e paginação. Essas funcionalidades aumentariam o escopo sem contribuir diretamente para o fluxo principal avaliado no teste. Para o volume demonstrativo do projeto, a listagem atual e um único nível de acesso administrativo são suficientes.

## Uso de IA
O que deleguei para a IA
Utilizei o Codex para gerar a estrutura inicial do projeto Django e auxiliar na implementação dos models, formulários, views, templates, estilos e testes. Minha participação foi definir o tema e as regras de negócio, revisar o resultado, testar os fluxos e solicitar correções conforme os problemas encontrados.

Uma implementação ruim gerada pela IA
A primeira versão permitia solicitar apenas um equipamento e uma unidade por vez. Percebi que isso não representava uma solicitação real, pois uma pessoa pode precisar, por exemplo, de dois notebooks e um monitor. Por isso, alterei o fluxo para aceitar vários equipamentos e quantidades diferentes na mesma solicitação, incluindo a validação de estoque.

Uma decisão tomada contra a sugestão da IA
A IA adicionou textos explicativos e documentação mais extensa do que eu considerava necessário, incluindo uma instrução sobre o usuário do Django na tela de login. Decidi remover esses textos e simplificar o README para deixar a interface e a documentação mais diretas, mantendo somente as informações necessárias para entender e executar o projeto.
