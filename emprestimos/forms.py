from datetime import date

from django import forms

from .models import Equipamento, ItemSolicitacao, SolicitacaoEmprestimo
from .services import encontrar_proxima_janela, verificar_disponibilidade


class SolicitacaoEmprestimoForm(forms.ModelForm):
    equipamentos = forms.ModelMultipleChoiceField(
        queryset=Equipamento.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label="Equipamentos",
        error_messages={
            "required": "Selecione ao menos uma unidade de um equipamento.",
            "invalid_choice": "Um dos equipamentos selecionados não está disponível para solicitação.",
        },
    )

    class Meta:
        model = SolicitacaoEmprestimo
        fields = [
            "nome",
            "email",
            "data_retirada",
            "data_devolucao",
            "finalidade",
        ]
        widgets = {
            "nome": forms.TextInput(
                attrs={"placeholder": "Digite seu nome completo", "autocomplete": "name"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "seu.email@empresa.com", "autocomplete": "email"}
            ),
            "data_retirada": forms.DateInput(attrs={"type": "date"}),
            "data_devolucao": forms.DateInput(attrs={"type": "date"}),
            "finalidade": forms.Textarea(
                attrs={
                    "placeholder": "Descreva a finalidade do empréstimo",
                    "rows": 4,
                }
            ),
        }
        labels = {
            "nome": "Nome completo",
            "email": "E-mail",
            "data_retirada": "Data de retirada",
            "data_devolucao": "Data prevista de devolução",
            "finalidade": "Finalidade do empréstimo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        equipamentos = Equipamento.objects.filter(ativo=True).order_by("pk")
        self.fields["equipamentos"].queryset = equipamentos

        if self.is_bound:
            dados = self.data.copy()
            equipamentos_selecionados = []
            for equipamento in equipamentos:
                try:
                    quantidade = int(
                        dados.get(f"quantidade_{equipamento.pk}", 0) or 0
                    )
                except (TypeError, ValueError):
                    quantidade = 0
                if quantidade > 0:
                    equipamentos_selecionados.append(str(equipamento.pk))
            dados.setlist("equipamentos", equipamentos_selecionados)
            self.data = dados

        minimum_date = date.today().isoformat()
        self.fields["data_retirada"].widget.attrs["min"] = minimum_date
        self.fields["data_devolucao"].widget.attrs["min"] = minimum_date

        for field_name, field in self.fields.items():
            if field_name == "equipamentos":
                continue
            field.widget.attrs["class"] = "form-control"

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        if len(nome) < 3:
            raise forms.ValidationError("Informe seu nome completo.")
        return nome

    def clean_data_retirada(self):
        data_retirada = self.cleaned_data["data_retirada"]
        if data_retirada < date.today():
            raise forms.ValidationError("A retirada não pode estar no passado.")
        return data_retirada

    def clean_equipamentos(self):
        equipamentos = self.cleaned_data["equipamentos"]
        itens_solicitados = []

        for equipamento in equipamentos:
            try:
                quantidade = int(
                    self.data.get(f"quantidade_{equipamento.pk}", 0) or 0
                )
            except (TypeError, ValueError):
                raise forms.ValidationError(
                    f"Informe uma quantidade válida para {equipamento.nome}."
                )

            if quantidade < 1:
                raise forms.ValidationError(
                    f"Informe ao menos uma unidade de {equipamento.nome}."
                )
            if quantidade > equipamento.quantidade_total:
                raise forms.ValidationError(
                    f"A quantidade de {equipamento.nome} não pode ultrapassar "
                    f"{equipamento.quantidade_total}."
                )
            itens_solicitados.append((equipamento, quantidade))

        self.itens_solicitados = itens_solicitados
        return equipamentos

    def clean(self):
        cleaned_data = super().clean()
        retirada = cleaned_data.get("data_retirada")
        devolucao = cleaned_data.get("data_devolucao")
        equipamentos = cleaned_data.get("equipamentos")

        if retirada and devolucao and devolucao < retirada:
            self.add_error(
                "data_devolucao",
                "A devolução não pode ser anterior à retirada.",
            )

        if equipamentos and equipamentos.filter(ativo=False).exists():
            self.add_error(
                "equipamentos",
                "Um dos equipamentos selecionados não está disponível para solicitação.",
            )

        itens_solicitados = getattr(self, "itens_solicitados", [])
        if retirada and devolucao and retirada <= devolucao and itens_solicitados:
            resultado = verificar_disponibilidade(
                itens_solicitados,
                retirada,
                devolucao,
            )
            if not resultado["disponivel"]:
                indisponiveis = ", ".join(
                    item["equipamento"].nome
                    for item in resultado["itens"]
                    if not item["disponivel"]
                )
                self.proxima_janela = encontrar_proxima_janela(
                    itens_solicitados,
                    retirada,
                    devolucao,
                )
                self.add_error(
                    "equipamentos",
                    f"Quantidade indisponível no período informado: {indisponiveis}.",
                )

        return cleaned_data

    def save(self, commit=True):
        solicitacao = super().save(commit=commit)
        if commit:
            ItemSolicitacao.objects.bulk_create(
                [
                    ItemSolicitacao(
                        solicitacao=solicitacao,
                        equipamento=equipamento,
                        quantidade=quantidade,
                    )
                    for equipamento, quantidade in self.itens_solicitados
                ]
            )
        return solicitacao
