import json
from twilio.rest import TwilioRestClient
from plaid import Client

class Messaging:
	fromNumber = "+16504698724"

	# Twilio variables
	account_sid = "ACa8d56d6b3d8cdd2bfb8ad30eea6b6d0f"
	auth_token = "35111cf01f884bc24a8e0b1de8649bc1"

	@classmethod
	def sendMessage(cls, message, toNumber):
		client = TwilioRestClient(cls.account_sid, cls.auth_token)
		message = client.messages.create(to=toNumber, from_=cls.fromNumber,
                                     body=message)

class PlaidData:
	client_id = '54137790d8675800005de8d2'
	secret = 'SKTzUuKXq2ZcxviiwW0fiJ'

	def __init__(self, username, password):
		self.client = Client(client_id=self.client_id, secret=self.secret)
		self.connect = self.client.connect(account_type='wells', username=username, password=password, email='joefarned@gmail.com')

	def getJSONResponse(self):
		json_response = json.loads(self.connect.content)
		import pprint
		pprint.pprint(json_response)
		message = "Your last transaction was @ " + json_response['transactions'][0]['name']
		Messaging.sendMessage(message, "+16508620978") 

objectData = PlaidData("joefarned3", "angela0816")
objectData.getJSONResponse()