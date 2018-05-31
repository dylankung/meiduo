# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-03 10:12
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20180403_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='逻辑删除'),
        ),
        migrations.AlterField(
            model_name='address',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL, verbose_name='用户'),
        ),
    ]
