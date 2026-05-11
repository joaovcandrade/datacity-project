from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_user_criado_por_hierarquia'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManagerGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('ativo', models.BooleanField(db_index=True, default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('gestor_lider', models.ForeignKey(help_text='Gestor líder responsável pelo grupo/secretaria.', on_delete=django.db.models.deletion.CASCADE, related_name='grupos_liderados', to='accounts.user')),
                ('municipio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grupos_gestores', to='accounts.municipality')),
                ('indicadores', models.ManyToManyField(blank=True, help_text='Indicadores que os usuários do grupo poderão preencher.', related_name='grupos_gestores', to='accounts.indicator')),
            ],
            options={
                'verbose_name': 'Grupo/Secretaria',
                'verbose_name_plural': 'Grupos/Secretarias',
                'db_table': 'grupo_gestor',
                'ordering': ['nome'],
            },
        ),
        migrations.AddField(
            model_name='user',
            name='grupo_gestor',
            field=models.ForeignKey(blank=True, help_text='Grupo/secretaria ao qual o gestor subordinado pertence.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios', to='accounts.managergroup'),
        ),
        migrations.AddConstraint(
            model_name='managergroup',
            constraint=models.UniqueConstraint(fields=('gestor_lider', 'nome'), name='uniq_grupo_por_gestor_lider_nome'),
        ),
    ]
