# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_visualization', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu_tree',
            name='tree',
            field=models.TextField(),
            preserve_default=True,
        ),
    ]
