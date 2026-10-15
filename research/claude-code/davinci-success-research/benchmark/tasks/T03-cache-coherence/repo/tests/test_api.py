import unittest
from store import Store
from cache import CachedStore
from api import rename_user


class ApiTests(unittest.TestCase):
    def test_rename_returns_updated_user(self):
        store = Store()
        store.write(1, {"name": "Ann"})
        cached = CachedStore(store)
        self.assertEqual(rename_user(cached, 1, "Anna"), {"name": "Anna"})


if __name__ == "__main__":
    unittest.main()
