# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_visualization', '0003_path_uuid_data_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='path_uuid',
            name='data_type',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
