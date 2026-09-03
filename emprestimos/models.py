from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Equipamento(models.Model):
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=80)
    identificacao = models.CharField(max_length=40, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["tipo", "nome"]
        verbose_name = "equipamento"
        verbose_name_plural = "equipamentos"

    def __str__(self):
        return f"{self.nome} ({self.identificacao})"


class SolicitacaoEmprestimo(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFIRMADO = "confirmado", "Confirmado"
        CANCELADO = "cancelado", "Cancelado"

    nome = models.CharField(max_length=120)
    email = models.EmailField()
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="solicitacoes",
    )
    data_retirada = models.DateField()
    data_devolucao = models.DateField("data prevista de devolução")
    finalidade = models.TextField(max_length=500)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data_retirada", "criado_em"]
        verbose_name = "solicitação de empréstimo"
        verbose_name_plural = "solicitações de empréstimo"
        constraints = [
            models.CheckConstraint(
                condition=Q(data_devolucao__gte=models.F("data_retirada")),
                name="devolucao_igual_ou_apos_retirada",
            )
        ]

    def clean(self):
        super().clean()
        if (
            self.data_retirada
            and self.data_devolucao
            and self.data_devolucao < self.data_retirada
        ):
            raise ValidationError(
                {"data_devolucao": "A devolução não pode ser anterior à retirada."}
            )

    def __str__(self):
        return f"{self.nome} — {self.equipamento.nome}"

