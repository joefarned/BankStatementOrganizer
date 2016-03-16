from __future__ import absolute_import

import os
from datetime import datetime, timedelta

from celery import Celery
from django.conf import settings

from pava.api.banking import PlaidData
from pava.api.ml import ML

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pava.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Dev')

from configurations import importer
importer.install()

app = Celery('pava')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task(bind=True)
def load_all_bank_data(self, user):
    print 'load data 1'
    for account in user.account_set.all():
        new_data = PlaidData.import_into_database(user, account, account.access_token)

    return True

@app.task(bind=True)
def load_bank_data(self, account):
    print 'load data 1'
    new_data = PlaidData.import_into_database(account.user, account, account.access_token)
    return True

@app.task(bind=True)
def load_bank_data_and_later(self, account, recurring=True):
    print 'load data 2'
    if recurring:
        tomorrow = datetime.utcnow() + timedelta(days=1)
        load_bank_data_and_later.apply_async((account,), eta=tomorrow)

    user = account.user
    PlaidData.import_into_database(user, account, account.access_token)

    ml = ML()
    ml.run_ml_hardcoded(user.id)

    return True
