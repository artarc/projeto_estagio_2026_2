import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import SolicitacaoEmprestimoForm
from .models import Equipamento, SolicitacaoEmprestimo
from .services import encontrar_proxima_janela, verificar_disponibilidade


def home(request):
    equipamentos = list(
        Equipamento.objects.com_disponibilidade().filter(ativo=True).order_by("pk")
    )

    if request.method == "POST":
        form = SolicitacaoEmprestimoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(
                request,
                "Solicitação enviada com sucesso! A equipe responsável analisará o pedido.",
            )
            return redirect(f"{reverse('home')}#solicitar")
    else:
        form = SolicitacaoEmprestimoForm()

    equipamentos_selecionados = []
    for equipamento in equipamentos:
        try:
            quantidade = int(
                form.data.get(f"quantidade_{equipamento.pk}", 0) or 0
            )
        except (TypeError, ValueError):
            quantidade = 0
        equipamento.quantidade_solicitada = max(quantidade, 0)
        if equipamento.quantidade_solicitada:
            equipamentos_selecionados.append(equipamento.pk)

    return render(
        request,
        "emprestimos/home.html",
        {
            "form": form,
            "equipamentos": equipamentos,
            "equipamentos_selecionados": equipamentos_selecionados,
            "tem_equipamentos_disponiveis": bool(equipamentos),
            "proxima_janela": getattr(form, "proxima_janela", None),
        },
    )


@require_POST
def consultar_disponibilidade(request):
    try:
        dados = json.loads(request.body)
        data_retirada = date.fromisoformat(dados["data_retirada"])
        data_devolucao = date.fromisoformat(dados["data_devolucao"])
        itens_recebidos = dados.get("itens", [])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse(
            {"erro": "Informe um período e quantidades válidas."},
            status=400,
        )

    if data_retirada < date.today() or data_devolucao < data_retirada:
        return JsonResponse(
            {"erro": "O período informado não é válido."},
            status=400,
        )

    quantidades = {}
    try:
        for item in itens_recebidos:
            equipamento_id = int(item["equipamento_id"])
            quantidade = int(item["quantidade"])
            if quantidade < 1:
                raise ValueError
            quantidades[equipamento_id] = (
                quantidades.get(equipamento_id, 0) + quantidade
            )
    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {"erro": "As quantidades informadas não são válidas."},
            status=400,
        )

    if not quantidades:
        return JsonResponse({"disponivel": True, "itens": []})

    equipamentos = Equipamento.objects.filter(
        pk__in=quantidades,
        ativo=True,
    ).in_bulk()
    if len(equipamentos) != len(quantidades):
        return JsonResponse(
            {"erro": "Um dos equipamentos não está disponível para solicitação."},
            status=400,
        )

    itens = [
        (equipamentos[equipamento_id], quantidade)
        for equipamento_id, quantidade in quantidades.items()
    ]
    resultado = verificar_disponibilidade(
        itens,
        data_retirada,
        data_devolucao,
    )
    proxima_janela = None
    if not resultado["disponivel"]:
        proxima_janela = encontrar_proxima_janela(
            itens,
            data_retirada,
            data_devolucao,
        )

    resposta = {
        "disponivel": resultado["disponivel"],
        "itens": [
            {
                "equipamento_id": item["equipamento"].pk,
                "nome": item["equipamento"].nome,
                "quantidade_solicitada": item["quantidade_solicitada"],
                "quantidade_disponivel": item["quantidade_disponivel"],
                "disponivel": item["disponivel"],
            }
            for item in resultado["itens"]
        ],
        "proxima_data_retirada": (
            proxima_janela[0].isoformat() if proxima_janela else None
        ),
        "proxima_data_devolucao": (
            proxima_janela[1].isoformat() if proxima_janela else None
        ),
    }
    return JsonResponse(resposta)


@login_required
def dashboard(request):
    solicitacoes = SolicitacaoEmprestimo.objects.prefetch_related(
        "itens__equipamento"
    )
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
