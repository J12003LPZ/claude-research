class Store:
    def __init__(self):
        self.data = {}
        self.reads = 0

    def read(self, key):
        self.reads += 1
        return self.data.get(key)

    def write(self, key, value):
        self.data[key] = value

    def remove(self, key):
        self.data.pop(key, None)
