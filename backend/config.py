import os

# Supabase PostgreSQL Configuration - Using port 6543 (Transaction Mode Pooler)
SUPABASE_DB_URL = os.getenv(
    'SUPABASE_DB_URL',
    'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'
)

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', True)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', "857792394948-9m57q54s4638muf0ab5ihgakj4g44lje.apps.googleusercontent.com")
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', "")


# Supabase API Configuration (for Storage)
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://fydfsgjrlowrrtlmefwq.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZGZzZ2pybG93cnJ0bG1lZndxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwMjkwNTcsImV4cCI6MjA5MDYwNTA1N30.m94HHMC7852zw9xfkkOYTPY1IzoH_kNPLYpTe0myGB4')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZGZzZ2pybG93cnJ0bG1lZndxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTAyOTA1NywiZXhwIjoyMDkwNjA1MDU3fQ.mMZth_DpbilzCsDJhriyP6ZKb8pM5PSyhgLfgGA-5Ww')

# Firebase Cloud Messaging (FCM) - for push notifications
# Using a demo/test server key - replace with real one from Firebase Console for production
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY', 'AAAATMVnu0E:APA91bHQzQj5ExampleDemoKeyForTesting123456789')

# PayMongo Configuration
PAYMONGO_SECRET_KEY = os.getenv('PAYMONGO_SECRET_KEY', '')
PAYMONGO_PUBLIC_KEY = os.getenv('PAYMONGO_PUBLIC_KEY', '')
PAYMONGO_WEBHOOK_SECRET = os.getenv('PAYMONGO_WEBHOOK_SECRET', '')
APP_BASE_URL = os.getenv('APP_BASE_URL', 'https://autoride-booking-system.vercel.app')

# Email Configuration (SMTP)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = os.getenv('SMTP_PORT', 587)
EMAIL_USER = os.getenv('EMAIL_USER', 'patrickciarjohn@gmail.com')
EMAIL_PASS = os.getenv('EMAIL_PASS', 'lpif jsut hjzy cllw')

# Twilio Configuration (for SMS notifications)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token_here')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+15017122661')
