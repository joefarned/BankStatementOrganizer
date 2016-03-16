import json
from collections import defaultdict
from pymongo import MongoClient
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from pava.api.twillio import Messaging
from pava.api.banking import PlaidData, BankingData

from pava.celeryapp import load_bank_data, load_bank_data_and_later

from .models import Account

def home(request):
    if request.user.is_authenticated():
        return redirect('/feed')

    return render(request, 'home.html', None)

def privacy(request):
    return render(request, 'privacy.html', None)

def terms(request):
    return render(request, 'terms.html', None)

@login_required
def feed(request):
    bank_data = BankingData()
    data = {
        'accounts': Account.objects.filter(user=request.user),
        'transactions': list(bank_data.all_transactions(request.user).sort([('predicted-interest', -1)]))
    }

    categorized_transactions = defaultdict(list)
    interest_sum = defaultdict(int)

    for transaction in data['transactions']:
        if not 'category' in  transaction:
            categorized_transactions['_'].append(transaction)
            interest_sum['_'] += transaction.get('predicted-interest', 0)
            continue

        category = tuple(transaction['category'])
        categorized_transactions[category].append(transaction)
        interest_sum[category] += transaction.get('predicted-interest', 0)

    data['categorized_transactions'] = categorized_transactions

    for category in interest_sum:
        interest_sum[category] /= len(categorized_transactions[category])

    sorted_categories = [(category, 0, categorized_transactions[category], interest_sum[category]) for category in interest_sum]


    had_geo = [
        transaction for transaction in data['transactions'] if 'longitude' in transaction
    ]

    data['geo_present'] = had_geo

    merchants = defaultdict(list)
    merchant_map = {}

    for transaction in data['transactions']:
        merchants[transaction.get('name')].append(transaction)
        merchant_map[transaction.get('name')] = transaction.get('name')

    most_merchants = [[merchant_map[entity], entity, merchants[entity]] for entity in merchants if len(merchants[entity]) > 5]

    for merch in most_merchants:
        sorted_categories.append((merch[0], 1, merch[2], sum([x.get('predicted-interest', 0) for x in merch[2]]) / len(merch[2]) ))

    sorted_categories.sort(key=lambda x: x[3])
    sorted_categories.reverse()
    data['categorized_transactions'] = sorted_categories

    return render(request, 'feed.html', data)

@login_required
def load_data(request):
    data = []

    for account in Account.objects.filter(user=request.user):
        load_bank_data_and_later.delay(account, False)

    return redirect('/feed')

@login_required
def accounts(request):
    data = {
        'accounts': request.user.account_set.all(),
        'institutions': PlaidData.institutions(),
    }

    return render(request, 'accounts.html', data)


def setup_for_new_account(account):
    load_bank_data_and_later.delay(account)

    # set up a couple later tasks to update
    num1 = datetime.utcnow() + timedelta(minutes=1)
    num2 = datetime.utcnow() + timedelta(minutes=5)
    num3 = datetime.utcnow() + timedelta(minutes=60)

    load_bank_data.apply_async((account,), eta=num1)
    load_bank_data.apply_async((account,), eta=num2)
    load_bank_data.apply_async((account,), eta=num3)

    print 'setup'

@login_required
def new_account(request):
    data = {

    }

    response_data = {}

    if request.POST.get('institution') and request.POST.get('user') and request.POST.get('pass') and request.POST.get('email'):
        plaid_response = PlaidData.initial_login(
            account_type=request.POST.get('institution'),
            username=request.POST.get('user'),
            password=request.POST.get('pass'),
            email=request.POST.get('email')
            )

        if 'access_token' in plaid_response:
            if 'mfa' in plaid_response:
                response_data['mfa'] = plaid_response['mfa']
                response_data['status'] = 'mfa'
                response_data['token'] = plaid_response['access_token']
                response_data['account_type'] = request.POST.get('institution')
            else:
                new_account = Account(
                    user=request.user,
                    bank_type=request.POST.get('institution'),
                    access_token=plaid_response['access_token'])
                new_account.save()
                setup_for_new_account(new_account)
                response_data['status'] = 'ok'

            import pprint
            pprint.pprint(plaid_response)
        else:
            response_data['status'] = 'fail'
            response_data['message'] = plaid_response['resolve']

    else:
        response_data['status'] = 'fail'

    return HttpResponse(json.dumps(response_data), content_type="application/json")

@login_required
def new_account_mfa(request):
    data = {

    }

    response_data = {}

    if request.POST.get('token') and request.POST.get('answer') and request.POST.get('account_type'):
        plaid_response = PlaidData.login_step(
            access_token=request.POST.get('token'),
            answer=request.POST.get('answer'),
            account_type=request.POST.get('account_type')
            )

        import pprint
        pprint.pprint(plaid_response)

        if 'access_token' in plaid_response:
            if 'mfa' in plaid_response:
                response_data['mfa'] = plaid_response['mfa']
                response_data['status'] = 'mfa'
            else:
                new_account = Account(
                    user=request.user,
                    bank_type=request.POST.get('account_type'),
                    access_token=plaid_response['access_token'])
                new_account.save()
                setup_for_new_account(new_account)

                response_data['status'] = 'ok'


        else:
            response_data['status'] = 'fail'
            response_data['message'] = plaid_response['resolve']

    else:
        response_data['status'] = 'fail'
        response_data['message'] = 'Some data is missing.'

    return HttpResponse(json.dumps(response_data), content_type="application/json")

