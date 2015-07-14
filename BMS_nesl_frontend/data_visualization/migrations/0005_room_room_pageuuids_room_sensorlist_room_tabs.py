# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_visualization', '0004_auto_20150329_2042'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('room_name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Room_PageUUIDs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Power', models.CharField(max_length=2000)),
                ('Water', models.CharField(max_length=2000)),
                ('Gas', models.CharField(max_length=2000)),
                ('Environment', models.TextField()),
                ('Motion', models.TextField()),
                ('room', models.ForeignKey(to='data_visualization.Room')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Room_Sensorlist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sensor_list_tree', models.TextField()),
                ('room', models.ForeignKey(to='data_visualization.Room')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Room_Tabs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tabs', models.CharField(max_length=1000)),
                ('room', models.ForeignKey(to='data_visualization.Room')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
