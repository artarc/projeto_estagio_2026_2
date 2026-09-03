from datetime import date

from django import forms

from .models import Equipamento, SolicitacaoEmprestimo


class SolicitacaoEmprestimoForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoEmprestimo
        fields = [
            "nome",
            "email",
            "equipamento",
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
        self.fields["equipamento"].queryset = Equipamento.objects.filter(
            ativo=True
        ).order_by("pk")
        self.fields["equipamento"].empty_label = "Selecione um equipamento"
        minimum_date = date.today().isoformat()
        self.fields["data_retirada"].widget.attrs["min"] = minimum_date
        self.fields["data_devolucao"].widget.attrs["min"] = minimum_date

        for field in self.fields.values():
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

    def clean(self):
        cleaned_data = super().clean()
        retirada = cleaned_data.get("data_retirada")
        devolucao = cleaned_data.get("data_devolucao")
        equipamento = cleaned_data.get("equipamento")

        if retirada and devolucao and devolucao < retirada:
            self.add_error(
                "data_devolucao",
                "A devolução não pode ser anterior à retirada.",
            )

        if equipamento and not equipamento.ativo:
            self.add_error(
                "equipamento",
                "Este equipamento não está disponível para solicitação.",
            )

        return cleaned_data
