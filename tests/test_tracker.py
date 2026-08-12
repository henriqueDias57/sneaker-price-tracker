import unittest
import os
import shutil
import tempfile
from database.db_manager import DatabaseManager
from scrapers.mock_collector import MockCollector
from analytics.price_analyzer import PriceAnalyzer

class TestSneakerPriceTracker(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_sneakers.db")
        self.db = DatabaseManager(db_path=self.db_path)

        self.sample_sneaker = {
            "id": "test-vomero-5",
            "name": "Nike Zoom Vomero 5",
            "colorway": "Black",
            "size": "BR 40",
            "target_price": 900.0,
            "sources": [
                {
                    "name": "TestStore",
                    "url": "https://example.com",
                    "type": "manual"
                }
            ]
        }
        self.db.save_sneaker(self.sample_sneaker)

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def test_save_and_retrieve_sneaker(self):
        sneakers = self.db.get_all_sneakers()
        self.assertEqual(len(sneakers), 1)
        self.assertEqual(sneakers[0]["id"], "test-vomero-5")
        self.assertEqual(sneakers[0]["size"], "BR 40")

    def test_price_history_recording(self):
        self.db.save_price_record("test-vomero-5", "TestStore", 850.0)
        df = self.db.get_price_history_dataframe("test-vomero-5")
        self.assertFalse(df.empty)
        self.assertEqual(df["price"].iloc[0], 850.0)

    def test_analyzer_target_hit(self):
        self.db.save_price_record("test-vomero-5", "TestStore", 850.0)
        analyzer = PriceAnalyzer(self.db)
        summaries = analyzer.analyze_all_sneakers()
        self.assertEqual(len(summaries), 1)
        self.assertTrue(summaries[0]["target_hit"])
        self.assertEqual(summaries[0]["current_best_price"], 850.0)

    def test_mock_collector(self):
        collector = MockCollector()
        records = collector.generate_historical_dataset([self.sample_sneaker], days=5)
        self.assertTrue(len(records) > 0)

if __name__ == "__main__":
    unittest.main()
