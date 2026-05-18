import os

# Supabase PostgreSQL Configuration
SUPABASE_DB_URL = os.getenv(
    'SUPABASE_DB_URL',
    'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'
)

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', True)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '632685261969-pak4g39l46krdnufu49h576eo5ainddl.apps.googleusercontent.com')

# Semaphore SMS Configuration
SEMAPHORE_API_KEY = os.getenv('SEMAPHORE_API_KEY', 'ed4e2a40f128550a21e44978605c171d')
SEMAPHORE_SENDER_NAME = os.getenv('SEMAPHORE_SENDER_NAME', 'SEMAPHORE')

# Supabase API Configuration (for Storage)
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://fydfsgjrlowrrtlmefwq.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZGZzZ2pybG93cnJ0bG1lZndxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwMjkwNTcsImV4cCI6MjA5MDYwNTA1N30.m94HHMC7852zw9xfkkOYTPY1IzoH_kNPLYpTe0myGB4')

# Firebase Cloud Messaging (FCM) - for push notifications
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY', 'BIb5YffHFeCD1_TYpNHpC5TOeZgML5MW8CIsaD-jExr1a5soJ598H7PPrdppR2JX2EvJhZc1CFBp7oF7BEwk-sU')

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
