from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import SolicitacaoEmprestimoForm
from .models import Equipamento, SolicitacaoEmprestimo


def home(request):
    equipamentos = list(
        Equipamento.objects.com_disponibilidade().filter(ativo=True).order_by("pk")
    )

    if request.method == "POST":
        form = SolicitacaoEmprestimoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Solicitação enviada com sucesso! A equipe responsável analisará o pedido.",
            )
            return redirect(f"{reverse('home')}#solicitar")
    else:
        form = SolicitacaoEmprestimoForm()

    equipamentos_selecionados = []
    if form.is_bound:
        equipamentos_selecionados = [
            int(equipamento_id)
            for equipamento_id in request.POST.getlist("equipamentos")
            if equipamento_id.isdigit()
        ]

    return render(
        request,
        "emprestimos/home.html",
        {
            "form": form,
            "equipamentos": equipamentos,
            "equipamentos_selecionados": equipamentos_selecionados,
            "tem_equipamentos_disponiveis": any(
                equipamento.quantidade_disponivel > 0
                for equipamento in equipamentos
            ),
        },
    )


@login_required
def dashboard(request):
    solicitacoes = SolicitacaoEmprestimo.objects.prefetch_related("equipamentos")
    equipamentos = Equipamento.objects.com_disponibilidade().filter(
        ativo=True
    ).order_by("pk")
    pesquisa = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    status_validos = {valor for valor, _ in SolicitacaoEmprestimo.Status.choices}

    if pesquisa:
        solicitacoes = solicitacoes.filter(
            Q(nome__icontains=pesquisa) | Q(equipamentos__nome__icontains=pesquisa)
        ).distinct()

    if status in status_validos:
        solicitacoes = solicitacoes.filter(status=status)
    else:
        status = ""

    contadores = {
        "pendentes": SolicitacaoEmprestimo.objects.filter(
            status=SolicitacaoEmprestimo.Status.PENDENTE
        ).count(),
        "confirmadas": SolicitacaoEmprestimo.objects.filter(
            status=SolicitacaoEmprestimo.Status.CONFIRMADO
        ).count(),
        "canceladas": SolicitacaoEmprestimo.objects.filter(
            status=SolicitacaoEmprestimo.Status.CANCELADO
        ).count(),
    }

    return render(
        request,
        "emprestimos/dashboard.html",
        {
            "solicitacoes": solicitacoes,
            "equipamentos": equipamentos,
            "contadores": contadores,
            "pesquisa": pesquisa,
            "status_selecionado": status,
            "status_opcoes": SolicitacaoEmprestimo.Status.choices,
        },
    )


@login_required
@require_POST
def confirmar_solicitacao(request, pk):
    with transaction.atomic():
        solicitacao = get_object_or_404(
            SolicitacaoEmprestimo.objects.select_for_update(),
            pk=pk,
        )
        # Mantém a verificação do estoque e a confirmação na mesma seção crítica.
        list(solicitacao.equipamentos.select_for_update())
        try:
            alterada = solicitacao.confirmar()
        except ValidationError:
            messages.error(
                request,
                "Não foi possível confirmar: um ou mais equipamentos não possuem unidades disponíveis nesse período.",
            )
        else:
            if alterada:
                messages.success(request, "Solicitação confirmada com sucesso.")
            else:
                messages.info(request, "A solicitação já foi analisada.")

    return _redirecionar_para_dashboard(request)


@login_required
@require_POST
def cancelar_solicitacao(request, pk):
    with transaction.atomic():
        solicitacao = get_object_or_404(
            SolicitacaoEmprestimo.objects.select_for_update(),
            pk=pk,
        )
        if solicitacao.cancelar():
            messages.success(request, "Solicitação cancelada com sucesso.")
        else:
            messages.info(request, "A solicitação já foi analisada.")

    return _redirecionar_para_dashboard(request)


@login_required
@require_POST
def excluir_solicitacao(request, pk):
    with transaction.atomic():
        solicitacao = get_object_or_404(
            SolicitacaoEmprestimo.objects.select_for_update(),
            pk=pk,
        )
        estava_confirmada = (
            solicitacao.status == SolicitacaoEmprestimo.Status.CONFIRMADO
        )
        if estava_confirmada:
            list(solicitacao.equipamentos.select_for_update())
        solicitacao.delete()

    if estava_confirmada:
        messages.success(
            request,
            "Solicitação excluída. O estoque dos equipamentos foi atualizado.",
        )
    else:
        messages.success(request, "Solicitação excluída com sucesso.")

    return _redirecionar_para_dashboard(request)


def _redirecionar_para_dashboard(request):
    destino = request.POST.get("next", "")
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(destino)
    return redirect("dashboard")
