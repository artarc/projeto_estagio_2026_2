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

## Uso de IA
Eu desenvolvi todo o projeto com apoio do Codex. Primeiro, montei um prompt com as principais instruções e definições do serviço. Depois que a estrutura inicial foi gerada, fui revisando o código e os elementos implementados, removendo textos e funcionalidades desnecessárias adicionadas pela IA.
Na revisão, percebi que a lógica de aluguel de equipamentos precisava ser alterada, pois inicialmente só era possível solicitar um equipamento de um único tipo por vez. Fiz os ajustes necessários para deixar esse fluxo mais flexível.
Também implementei melhorias no visual do sistema e corrigi pequenos problemas de interface, como posicionamento de botões, alinhamentos e quebras de layout.