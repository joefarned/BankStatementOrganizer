from django.db import models
from django.conf import settings

from pava.api.banking import BankingData
bank_data = BankingData()

class Account(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    bank_type = models.CharField(max_length=50)
    access_token= models.TextField()
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = ('Account')
        verbose_name_plural = ('Accounts')

    def __unicode__(self):
        return self.access_token

    def sub_accounts(self):
        return bank_data.get_accounts(self)
