import json
import os.path

from plaid import Client
from pymongo import MongoClient

class PlaidData:
    client_id = '54137790d8675800005de8d2'
    secret = 'SKTzUuKXq2ZcxviiwW0fiJ'
    _institutions = None

    @classmethod
    def getData(self, account_type, username, password, email):
        client = Client(client_id=self.client_id, secret=self.secret)
        connect = client.connect(account_type=account_type, username=username, password=password, email=email)

        json_response = json.loads(connect.content)
        return json_response

    @classmethod
    def initial_login(self, account_type, username, password, email):
        client = Client(client_id=self.client_id, secret=self.secret)
        connect = client.connect(account_type=account_type, username=username, password=password, email=email)

        json_response = json.loads(connect.content)
        return json_response

    @classmethod
    def login_step(self, access_token, answer, account_type):
        client = Client(client_id=self.client_id, secret=self.secret)
        client.set_access_token(access_token)
        step = client.step(account_type=account_type, mfa=answer)

        return json.loads(step.content)

    @classmethod
    def import_into_database(self, user, sub_account, access_token):
        # data = PlaidData.getData('wells', "joefarned3", "angela0816", 'joefarned@gmail.com')
        client = Client(client_id=self.client_id, secret=self.secret)
        client.set_access_token(access_token)
        connect = client.transactions()
        data = json.loads(connect.content)

        c = MongoClient()
        db = c['pava']

        accounts = db['accounts']
        transactions = db['transactions']

        for account in data['accounts']:
            account['_user_id'] = user.id
            account['_user_account'] = sub_account.id
            if not accounts.find({'_id': account['_id']}).count():
                print accounts.insert(account)
            else:
                accounts.update({'_id': account['_id']}, account)

        for transaction in data['transactions']:
            transaction['_user_id'] = user.id
            if not transactions.find({'_id': transaction['_id']}).count():
                print transactions.insert(transaction)

        return data

    @classmethod
    def _load_institutions(self):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'institutions.json')
        with open(path) as f:
            return json.load(f)

    @classmethod
    def institutions(self):
        if not self._institutions:
            self._institutions = self._load_institutions()

        return self._institutions

class BankingData:
    def __init__(self):
        self.c = MongoClient()
        self.db = self.c['pava']

        self.accounts = self.db['accounts']
        self.transactions = self.db['transactions']


    def all_transactions(self, user):
        return self.transactions.find({'_user_id': user.id})

    def get_accounts(self, sub_account):
        return self.accounts.find({'_user_account': sub_account.id})
