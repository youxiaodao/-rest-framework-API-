# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-11-23 05:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20181123_1300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='balance',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='可提现和使用余额'),
        ),
    ]
