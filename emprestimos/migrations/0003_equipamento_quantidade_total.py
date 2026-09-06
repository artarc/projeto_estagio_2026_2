from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("emprestimos", "0002_solicitacao_multiplos_equipamentos"),
    ]

    operations = [
        migrations.AddField(
            model_name="equipamento",
            name="quantidade_total",
            field=models.PositiveIntegerField(default=5),
        ),
    ]
