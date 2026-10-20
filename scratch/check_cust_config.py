try:
    with open('customer_mobile/www/config.js', 'r', encoding='utf-8') as f:
        print("customer_mobile config.js:\n", f.read())
except Exception as e:
    print("Error:", e)
