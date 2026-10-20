CUST_HTML = 'AutorideSystem/customer_mobile/www/index.html'
CUST_JS = 'AutorideSystem/customer_mobile/www/js/app.js'

# 1. Update customer HTML
with open(CUST_HTML, 'r', encoding='utf-8') as f:
    html_content = f.read()

for i in range(6):
    old_tag = f'<input type="number" maxlength="1" id="otp{i}"'
    new_tag = f'<input type="tel" inputmode="numeric" pattern="[0-9]*" maxlength="1" id="otp{i}"'
    assert html_content.count(old_tag) == 1, f"Could not find unique {old_tag}"
    html_content = html_content.replace(old_tag, new_tag, 1)

with open(CUST_HTML, 'w', encoding='utf-8') as f:
    f.write(html_content)
print("Updated customer_mobile/www/index.html OTP inputs")

# 2. Update customer JS
with open(CUST_JS, 'r', encoding='utf-8') as f:
    js_content = f.read()

old_otp_fn = """// AUTH: OTP
function otpNext(el, nextIdx) {
  if (el.value.length >= 1 && nextIdx >= 0) {
    var next = document.getElementById('otp' + nextIdx);
    if (next) next.focus();
  }
}"""

new_otp_fn = """// AUTH: OTP
function otpNext(el, nextIdx) {
  if (el.value) {
    el.value = el.value.replace(/[^0-9]/g, '').slice(-1);
  }
  if (el.value.length >= 1 && nextIdx >= 0) {
    var next = document.getElementById('otp' + nextIdx);
    if (next) next.focus();
  }
}"""

assert js_content.count(old_otp_fn) == 1, "Could not find unique otpNext function in app.js"
js_content = js_content.replace(old_otp_fn, new_otp_fn, 1)

with open(CUST_JS, 'w', encoding='utf-8') as f:
    f.write(js_content)
print("Updated customer_mobile/www/js/app.js otpNext function")
