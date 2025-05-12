import os
from dotenv import load_dotenv
from twilio.rest import Client
'''
load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

message = client.messages.create(
    from_=os.getenv("TWILIO_MY_NUMBER"),
    body='Click here for match stats: https://www.leagueofgraphs.com/match/NA/5284768552',
    to=os.getenv("TWILIO_VIRTUAL_NUMBER"))

'''
def send_message(from_, to, message, account_sid, auth_token):
    Client(account_sid, auth_token).messages.create(
        from_=from_,
        to=to,
        body=message
    )
