# Generated manually for audit action choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_designacaoindicador_designacaopreenchimento_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='acao',
            field=models.CharField(choices=[
                ('ANEXO_APAGADO', 'Anexo apagado'),
                ('VALOR_ALTERADO', 'Valor alterado'),
                ('INDICADOR_EDITADO', 'Indicador editado'),
                ('INDICADOR_DELETADO', 'Indicador deletado'),
                ('RECUPERACAO', 'Recuperação'),
                ('ANEXO_ENVIADO', 'Anexo enviado'),
                ('DESIGNACAO_CRIADA', 'Designação criada'),
                ('DESIGNACAO_CANCELADA', 'Designação cancelada'),
                ('PREENCHIMENTO_DESIGNADO', 'Preenchimento designado'),
            ], max_length=50),
        ),
    ]
