# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-25 07:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_auto_20180423_2237'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordergoods',
            name='score',
            field=models.SmallIntegerField(default=5, verbose_name='满意度评分'),
        ),
    ]
