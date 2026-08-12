import unittest
import os
import shutil
import tempfile
from database.db_manager import DatabaseManager
from scrapers.search_engine import SneakerSearchEngine

class TestSneakerSearch(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_sneakers.db")
        self.db = DatabaseManager(db_path=self.db_path)
        self.engine = SneakerSearchEngine()

        self.sample_sneaker = {
            "id": "adidas-samba-og-white",
            "name": "Adidas Samba OG",
            "colorway": "Cloud White",
            "size": "BR 40",
            "target_price": 650.0,
            "image_url": "https://example.com/samba.jpg",
            "sources": [
                {
                    "name": "Adidas",
                    "url": "https://adidas.com",
                    "type": "manual"
                }
            ]
        }

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def test_search_engine_filtering(self):
        results = self.engine.search("Vomero")
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]["id"], "nike-vomero-5-cobblestone")

    def test_search_engine_multi_token(self):
        results = self.engine.search("Samba White")
        self.assertTrue(len(results) >= 1)
        self.assertIn("Samba", results[0]["name"])

    def test_pin_and_unpin_sneaker(self):
        self.db.pin_sneaker(self.sample_sneaker)
        pinned = self.db.get_all_sneakers(pinned_only=True)
        self.assertEqual(len(pinned), 1)
        self.assertEqual(pinned[0]["id"], "adidas-samba-og-white")

        self.db.unpin_sneaker("adidas-samba-og-white")
        pinned_after = self.db.get_all_sneakers(pinned_only=True)
        self.assertEqual(len(pinned_after), 0)

    def test_search_cache_persistence(self):
        query = "jordan chicago"
        results = self.engine.search(query)
        self.db.save_search_cache(query, results)

        cached = self.db.get_search_cache(query)
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), len(results))

if __name__ == "__main__":
    unittest.main()
