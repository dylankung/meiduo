# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-25 09:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_ordergoods_is_anonymous'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordergoods',
            name='is_commented',
            field=models.BooleanField(default=False, verbose_name='是否评价了'),
        ),
    ]