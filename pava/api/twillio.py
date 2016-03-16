from twilio.rest import TwilioRestClient

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