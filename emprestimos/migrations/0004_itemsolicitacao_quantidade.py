from django.db import migrations, models
import django.db.models.deletion


def copiar_itens_existentes(apps, schema_editor):
    Solicitacao = apps.get_model("emprestimos", "SolicitacaoEmprestimo")
    ItemSolicitacao = apps.get_model("emprestimos", "ItemSolicitacao")

    for solicitacao in Solicitacao.objects.prefetch_related("equipamentos"):
        ItemSolicitacao.objects.bulk_create(
            [
                ItemSolicitacao(
                    solicitacao_id=solicitacao.pk,
                    equipamento_id=equipamento.pk,
                    quantidade=1,
                )
                for equipamento in solicitacao.equipamentos.all()
            ]
        )


def restaurar_relacoes_existentes(apps, schema_editor):
    Solicitacao = apps.get_model("emprestimos", "SolicitacaoEmprestimo")
    ItemSolicitacao = apps.get_model("emprestimos", "ItemSolicitacao")

    for item in ItemSolicitacao.objects.all():
        solicitacao = Solicitacao.objects.get(pk=item.solicitacao_id)
        solicitacao.equipamentos.add(item.equipamento_id)


class Migration(migrations.Migration):
    dependencies = [
        ("emprestimos", "0003_equipamento_quantidade_total"),
    ]

    operations = [
        migrations.CreateModel(
            name="ItemSolicitacao",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantidade", models.PositiveIntegerField(default=1)),
                (
                    "equipamento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="itens_solicitacao",
                        to="emprestimos.equipamento",
                    ),
                ),
                (
                    "solicitacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens",
                        to="emprestimos.solicitacaoemprestimo",
                    ),
                ),
            ],
            options={
                "verbose_name": "item da solicitação",
                "verbose_name_plural": "itens da solicitação",
                "ordering": ["equipamento_id"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("solicitacao", "equipamento"),
                        name="item_unico_por_solicitacao_e_equipamento",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("quantidade__gte", 1)),
                        name="quantidade_item_maior_que_zero",
                    ),
                ],
            },
        ),
        migrations.RunPython(
            copiar_itens_existentes,
            restaurar_relacoes_existentes,
        ),
        migrations.RemoveField(
            model_name="solicitacaoemprestimo",
            name="equipamentos",
        ),
        migrations.AddField(
            model_name="solicitacaoemprestimo",
            name="equipamentos",
            field=models.ManyToManyField(
                related_name="solicitacoes",
                through="emprestimos.ItemSolicitacao",
                to="emprestimos.equipamento",
            ),
        ),
    ]
