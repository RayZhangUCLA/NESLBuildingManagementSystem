# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_visualization', '0002_auto_20150101_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='path_uuid',
            name='data_type',
            field=models.CharField(default=None, max_length=20),
            preserve_default=False,
        ),
    ]
