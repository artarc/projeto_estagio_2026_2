import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Equipamento, ItemSolicitacao, SolicitacaoEmprestimo


class PaginaPublicaTests(TestCase):
    def setUp(self):
        self.equipamento = Equipamento.objects.create(
            nome="Notebook de teste",
            tipo="Notebook",
            identificacao="NB-TESTE",
            ativo=True,
        )
        self.monitor = Equipamento.objects.create(
            nome="Monitor de teste",
            tipo="Monitor",
            identificacao="MON-TESTE",
            ativo=True,
        )
        self.inativo = Equipamento.objects.create(
            nome="Monitor inativo",
            tipo="Monitor",
            identificacao="MON-INATIVO",
            ativo=False,
        )
        retirada = date.today() + timedelta(days=2)
        self.dados_validos = {
            "nome": "Ana Souza",
            "email": "ana@example.com",
            "equipamentos": [self.equipamento.pk, self.monitor.pk],
            f"quantidade_{self.equipamento.pk}": 2,
            f"quantidade_{self.monitor.pk}": 1,
            "data_retirada": retirada,
            "data_devolucao": retirada + timedelta(days=2),
            "finalidade": "Apresentação para um cliente.",
        }

    def test_lista_apenas_equipamentos_ativos(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, self.equipamento.nome)
        self.assertNotContains(response, self.inativo.nome)
        self.assertContains(response, "Disponível")

    def test_equipamento_tem_cinco_unidades_por_padrao(self):
        self.assertEqual(self.equipamento.quantidade_total, 5)

    def test_formulario_exibe_campos_na_ordem_do_fluxo(self):
        response = self.client.get(reverse("home"))
        conteudo = response.content.decode()

        posicoes = [
            conteudo.index('id="id_nome"'),
            conteudo.index('id="id_email"'),
            conteudo.index('class="equipment-picker form-field-wide"'),
            conteudo.index('id="id_data_retirada"'),
            conteudo.index('id="id_data_devolucao"'),
            conteudo.index('id="id_finalidade"'),
        ]
        self.assertEqual(posicoes, sorted(posicoes))

    def test_solicitacao_valida_nasce_pendente(self):
        dados = {**self.dados_validos, "status": "confirmado"}

        response = self.client.post(reverse("home"), dados)

        self.assertRedirects(response, f"{reverse('home')}#solicitar")
        solicitacao = SolicitacaoEmprestimo.objects.get()
        self.assertEqual(solicitacao.status, SolicitacaoEmprestimo.Status.PENDENTE)
        self.assertSetEqual(
            set(solicitacao.equipamentos.all()),
            {self.equipamento, self.monitor},
        )
        self.assertEqual(
            solicitacao.itens.get(equipamento=self.equipamento).quantidade,
            2,
        )
        self.assertEqual(
            solicitacao.itens.get(equipamento=self.monitor).quantidade,
            1,
        )

    def test_rejeita_devolucao_anterior_a_retirada(self):
        dados = {
            **self.dados_validos,
            "data_devolucao": self.dados_validos["data_retirada"] - timedelta(days=1),
        }

        response = self.client.post(reverse("home"), dados)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A devolução não pode ser anterior à retirada.")
        self.assertSetEqual(
            set(response.context["equipamentos_selecionados"]),
            {self.equipamento.pk, self.monitor.pk},
        )
        self.assertFalse(SolicitacaoEmprestimo.objects.exists())

    def test_rejeita_equipamento_inativo(self):
        dados = {
            **self.dados_validos,
            "equipamentos": [self.inativo.pk],
            f"quantidade_{self.equipamento.pk}": 0,
            f"quantidade_{self.monitor.pk}": 0,
            f"quantidade_{self.inativo.pk}": 1,
        }

        response = self.client.post(reverse("home"), dados)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SolicitacaoEmprestimo.objects.exists())

    def test_home_mantem_equipamento_sem_estoque_selecionavel(self):
        for indice in range(5):
            solicitacao = SolicitacaoEmprestimo.objects.create(
                nome=f"Pessoa {indice}",
                email=f"pessoa{indice}@example.com",
                data_retirada=self.dados_validos["data_retirada"],
                data_devolucao=self.dados_validos["data_devolucao"],
                finalidade="Trabalho temporário.",
                status=SolicitacaoEmprestimo.Status.CONFIRMADO,
            )
            solicitacao.equipamentos.add(self.equipamento)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Indisponível agora")
        self.assertContains(response, "is-currently-unavailable")
        self.assertNotContains(response, "disabled aria-disabled=\"true\"")

        dados = {
            **self.dados_validos,
            "equipamentos": [self.equipamento.pk],
            f"quantidade_{self.equipamento.pk}": 1,
            f"quantidade_{self.monitor.pk}": 0,
        }
        response = self.client.post(reverse("home"), dados)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Quantidade indisponível no período informado: Notebook de teste.",
        )
        self.assertContains(response, "A próxima janela comum é de")
        self.assertContains(response, "Usar estas datas")
        self.assertEqual(SolicitacaoEmprestimo.objects.count(), 5)

    def test_rejeita_quantidade_acima_do_estoque_total(self):
        dados = {
            **self.dados_validos,
            f"quantidade_{self.equipamento.pk}": 6,
            f"quantidade_{self.monitor.pk}": 0,
        }

        response = self.client.post(reverse("home"), dados)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "não pode ultrapassar 5")
        self.assertFalse(SolicitacaoEmprestimo.objects.exists())


class DisponibilidadeApiTests(TestCase):
    def setUp(self):
        self.notebook = Equipamento.objects.create(
            nome="Notebook API",
            tipo="Notebook",
            identificacao="NB-API",
            quantidade_total=5,
        )
        self.monitor = Equipamento.objects.create(
            nome="Monitor API",
            tipo="Monitor",
            identificacao="MON-API",
            quantidade_total=5,
        )
        self.inicio = date.today() + timedelta(days=5)

    def criar_reserva(self, equipamento, quantidade, fim):
        solicitacao = SolicitacaoEmprestimo.objects.create(
            nome="Reserva confirmada",
            email="reserva@example.com",
            data_retirada=self.inicio,
            data_devolucao=fim,
            finalidade="Reserva para teste.",
            status=SolicitacaoEmprestimo.Status.CONFIRMADO,
        )
        ItemSolicitacao.objects.create(
            solicitacao=solicitacao,
            equipamento=equipamento,
            quantidade=quantidade,
        )

    def consultar(self, itens, fim=None):
        return self.client.post(
            reverse("consultar_disponibilidade"),
            data=json.dumps(
                {
                    "data_retirada": self.inicio.isoformat(),
                    "data_devolucao": (fim or self.inicio + timedelta(days=1)).isoformat(),
                    "itens": itens,
                }
            ),
            content_type="application/json",
        )

    def test_consulta_considera_quantidade_reservada(self):
        self.criar_reserva(
            self.notebook,
            quantidade=3,
            fim=self.inicio + timedelta(days=2),
        )

        response = self.consultar(
            [{"equipamento_id": self.notebook.pk, "quantidade": 2}]
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["disponivel"])
        self.assertEqual(response.json()["itens"][0]["quantidade_disponivel"], 2)

    def test_retorna_proxima_janela_comum_preservando_duracao(self):
        self.criar_reserva(
            self.notebook,
            quantidade=4,
            fim=self.inicio + timedelta(days=2),
        )
        self.criar_reserva(
            self.monitor,
            quantidade=5,
            fim=self.inicio + timedelta(days=4),
        )

        response = self.consultar(
            [
                {"equipamento_id": self.notebook.pk, "quantidade": 2},
                {"equipamento_id": self.monitor.pk, "quantidade": 1},
            ]
        )

        dados = response.json()
        self.assertFalse(dados["disponivel"])
        self.assertEqual(
            dados["proxima_data_retirada"],
            (self.inicio + timedelta(days=5)).isoformat(),
        )
        self.assertEqual(
            dados["proxima_data_devolucao"],
            (self.inicio + timedelta(days=6)).isoformat(),
        )

    def test_quantidade_superior_ao_total_nao_tem_sugestao(self):
        response = self.consultar(
            [{"equipamento_id": self.notebook.pk, "quantidade": 6}]
        )

        dados = response.json()
        self.assertFalse(dados["disponivel"])
        self.assertIsNone(dados["proxima_data_retirada"])
        self.assertIsNone(dados["proxima_data_devolucao"])

    def test_consulta_aceita_apenas_post(self):
        response = self.client.get(reverse("consultar_disponibilidade"))

        self.assertEqual(response.status_code, 405)


class DashboardTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="gestor",
            password="SenhaSegura123!",
        )
        self.equipamento = Equipamento.objects.create(
            nome="Projetor",
            tipo="Audiovisual",
            identificacao="PROJ-TESTE",
        )
        self.solicitacao = SolicitacaoEmprestimo.objects.create(
            nome="Bruno Lima",
            email="bruno@example.com",
            data_retirada=date.today() + timedelta(days=3),
            data_devolucao=date.today() + timedelta(days=4),
            finalidade="Apresentação interna.",
        )
        self.solicitacao.equipamentos.add(self.equipamento)
        item = self.solicitacao.itens.get(equipamento=self.equipamento)
        item.quantidade = 2
        item.save(update_fields=["quantidade"])

    def test_dashboard_redireciona_visitante_para_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_autenticado_exibe_solicitacao(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bruno Lima")
        self.assertContains(response, "bruno@example.com")
        self.assertContains(response, "<b>5</b> de 5 disponíveis", html=True)
        self.assertContains(response, "× 2")
        self.assertContains(response, "Excluir")

    def test_confirmacao_abate_estoque_exibido_no_dashboard(self):
        self.client.force_login(self.usuario)

        self.client.post(
            reverse("confirmar_solicitacao", args=[self.solicitacao.pk])
        )
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "<b>3</b> de 5 disponíveis", html=True)
        equipamento = next(
            item
            for item in response.context["equipamentos"]
            if item.pk == self.equipamento.pk
        )
        self.assertEqual(equipamento.quantidade_disponivel, 3)

    def test_dashboard_filtra_por_status_e_pesquisa(self):
        self.client.force_login(self.usuario)
        response = self.client.get(
            reverse("dashboard"),
            {"q": "Projetor", "status": "pendente"},
        )

        self.assertContains(response, "Bruno Lima")
        self.assertEqual(list(response.context["solicitacoes"]), [self.solicitacao])

    def test_cancelamento_exige_login_e_altera_pendencia(self):
        url = reverse("cancelar_solicitacao", args=[self.solicitacao.pk])
        response = self.client.post(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        self.client.force_login(self.usuario)
        self.client.post(url)
        self.solicitacao.refresh_from_db()
        self.assertEqual(
            self.solicitacao.status,
            SolicitacaoEmprestimo.Status.CANCELADO,
        )

    def test_acao_preserva_filtros_do_dashboard(self):
        self.client.force_login(self.usuario)
        destino = f"{reverse('dashboard')}?q=Bruno&status=pendente"

        response = self.client.post(
            reverse("cancelar_solicitacao", args=[self.solicitacao.pk]),
            {"next": destino},
        )

        self.assertRedirects(response, destino)

    def test_exclusao_exige_login_e_aceita_apenas_post(self):
        url = reverse("excluir_solicitacao", args=[self.solicitacao.pk])

        response = self.client.post(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        self.client.force_login(self.usuario)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            SolicitacaoEmprestimo.objects.filter(pk=self.solicitacao.pk).exists()
        )

    def test_exclusao_confirmada_devolve_equipamento_ao_estoque(self):
        self.solicitacao.status = SolicitacaoEmprestimo.Status.CONFIRMADO
        self.solicitacao.save(update_fields=["status"])
        self.client.force_login(self.usuario)

        disponibilidade_antes = Equipamento.objects.com_disponibilidade().get(
            pk=self.equipamento.pk
        )
        self.assertEqual(disponibilidade_antes.quantidade_disponivel, 3)

        response = self.client.post(
            reverse("excluir_solicitacao", args=[self.solicitacao.pk]),
            follow=True,
        )

        self.assertFalse(
            SolicitacaoEmprestimo.objects.filter(pk=self.solicitacao.pk).exists()
        )
        equipamento = next(
            item
            for item in response.context["equipamentos"]
            if item.pk == self.equipamento.pk
        )
        self.assertEqual(equipamento.quantidade_disponivel, 5)
        self.assertContains(
            response,
            "Solicitação excluída. O estoque dos equipamentos foi atualizado.",
        )

    def test_exclusao_preserva_filtros_do_dashboard(self):
        self.client.force_login(self.usuario)
        destino = f"{reverse('dashboard')}?q=Bruno&status=pendente"

        response = self.client.post(
            reverse("excluir_solicitacao", args=[self.solicitacao.pk]),
            {"next": destino},
        )

        self.assertRedirects(response, destino)
        self.assertFalse(SolicitacaoEmprestimo.objects.exists())


class ConflitoEmprestimoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="gestor",
            password="SenhaSegura123!",
        )
        self.client.force_login(self.usuario)
        self.equipamento = Equipamento.objects.create(
            nome="Notebook Dell",
            tipo="Notebook",
            identificacao="NB-CONFLITO",
            quantidade_total=1,
        )
        self.monitor = Equipamento.objects.create(
            nome="Monitor",
            tipo="Monitor",
            identificacao="MON-CONFLITO",
        )
        self.inicio = date.today() + timedelta(days=10)

    def criar_solicitacao(
        self,
        inicio,
        fim,
        status="pendente",
        nome="Pessoa",
        equipamentos=None,
        quantidades=None,
    ):
        solicitacao = SolicitacaoEmprestimo.objects.create(
            nome=nome,
            email="pessoa@example.com",
            data_retirada=inicio,
            data_devolucao=fim,
            finalidade="Trabalho temporário.",
            status=status,
        )
        for equipamento in equipamentos or [self.equipamento]:
            ItemSolicitacao.objects.create(
                solicitacao=solicitacao,
                equipamento=equipamento,
                quantidade=(quantidades or {}).get(equipamento.pk, 1),
            )
        return solicitacao

    def test_nao_confirma_periodo_sobreposto_inclusive(self):
        self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=2),
            status=SolicitacaoEmprestimo.Status.CONFIRMADO,
            nome="Reserva existente",
        )
        conflitante = self.criar_solicitacao(
            self.inicio + timedelta(days=2),
            self.inicio + timedelta(days=4),
            nome="Reserva conflitante",
            equipamentos=[self.equipamento, self.monitor],
        )

        response = self.client.post(
            reverse("confirmar_solicitacao", args=[conflitante.pk]),
            follow=True,
        )

        conflitante.refresh_from_db()
        self.assertEqual(conflitante.status, SolicitacaoEmprestimo.Status.PENDENTE)
        self.assertContains(response, "não possuem unidades disponíveis nesse período")

    def test_confirma_varios_equipamentos_sem_conflito(self):
        nova = self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=2),
            equipamentos=[self.equipamento, self.monitor],
        )

        self.client.post(reverse("confirmar_solicitacao", args=[nova.pk]))

        nova.refresh_from_db()
        self.assertEqual(nova.status, SolicitacaoEmprestimo.Status.CONFIRMADO)
        self.assertSetEqual(
            set(nova.equipamentos.all()),
            {self.equipamento, self.monitor},
        )

    def test_solicitacao_pendente_nao_bloqueia_confirmacao(self):
        self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=2),
            nome="Outra pendência",
        )
        nova = self.criar_solicitacao(
            self.inicio + timedelta(days=1),
            self.inicio + timedelta(days=3),
            nome="Nova solicitação",
        )

        self.client.post(reverse("confirmar_solicitacao", args=[nova.pk]))

        nova.refresh_from_db()
        self.assertEqual(nova.status, SolicitacaoEmprestimo.Status.CONFIRMADO)

    def test_confirma_solicitacoes_ate_atingir_a_quantidade_total(self):
        equipamento = Equipamento.objects.create(
            nome="Headset",
            tipo="Periférico",
            identificacao="HEAD-ESTOQUE",
            quantidade_total=5,
        )
        for indice in range(4):
            self.criar_solicitacao(
                self.inicio,
                self.inicio + timedelta(days=2),
                status=SolicitacaoEmprestimo.Status.CONFIRMADO,
                nome=f"Reserva {indice}",
                equipamentos=[equipamento],
            )
        quinta = self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=2),
            nome="Quinta reserva",
            equipamentos=[equipamento],
        )

        self.client.post(reverse("confirmar_solicitacao", args=[quinta.pk]))

        quinta.refresh_from_db()
        self.assertEqual(quinta.status, SolicitacaoEmprestimo.Status.CONFIRMADO)

        sexta = self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=2),
            nome="Sexta reserva",
            equipamentos=[equipamento],
        )
        response = self.client.post(
            reverse("confirmar_solicitacao", args=[sexta.pk]),
            follow=True,
        )

        sexta.refresh_from_db()
        self.assertEqual(sexta.status, SolicitacaoEmprestimo.Status.PENDENTE)
        self.assertContains(response, "não possuem unidades disponíveis nesse período")

    def test_quantidade_solicitada_participa_do_conflito(self):
        equipamento = Equipamento.objects.create(
            nome="Notebook por lote",
            tipo="Notebook",
            identificacao="NB-LOTE",
            quantidade_total=5,
        )
        self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=2),
            status=SolicitacaoEmprestimo.Status.CONFIRMADO,
            nome="Reserva de quatro unidades",
            equipamentos=[equipamento],
            quantidades={equipamento.pk: 4},
        )
        lote = self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=2),
            nome="Pedido de duas unidades",
            equipamentos=[equipamento],
            quantidades={equipamento.pk: 2},
        )

        response = self.client.post(
            reverse("confirmar_solicitacao", args=[lote.pk]),
            follow=True,
        )

        lote.refresh_from_db()
        self.assertEqual(lote.status, SolicitacaoEmprestimo.Status.PENDENTE)
        self.assertContains(response, "não possuem unidades disponíveis nesse período")

    def test_reserva_com_devolucao_passada_libera_estoque_atual(self):
        equipamento = Equipamento.objects.create(
            nome="Kit de teste",
            tipo="Periférico",
            identificacao="KIT-LIBERADO",
            quantidade_total=1,
        )
        reserva_passada = SolicitacaoEmprestimo.objects.create(
            nome="Reserva encerrada",
            email="encerrada@example.com",
            data_retirada=date.today() - timedelta(days=3),
            data_devolucao=date.today() - timedelta(days=1),
            finalidade="Trabalho concluído.",
            status=SolicitacaoEmprestimo.Status.CONFIRMADO,
        )
        reserva_passada.equipamentos.add(equipamento)

        disponibilidade = Equipamento.objects.com_disponibilidade().get(
            pk=equipamento.pk
        )

        self.assertEqual(disponibilidade.quantidade_disponivel, 1)

    def test_acao_de_confirmar_aceita_apenas_post(self):
        solicitacao = self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=1),
        )

        response = self.client.get(
            reverse("confirmar_solicitacao", args=[solicitacao.pk])
        )

        self.assertEqual(response.status_code, 405)
