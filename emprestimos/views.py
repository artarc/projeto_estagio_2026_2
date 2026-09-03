from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import SolicitacaoEmprestimoForm
from .models import Equipamento


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

