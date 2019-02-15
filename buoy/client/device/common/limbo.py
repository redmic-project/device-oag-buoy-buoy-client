
class Limbo(object):
    def __init__(self):
        self.items = dict()

    def add(self, id, item):
        self.items[id] = item

    def clear(self):
        self.items.clear()

    def get(self, id):
        if self.exists(id):
            return self.items[id]
        return None

    def pop(self, id):
        item = self.get(id)
        if item:
            del self.items[id]
        return item

    def size(self):
        return len(self.items)

    def exists(self, id):
        return id in self.items
