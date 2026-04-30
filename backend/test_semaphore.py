import requests
from config import SEMAPHORE_API_KEY, SEMAPHORE_SENDER_NAME

def test_semaphore():
    try:
        print(f"Testing Semaphore with API Key: {SEMAPHORE_API_KEY[:5]}...")
        
        # Testing with YOUR phone number
        to_number = "09384592953" 
        
        response = requests.post("https://api.semaphore.co/api/v4/messages", data={
            'apikey': SEMAPHORE_API_KEY,
            'number': to_number,
            'message': 'Autoride Semaphore Test: Success na tayo!',
            'sendername': SEMAPHORE_SENDER_NAME
        })
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS! Check your phone.")
        else:
            print("FAILED! Check the error above.")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_semaphore()
