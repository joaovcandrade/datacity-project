# Generated to revert manager group/secretary feature while preserving later changes.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_managergroup_user_grupo_gestor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='grupo_gestor',
        ),
        migrations.DeleteModel(
            name='ManagerGroup',
        ),
    ]
