import asyncio
import unittest

from storage.json_store import JsonStore


class StoreTests(unittest.TestCase):
    def test_cache_roundtrip(self):
        store = JsonStore(ttl_hours=24)
        payload = {"analysis_id": "abc", "url": "https://example.com/"}

        asyncio.run(store.set_cached("example.com", payload))
        cached = asyncio.run(store.get_cached("https://example.com/"))

        self.assertIsNotNone(cached)
        self.assertEqual(cached["analysis_id"], "abc")

    def test_analysis_roundtrip(self):
        store = JsonStore(ttl_hours=24)
        payload = {"analysis_id": "x1", "url": "https://example.com/"}
        asyncio.run(store.save_analysis("x1", payload))
        loaded = asyncio.run(store.get_analysis("x1"))
        self.assertEqual(loaded["analysis_id"], "x1")


if __name__ == "__main__":
    unittest.main()
