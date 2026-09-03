from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Equipamento, SolicitacaoEmprestimo


class PaginaPublicaTests(TestCase):
    def setUp(self):
        self.equipamento = Equipamento.objects.create(
            nome="Notebook de teste",
            tipo="Notebook",
            identificacao="NB-TESTE",
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
            "equipamento": self.equipamento.pk,
            "data_retirada": retirada,
            "data_devolucao": retirada + timedelta(days=2),
            "finalidade": "Apresentação para um cliente.",
        }

    def test_lista_apenas_equipamentos_ativos(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, self.equipamento.nome)
        self.assertNotContains(response, self.inativo.nome)

    def test_solicitacao_valida_nasce_pendente(self):
        dados = {**self.dados_validos, "status": "confirmado"}

        response = self.client.post(reverse("home"), dados)

        self.assertRedirects(response, f"{reverse('home')}#solicitar")
        solicitacao = SolicitacaoEmprestimo.objects.get()
        self.assertEqual(solicitacao.status, SolicitacaoEmprestimo.Status.PENDENTE)

    def test_rejeita_devolucao_anterior_a_retirada(self):
        dados = {
            **self.dados_validos,
            "data_devolucao": self.dados_validos["data_retirada"] - timedelta(days=1),
        }

        response = self.client.post(reverse("home"), dados)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A devolução não pode ser anterior à retirada.")
        self.assertFalse(SolicitacaoEmprestimo.objects.exists())

    def test_rejeita_equipamento_inativo(self):
        dados = {**self.dados_validos, "equipamento": self.inativo.pk}

        response = self.client.post(reverse("home"), dados)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SolicitacaoEmprestimo.objects.exists())


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
            equipamento=self.equipamento,
            data_retirada=date.today() + timedelta(days=3),
            data_devolucao=date.today() + timedelta(days=4),
            finalidade="Apresentação interna.",
        )

    def test_dashboard_redireciona_visitante_para_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_autenticado_exibe_solicitacao(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bruno Lima")
        self.assertContains(response, "bruno@example.com")

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
        )
        self.inicio = date.today() + timedelta(days=10)

    def criar_solicitacao(self, inicio, fim, status="pendente", nome="Pessoa"):
        return SolicitacaoEmprestimo.objects.create(
            nome=nome,
            email="pessoa@example.com",
            equipamento=self.equipamento,
            data_retirada=inicio,
            data_devolucao=fim,
            finalidade="Trabalho temporário.",
            status=status,
        )

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
        )

        response = self.client.post(
            reverse("confirmar_solicitacao", args=[conflitante.pk]),
            follow=True,
        )

        conflitante.refresh_from_db()
        self.assertEqual(conflitante.status, SolicitacaoEmprestimo.Status.PENDENTE)
        self.assertContains(response, "já está reservado nesse período")

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

    def test_acao_de_confirmar_aceita_apenas_post(self):
        solicitacao = self.criar_solicitacao(
            self.inicio,
            self.inicio + timedelta(days=1),
        )

        response = self.client.get(
            reverse("confirmar_solicitacao", args=[solicitacao.pk])
        )

        self.assertEqual(response.status_code, 405)
