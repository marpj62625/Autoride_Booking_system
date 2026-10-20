from html.parser import HTMLParser

class ParentFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.modal_parents = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_id = attrs_dict.get('id', '')
        tag_class = attrs_dict.get('class', '')
        self.stack.append((tag, tag_id, tag_class))
        if tag_id == 'desktopCameraModal':
            self.modal_parents = list(self.stack[:-1])

    def handle_endtag(self, tag):
        if tag in ['img', 'input', 'br', 'hr', 'meta', 'link']:
            return
        # Pop matching tag from stack
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

parser = ParentFinder()
parser.feed(html)

print("Parents of desktopCameraModal:")
if parser.modal_parents:
    for p in parser.modal_parents:
        print(p)
else:
    print("Not found or no parents")
