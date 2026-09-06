from django.db import migrations, models


def copiar_equipamentos_existentes(apps, schema_editor):
    Solicitacao = apps.get_model("emprestimos", "SolicitacaoEmprestimo")
    for solicitacao in Solicitacao.objects.exclude(equipamento_legado=None):
        solicitacao.equipamentos.add(solicitacao.equipamento_legado_id)


def restaurar_equipamento_legado(apps, schema_editor):
    Solicitacao = apps.get_model("emprestimos", "SolicitacaoEmprestimo")
    for solicitacao in Solicitacao.objects.prefetch_related("equipamentos"):
        equipamento = solicitacao.equipamentos.first()
        if equipamento:
            solicitacao.equipamento_legado_id = equipamento.pk
            solicitacao.save(update_fields=["equipamento_legado"])


class Migration(migrations.Migration):
    dependencies = [
        ("emprestimos", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="solicitacaoemprestimo",
            old_name="equipamento",
            new_name="equipamento_legado",
        ),
        migrations.AlterField(
            model_name="solicitacaoemprestimo",
            name="equipamento_legado",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name="+",
                to="emprestimos.equipamento",
            ),
        ),
        migrations.AddField(
            model_name="solicitacaoemprestimo",
            name="equipamentos",
            field=models.ManyToManyField(
                related_name="solicitacoes",
                to="emprestimos.equipamento",
            ),
        ),
        migrations.RunPython(
            copiar_equipamentos_existentes,
            restaurar_equipamento_legado,
        ),
        migrations.RemoveField(
            model_name="solicitacaoemprestimo",
            name="equipamento_legado",
        ),
    ]
