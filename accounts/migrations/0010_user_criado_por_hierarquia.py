# Generated for manager hierarchy in DataCity
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_platformgoalreference_municipio_scope'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='criado_por',
            field=models.ForeignKey(
                blank=True,
                help_text='Usuário administrador ou gestor que criou esta conta.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='usuarios_criados',
                to='accounts.user'
            ),
        ),
    ]
