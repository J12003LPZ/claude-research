import unittest
from pager import paginate


class Accept(unittest.TestCase):
    def test_partial_last_page(self):
        self.assertEqual(paginate([1, 2, 3, 4, 5], 2, 3), [4, 5])

    def test_single_item_last_page(self):
        self.assertEqual(paginate(list(range(7)), 3, 3), [6])

    def test_past_the_end_is_empty(self):
        self.assertEqual(paginate([1, 2, 3], 5, 3), [])

    def test_empty_input(self):
        self.assertEqual(paginate([], 1, 3), [])

    def test_full_pages_unchanged(self):
        self.assertEqual(paginate([1, 2, 3, 4, 5, 6], 2, 3), [4, 5, 6])

    def test_page_below_one_raises(self):
        with self.assertRaises(ValueError):
            paginate([1], 0, 3)

    def test_per_page_below_one_raises(self):
        with self.assertRaises(ValueError):
            paginate([1], 1, 0)

    def test_input_not_mutated(self):
        data = [1, 2, 3, 4]
        paginate(data, 2, 3)
        self.assertEqual(data, [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
