import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASS

def test_real_email():
    print("--- STARTING REAL EMAIL TEST ---")
    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
    print(f"Using sender: {EMAIL_USER}")
    
    subject = "Autoride System: REAL SMTP TEST SUCCESS"
    body = "Hello! If you are reading this, it means your Autoride System is now successfully sending real emails via Gmail SMTP. --------"
    
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER  # Send it back to yourself for testing
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            
        print("\nSUCCESS! The email was sent successfully.")
        print("Please check your Gmail inbox (and Spam folder) for the test message.")
    except Exception as e:
        print(f"\nFAILED. Error: {str(e)}")
        print("\nTips:")
        print("1. Double check the 16-letter App Password.")
        print("2. Ensure 2-Step Verification is still ON.")

if __name__ == "__main__":
    test_real_email()
