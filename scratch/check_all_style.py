with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos_style_open = text.find('<style>')
pos_style_close = text.find('</style>')
sub = text[pos_style_open:pos_style_close]
print(f"Total in <style>: opens={sub.count('{')}, closes={sub.count('}')}, diff={sub.count('{') - sub.count('}')}")
