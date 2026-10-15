import unittest
from store import Store
from cache import CachedStore
from api import rename_user, delete_user


def make():
    store = Store()
    store.write(1, {"name": "Ann"})
    store.write(2, {"name": "Bob"})
    return store, CachedStore(store)


class Accept(unittest.TestCase):
    def test_rename_visible_through_cache(self):
        store, c = make()
        c.get(1)
        rename_user(c, 1, "Anna")
        self.assertEqual(c.get(1)["name"], "Anna")

    def test_delete_visible_through_cache(self):
        store, c = make()
        c.get(1)
        delete_user(c, 1)
        self.assertIsNone(c.get(1))

    def test_cache_still_caches(self):
        store, c = make()
        c.get(1)
        c.get(1)
        c.get(1)
        self.assertEqual(store.reads, 1)

    def test_rename_does_not_evict_other_keys(self):
        store, c = make()
        c.get(1)
        c.get(2)
        before = store.reads
        rename_user(c, 1, "Anna")
        c.get(2)
        c.get(2)
        self.assertEqual(store.reads, before)

    def test_delete_does_not_evict_other_keys(self):
        store, c = make()
        c.get(1)
        c.get(2)
        before = store.reads
        delete_user(c, 1)
        c.get(2)
        self.assertEqual(store.reads, before)

    def test_rename_then_repeated_reads_hit_store_at_most_once(self):
        store, c = make()
        c.get(1)
        rename_user(c, 1, "Anna")
        before = store.reads
        c.get(1)
        c.get(1)
        self.assertLessEqual(store.reads - before, 1)


if __name__ == "__main__":
    unittest.main()
