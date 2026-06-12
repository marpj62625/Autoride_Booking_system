import re

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    js = f.read()

# Replace light green and purple with Grab Green
js = js.replace('#34d399', '#00b14f')
js = js.replace('#a78bfa', '#00b14f')

# Let's also check if there is any other place doing inline color like color:#34d399 or ackground:#a78bfa
# The simple string replacement above will catch them all.

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(js)

print("Updated JS colors successfully")
