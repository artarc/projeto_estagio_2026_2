from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, F, IntegerField, Q, Value
from django.db.models.functions import Greatest


class EquipamentoQuerySet(models.QuerySet):
    def com_disponibilidade(self, data_referencia=None):
        data_referencia = data_referencia or date.today()
        return self.annotate(
            quantidade_reservada=Count(
                "solicitacoes",
                filter=Q(
                    solicitacoes__status=SolicitacaoEmprestimo.Status.CONFIRMADO,
                    solicitacoes__data_devolucao__gte=data_referencia,
                ),
                distinct=True,
            )
        ).annotate(
            quantidade_disponivel=Greatest(
                F("quantidade_total") - F("quantidade_reservada"),
                Value(0),
                output_field=IntegerField(),
            )
        )


class Equipamento(models.Model):
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=80)
    identificacao = models.CharField(max_length=40, unique=True)
    quantidade_total = models.PositiveIntegerField(default=5)
    ativo = models.BooleanField(default=True)

    objects = EquipamentoQuerySet.as_manager()

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
    equipamentos = models.ManyToManyField(
        Equipamento,
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

    def tem_conflito_confirmado(self):
        for equipamento in self.equipamentos.all():
            reservas_no_periodo = SolicitacaoEmprestimo.objects.filter(
                equipamentos=equipamento,
                status=self.Status.CONFIRMADO,
                data_retirada__lte=self.data_devolucao,
                data_devolucao__gte=self.data_retirada,
            ).exclude(pk=self.pk).count()

            if reservas_no_periodo >= equipamento.quantidade_total:
                return True

        return False

    def confirmar(self):
        if self.status != self.Status.PENDENTE:
            return False
        if self.tem_conflito_confirmado():
            raise ValidationError(
                "Um ou mais equipamentos não possuem unidades disponíveis nesse período."
            )
        self.status = self.Status.CONFIRMADO
        self.save(update_fields=["status"])
        return True

    def cancelar(self):
        if self.status != self.Status.PENDENTE:
            return False
        self.status = self.Status.CANCELADO
        self.save(update_fields=["status"])
        return True

    def __str__(self):
        if not self.pk:
            return self.nome
        nomes = ", ".join(self.equipamentos.values_list("nome", flat=True))
        return f"{self.nome} — {nomes}"
