class OrderedSet:
    def __init__(self):
        self.items = []
        self.seen = set()

    def add(self, item):
        if item not in self.seen:
            self.items.append(item)
            self.seen.add(item)

    def remove(self, item):
        if item in self.seen:
            self.items.remove(item)
            self.seen.remove(item)

    def get_index(self, item):
        return self.items.index(item)

    def clear(self):
        self.items.clear()
        self.seen.clear()

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __repr__(self):
        return f"{self.items}"
