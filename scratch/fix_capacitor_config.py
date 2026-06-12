import json

with open('customer_mobile/capacitor.config.json', 'r') as f:
    config = json.load(f)

# Add googleapis.com to allowNavigation so Google Sign-In works
config['server']['allowNavigation'] = [
    'autoride-booking-system.vercel.app',
    '*.googleapis.com',
    '*.google.com',
    'accounts.google.com'
]

with open('customer_mobile/capacitor.config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('Updated allowNavigation in capacitor.config.json')
print(json.dumps(config['server'], indent=2))
