from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import SolicitacaoEmprestimoForm
from .models import Equipamento, SolicitacaoEmprestimo


def home(request):
    equipamentos = Equipamento.objects.filter(ativo=True)

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

    return render(
        request,
        "emprestimos/home.html",
        {"form": form, "equipamentos": equipamentos},
    )


@login_required
def dashboard(request):
    solicitacoes = SolicitacaoEmprestimo.objects.select_related("equipamento")
    pesquisa = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    status_validos = {valor for valor, _ in SolicitacaoEmprestimo.Status.choices}

    if pesquisa:
        solicitacoes = solicitacoes.filter(
            Q(nome__icontains=pesquisa) | Q(equipamento__nome__icontains=pesquisa)
        )

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
            "contadores": contadores,
            "pesquisa": pesquisa,
            "status_selecionado": status,
            "status_opcoes": SolicitacaoEmprestimo.Status.choices,
        },
    )
