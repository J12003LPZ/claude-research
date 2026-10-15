class CachedStore:
    def __init__(self, store):
        self.store = store
        self._cache = {}

    def get(self, key):
        if key not in self._cache:
            self._cache[key] = self.store.read(key)
        return self._cache[key]

    def put(self, key, value):
        self.store.write(key, value)
        self._cache[key] = value

    def invalidate(self, key):
        self._cache.pop(key, None)
