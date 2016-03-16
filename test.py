# Download the twilio-python library from http://twilio.com/docs/libraries
from twilio.rest import TwilioRestClient
 
# Find these values at https://twilio.com/user/account
account_sid = "ACa8d56d6b3d8cdd2bfb8ad30eea6b6d0f"
auth_token = "35111cf01f884bc24a8e0b1de8649bc1"
client = TwilioRestClient(account_sid, auth_token)
 
message = client.messages.create(to="+16508620978", from_="+16504698724",
                                     body="Hello there!")