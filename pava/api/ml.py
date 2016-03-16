from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime
import numpy as np
from sklearn import linear_model
from sklearn.linear_model import SGDClassifier
import requests
from math import radians, cos, sin, asin, sqrt
import json


class ML(object):

    def __init__(self):
        super(ML, self).__init__()

        self.connection = MongoClient()
        self.db = self.connection['pava']

    	self.accounts = self.db['accounts']
        self.transactions = self.db['transactions']

    def run_ml_hardcoded(self, user_id):
        category_array = [[900, 100, 2, 4817.327312168776], [800, 100, 3, 660.6844291494644], [7.34, 0, 3, 660.6844291494644], [4.5, 100, 2, 663.9404169926431], [15, 100, 2, 661.0620842859299], [40, 100, 4, 4817.327312168776], [13, 100, 127, 662.3765181386126], [8.4, 2, 1, 660.6844291494644], [8.4, 156, 157, 660.6844291494644], [9.2, 2, 4, 663.9404169926431], [7.34, 100, 9, 660.6819125804176], [7.34, 3, 6, 660.6819125804176], [6.99, 100, 7, 661.3093923878442], [7.08, 2, 5, 661.3093923878442], [17, 8, 13, 661.3093923878442]]
        rating_list = [90, 90, 25, 20, 30, 35, 25, 25, 25, 25, 25, 25, 25, 25, 30]

        crf = self.build_prediction_model(category_array, rating_list)

        categorized_transactions = self.categorize(user_id)
        for category in categorized_transactions.keys():
            transaction_list = categorized_transactions.get(category)
            category_array = self.translate(transaction_list)

            i = 0
            for t in category_array:
                print transaction_list[i]['_id'], crf.predict(category_array[i])[0]
                self.transactions.update({'_id': transaction_list[i]['_id']},
                    {'$set':
                        {'predicted-interest': crf.predict(category_array[i])[0]}
                    }
                )
                i += 1

    def run_machine_learning(self, user_id):
        categorized_transactions = self.categorize(user_id)
        for category in categorized_transactions.keys():
            # Every value that is mapped to a key (ie category name)
            transaction_list = categorized_transactions.get(category)

            category_array = self.translate(transaction_list)
            rating_list = self.build_rating_list(transaction_list)

            print category_array
            print rating_list

            crf = self.build_prediction_model(category_array, rating_list)

            i = 0
            for t in category_array:
                self.transactions.update({'_id': transaction_list[i]['_id']},
                    {'$set':
                        {'predicted-interest': crf.predict(category_array[i])[0]}
                    }
                )
                i += 1
            print crf


    # Categoizes our database informations into a default dict
    def categorize(self, user_id):
        category_list = ['Arts and Entertainment', 'Bank Fees',
            'Cash Advance', 'Community', 'Food and Drink', 'Interest',
            'Parks and Outdoors', 'Paycheck', 'Payment', 'Professional',
            'Service', 'Shops', 'Tax', 'Transfer', 'Travel']

        all_transactions = self.transactions.find({'_user_id': user_id})

        # List that maps transaction categories to transactions
        # This is what we return
        categorized_transactions = defaultdict(list)

        # Add everything to categorized_transactions
        for transaction in all_transactions:
            if not 'category' in  transaction:
                continue
            category = transaction['category'][0]
            categorized_transactions[category].append(transaction)

        return categorized_transactions

    def build_rating_list(self, transaction_list):
        rating_list = [0] * len(transaction_list)

        i = 0
        for t in transaction_list:
            rating_list[i] = transaction_list[i]['real-interest']
            i += 1

        return rating_list

    def translate(self, transaction_list):
        # Init array
        category_array = []
        for x in range(0, len(transaction_list)):
            category_array.append([])
            for y in range(0, 4):
                category_array[x].append(0)

        # Price
        i = 0
        for c0 in category_array:
            c0[0] = transaction_list[i]['amount']
            i += 1

        # Days since last occurence
        i = 0
        for c1 in category_array:
            d1 = datetime.strptime(transaction_list[i]['date'], "%Y-%m-%d")
            j = i - 1
            while (j >= 0 and transaction_list[j]['name'] != transaction_list[i]['name']):
                j -= 1
            if (j > 0):
                d2 = datetime.strptime(transaction_list[j]['date'], "%Y-%m-%d")
                c1[1] = abs((d2 - d1).days)
            else:
                c1[1] = 100
            i += 1

        # Days since transaction occurred
        i = 0
        for c2 in category_array:
            d = datetime.today().strftime("%Y-%m-%d")
            d1 = datetime.strptime(d, "%Y-%m-%d")
            d2 = datetime.strptime(transaction_list[i]['date'], "%Y-%m-%d")
            c2[2] = abs((d2 - d1).days)
            i += 1
        i = 0

        # Location averaging
        totalLat = 0.0
        totalLng = 0.0
        totalPoints = 0
        lat = [0.0] * len(transaction_list)
        lng = [0.0] * len(transaction_list)
        i = 0
        for c4 in category_array:
            if 'location' not in transaction_list[i]['meta'] or 'city' not in transaction_list[i]['meta']['location']:
                continue
            request = requests.get("https://api.foursquare.com/v2/venues/search?client_id=2XO4NMYCUJDCKAP5SCZWLM5DERAJBWNNCB5EOBEMH2YVBIGA&client_secret=DQGH02IV0T24ZZHYTK5ZM305XWDEOFZD1SEEURVUDVIKS0VX&v=20130815&limit=1&query=" + transaction_list[i]['name'] + "&near=" + transaction_list[i]['meta']['location']['city'])
            data = json.loads(request.text)

            # Make sure Foursquare gives us a response
            if 'response' in data and 'venues' in data['response'] and len(data['response']['venues']) > 0:
                lat[i] = data['response']['venues'][0]['location']['lat']
                lng[i] = data['response']['venues'][0]['location']['lng']
                totalLat += lat[i]
                totalLng += lng[i]
                totalPoints += 1

            self.transactions.update({'_id': transaction_list[i]['_id']},
                {'$set': {'latitude': lat[i], 'longitude': lng[i]}})

            i += 1

        if i != 0:
            # Not totally accurate with longitude and latitude
            averageLat = totalLat / i
            averageLng = totalLng / i
        else:
            averageLat = averageLng = 0

        # Find the from the average point
        i = 0
        for c4 in category_array:
            c4[3] = self.haversine(averageLng, averageLat, lng[i], lat[i])
            i += 1

        return category_array

    def build_prediction_model(self, category_list, rating_list):
        # Training dataset, list of all the transactions we are using
        X = np.array(category_list)
        Y = np.array(rating_list)

        clf = SGDClassifier(loss='log', penalty='l2').fit(X, Y)

        return clf

    def haversine(self, lon1, lat1, lon2, lat2):
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        miles = 3956 * c
        return miles
