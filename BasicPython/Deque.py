
from collections import deque

class BrowserHistory:
    def __init__(self, max_size=5):
        self.history = deque(maxlen=max_size)
        self.forward_stack = deque()

    def add_page(self, url):
        self.history.append(url)
        self.forward_stack.clear()  # Clear forward stack on new navigation
        print(f"Visited: {url}")
        self.print_state()

    def go_back(self):
        if len(self.history) > 1:
            last_page = self.history.pop()
            self.forward_stack.append(last_page)
            print(f"Back: {last_page}")
        else:
            print("Cannot go back, only one page in history.")
        self.print_state()

    def go_forward(self):
        if self.forward_stack:
            page = self.forward_stack.pop()
            self.history.append(page)
            print(f"Forward: {page}")
        else:
            print("No forward history.")
        self.print_state()

    def print_state(self):
        print(f"Current History: {list(self.history)}")
        print(f"Forward Stack: {list(self.forward_stack)}")
        print("-" * 40)


bh = BrowserHistory()

bh.add_page("google.com")
bh.add_page("masaischool.com")
bh.add_page("github.com")
bh.add_page("stackoverflow.com")
bh.add_page("wikipedia.org")
bh.add_page("python.org")

bh.go_back()
bh.go_back()

bh.go_forward()
bh.add_page("reddit.com")

bh.go_back()
bh.go_forward()
