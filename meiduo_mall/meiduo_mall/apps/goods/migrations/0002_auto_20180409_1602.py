# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-09 08:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goodscategory',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='goods.GoodsCategory', verbose_name='父类别'),
        ),
    ]
