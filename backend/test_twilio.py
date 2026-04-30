import os
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

def test_twilio():
    try:
        print(f"Testing Twilio with SID: {TWILIO_ACCOUNT_SID[:5]}...")
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Testing with YOUR phone number
        to_number = "+639384592953" 
        
        message = client.messages.create(
            body="Autoride Twilio Test: Kung nababasa mo ito, working na ang SMS!",
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        
        print(f"SUCCESS! Message SID: {message.sid}")
    except Exception as e:
        print(f"FAILED! Error Details: {str(e)}")

if __name__ == "__main__":
    test_twilio()
