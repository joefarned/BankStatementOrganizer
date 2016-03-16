# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20140913_1348'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='added',
            field=models.DateTimeField(default=datetime.date(2014, 9, 13), auto_now_add=True),
            preserve_default=False,
        ),
    ]
