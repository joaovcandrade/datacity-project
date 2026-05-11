# Generated manually for platform goals/reference cities

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auditlog_action_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformGoalReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('gestor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='platform_goal_references', to=settings.AUTH_USER_MODEL)),
                ('municipio_referencia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='platform_goal_references', to='accounts.municipality')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goal_references', to='accounts.platform')),
            ],
            options={
                'verbose_name': 'Meta de referência da plataforma',
                'verbose_name_plural': 'Metas de referência das plataformas',
                'db_table': 'plataforma_meta_referencia',
            },
        ),
        migrations.AddConstraint(
            model_name='platformgoalreference',
            constraint=models.UniqueConstraint(fields=('platform', 'gestor'), name='uniq_meta_referencia_platform_gestor'),
        ),
    ]
