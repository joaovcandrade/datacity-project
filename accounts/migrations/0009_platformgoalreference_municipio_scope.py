from django.db import migrations, models
import django.db.models.deletion


def migrate_goal_reference_to_city_scope(apps, schema_editor):
    PlatformGoalReference = apps.get_model('accounts', 'PlatformGoalReference')
    User = apps.get_model('accounts', 'User')

    for ref in PlatformGoalReference.objects.all():
        if ref.municipio_id:
            continue
        municipio_id = None
        if ref.gestor_id:
            try:
                gestor = User.objects.get(id=ref.gestor_id)
                municipio_id = gestor.municipio_id
            except User.DoesNotExist:
                municipio_id = None
        if municipio_id:
            ref.municipio_id = municipio_id
            ref.save(update_fields=['municipio'])

    seen = set()
    for ref in PlatformGoalReference.objects.exclude(municipio_id__isnull=True).order_by('platform_id', 'municipio_id', 'id'):
        key = (ref.platform_id, ref.municipio_id)
        if key in seen:
            ref.delete()
        else:
            seen.add(key)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_indicator_value_decimal'),
    ]

    operations = [
        migrations.AddField(
            model_name='platformgoalreference',
            name='municipio',
            field=models.ForeignKey(
                blank=True,
                help_text='Município para o qual a meta vale. A referência é compartilhada por todos os gestores desse município.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='platform_goal_references_definidas',
                to='accounts.municipality',
            ),
        ),
        migrations.AlterField(
            model_name='platformgoalreference',
            name='gestor',
            field=models.ForeignKey(
                blank=True,
                help_text='Usuário que definiu ou atualizou a meta.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='platform_goal_references',
                to='accounts.user',
            ),
        ),
        migrations.RunPython(migrate_goal_reference_to_city_scope, reverse_noop),
        migrations.RemoveConstraint(
            model_name='platformgoalreference',
            name='uniq_meta_referencia_platform_gestor',
        ),
        migrations.AddConstraint(
            model_name='platformgoalreference',
            constraint=models.UniqueConstraint(fields=('platform', 'municipio'), name='uniq_meta_referencia_platform_municipio'),
        ),
    ]
